import tempfile
import pandas as pd
import os
import sys
import django
import logging
import math
import concurrent.futures
import PyPDF2

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import tabula
except Exception as e: # pragma: no cover
    tabula = None
    logging.error(f"Failed to import tabula-py: {e}")

# --- Django Setup (Ensure Paths are Correct) ---
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
DJANGO_SERVICE_DIR = os.path.join(PROJECT_ROOT, 'django-service')

if DJANGO_SERVICE_DIR not in sys.path:
    sys.path.insert(0, DJANGO_SERVICE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aquaguard_django.settings')

try:
    django.setup()
    from data_management.models import GroundWaterSample  # type: ignore
    logging.info("Django setup complete.")
except Exception as e:
    logging.critical(f"FATAL: Django setup failed! Error: {e}")
    raise

router = APIRouter()

class IngestionResponse(BaseModel):
    message: str
    records_processed: int
    new_records_created: int

# --- DEFINED COLUMN NAMES (24 core data columns needed for insertion) ---
CORE_DATA_COLUMNS = [
    'S.No', 'State', 'District', 'Location', 'Longitude', 'Latitude', 'Year', 
    'pH', 'EC (µS/cm)', 'CO3 (mg/L)', 'HCO3 (mg/L)', 'Cl (mg/L)', 'F (mg/L)', 
    'SO4 (mg/L)', 'NO3 (mg/L)', 'PO4 (mg/L)', 'Total Hardness (mg/L)', 
    'Ca (mg/L)', 'Mg (mg/L)', 'Na (mg/L)', 'K (mg/L)', 'Fe (ppm)', 'As (ppb)', 
    'U (ppb)'
]

def _safe_get_text(rec: dict, key: str) -> str:
    """Safely retrieves text fields, ensuring non-string inputs (like floats) are handled."""
    raw_value = rec.get(key)
    if raw_value is None:
        return ""
    # Explicitly cast to string before cleaning, preventing AttributeError if Pandas read it as a float.
    return str(raw_value).strip()


def _process_pdf_page(tmp_path: str, page: int) -> list:
    """Process a single page of a PDF file and return the extracted data frames."""
    if tabula is None:
        raise HTTPException(status_code=500, detail="tabula-py not available on server")
    
    logging.info(f"Processing page {page} of PDF")
    data_frames = []
    
    try:
        # Prioritize lattice mode for ruled tables
        data_frames = tabula.read_pdf(tmp_path, pages=str(page), multiple_tables=True, lattice=True, guess=False)
    except Exception:
        logging.warning(f"tabula lattice mode failed for page {page}. Retrying with stream mode.")
    
    if not data_frames:
        try:
            data_frames = tabula.read_pdf(tmp_path, pages=str(page), multiple_tables=True, stream=True, guess=False)
        except Exception as e:
            logging.error(f"tabula stream mode also failed for page {page}: {e}")
            data_frames = []
    
    return data_frames

def _get_pdf_page_count(tmp_path: str) -> int:
    """Get the total number of pages in a PDF file."""
    try:
        with open(tmp_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
    except Exception as e:
        logging.error(f"Error getting PDF page count: {e}")
        return 0

def _process_pdf_bytes(content: bytes, pages: str = 'all') -> tuple[int, int]:
    """Handles file writing, parallel page processing, and database insertion."""
    if tabula is None:
        raise HTTPException(status_code=500, detail="tabula-py not available on server")

    tmp_path = None
    try:
        # Write content to temp file for tabula to access
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            tmp.write(content)
            tmp.flush()
            tmp_path = tmp.name
        finally:
            tmp.close()

        # Determine which pages to process
        if pages.lower() == 'all':
            total_pages = _get_pdf_page_count(tmp_path)
            pages_to_process = list(range(1, total_pages + 1))
        else:
            # Simple parsing for single pages or comma-separated lists
            pages_to_process = [int(p.strip()) for p in pages.split(',') if p.strip().isdigit()]
        
        logging.info(f"Starting ingestion for pages: {pages_to_process}")
        
        # Process pages in parallel using a ThreadPoolExecutor
        all_data_frames = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(pages_to_process), 8)) as executor:
            future_to_page = {executor.submit(_process_pdf_page, tmp_path, page): page for page in pages_to_process}
            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    page_data_frames = future.result()
                    if page_data_frames:
                        all_data_frames.extend(page_data_frames)
                except Exception as e:
                    logging.error(f"Error processing page {future_to_page[future]}: {e}")
        
        if not all_data_frames:
            raise HTTPException(status_code=400, detail="No tables found in the PDF after extraction attempts.")

        # Combine all extracted tables
        df = pd.concat(all_data_frames, ignore_index=True)
        
        # --- Data Cleaning and Alignment ---
        
        # 1. Slice and Rename Columns (assuming 24 columns were extracted)
        if len(df.columns) >= len(CORE_DATA_COLUMNS):
            df = df.iloc[:, :len(CORE_DATA_COLUMNS)]
            df.columns = CORE_DATA_COLUMNS
            df = df.iloc[1:].reset_index(drop=True) # Drop the junk header row
        else:
            logging.error(f"Extracted fewer columns ({len(df.columns)}) than expected ({len(CORE_DATA_COLUMNS)}).")
            raise HTTPException(status_code=500, detail="Inconsistent column count detected during PDF extraction.")
            
        logging.info(f"FIXED Extraction columns: {list(df.columns)}")

        # 2. General cleaning and NaN replacement
        df.dropna(how='all', inplace=True)
        df.replace(['-', 'ND', 'LOR', ''], pd.NA, inplace=True) 
        
        # 3. Drop rows where S.No (mandatory field) is non-numeric/missing
        df = df[pd.to_numeric(df['S.No'], errors='coerce').notna()]
        
        logging.info(f"Total data rows to process: {len(df)}")


        records = df.to_dict('records')
        samples = []
        processed = 0
        
        def get_numeric(rec: dict, keys: list[str]):
            """Robustly fetches numeric data as Python float or None."""
            for k in keys:
                if k in rec and rec.get(k) is not None:
                    # Robust cleaning of spaces/commas before conversion
                    val_str = str(rec.get(k)).strip().replace(',', '').replace(' ', '')
                    if val_str:
                        val = pd.to_numeric(val_str, errors='coerce') 
                        if pd.notna(val):
                            return float(val) # Return Python float, not NumPy type
            return None # Return None for compatibility with Django DecimalField

        for idx, rec in enumerate(records):
            processed += 1
            s_no_val = None
            lon_val = None
            lat_val = None
            
            try:
                # --- MANDATORY FIELD VALIDATION ---
                s_no_val = get_numeric(rec, ['S.No']) 
                lon_val = get_numeric(rec, ['Longitude'])
                lat_val = get_numeric(rec, ['Latitude'])

                if s_no_val is None or lon_val is None or lat_val is None:
                    # Logging raw string data to see why conversion failed
                    s_no_raw = str(rec.get('S.No'))
                    lon_raw = str(rec.get('Longitude'))
                    lat_raw = str(rec.get('Latitude'))

                    logging.warning(
                        f"Skipping record {idx} due to missing required field. "
                        f"(S.No_raw: {s_no_raw!r}, Lon_raw: {lon_raw!r}, Lat_raw: {lat_raw!r})"
                    )
                    continue
                
                s_no_int = int(s_no_val)
                year_val = get_numeric(rec, ['Year'])
                year_int = int(year_val) if year_val is not None else 0

                # --- MODEL INSTANTIATION ---
                sample = GroundWaterSample(
                    s_no=s_no_int,
                    # Use _safe_get_text for string fields to prevent float crash
                    state=_safe_get_text(rec, 'State'),
                    district=_safe_get_text(rec, 'District'),
                    location=_safe_get_text(rec, 'Location'), 
                    longitude=lon_val, 
                    latitude=lat_val,
                    year=year_int,
                    
                    # Core and Heavy Metals
                    ph=get_numeric(rec, ['pH']),
                    ec_us_cm=get_numeric(rec, ['EC (µS/cm)']),
                    co3_mg_l=get_numeric(rec, ['CO3 (mg/L)']),
                    hco3_mg_l=get_numeric(rec, ['HCO3 (mg/L)']),
                    cl_mg_l=get_numeric(rec, ['Cl (mg/L)']),
                    f_mg_l=get_numeric(rec, ['F (mg/L)']),
                    total_hardness_mg_l=get_numeric(rec, ['Total Hardness (mg/L)']),
                    so4_mg_l=get_numeric(rec, ['SO4 (mg/L)']),
                    no3_mg_l=get_numeric(rec, ['NO3 (mg/L)']),
                    po4_mg_l=get_numeric(rec, ['PO4 (mg/L)']),
                    ca_mg_l=get_numeric(rec, ['Ca (mg/L)']),
                    mg_mg_l=get_numeric(rec, ['Mg (mg/L)']),
                    na_mg_l=get_numeric(rec, ['Na (mg/L)']),
                    k_mg_l=get_numeric(rec, ['K (mg/L)']),
                    fe_ppm=get_numeric(rec, ['Fe (ppm)']),
                    as_ppb=get_numeric(rec, ['As (ppb)']),
                    u_ppb=get_numeric(rec, ['U (ppb)']),
                )
                samples.append(sample)
            except Exception as e:
                logging.warning(f"Failed to process record idx={idx} (S.No={s_no_val}, Lon={lon_val}): {e}", exc_info=False)
                continue

        # --- DEDUPLICATION AND INSERTION ---
        to_insert = []
        incoming_snos = set()
        for s in samples: # Filter for unique S.No within the current batch
            if s.s_no not in incoming_snos:
                incoming_snos.add(s.s_no)
                to_insert.append(s)

        # Check against database for existing records
        current_batch_snos = [s.s_no for s in to_insert]
        existing_snos = set(GroundWaterSample.objects.filter(s_no__in=current_batch_snos).values_list('s_no', flat=True))
        
        final_insert_list = [s for s in to_insert if s.s_no not in existing_snos]
        
        logging.info(f"Incoming unique S.Nos: {len(to_insert)}. Existing S.Nos found in DB: {len(existing_snos)}. Final list to insert: {len(final_insert_list)}")
        if existing_snos:
            logging.warning(f"Skipped S.Nos because they already exist: {list(existing_snos)[:5]}...")
        
        created = GroundWaterSample.objects.bulk_create(final_insert_list, ignore_conflicts=True)
        
        skipped_duplicates = len(to_insert) - len(final_insert_list)
        logging.info(f"Successfully created {len(created)} records. Processed total of {processed} records. Skipped duplicates: {skipped_duplicates}")
        
        return processed, len(created)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@router.post("/convert_and_ingest", response_model=IngestionResponse)
async def convert_and_ingest_pdf(file: UploadFile = File(...), pages: str = '1'):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is supported.")
    try:
        content = await file.read()
        processed, created = await run_in_threadpool(_process_pdf_bytes, content, pages)
        return IngestionResponse(
            message="PDF data successfully converted and ingested.",
            records_processed=processed,
            new_records_created=created,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API endpoint caught ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion error: {e}")


@router.post("/convert_and_ingest_async", status_code=202)
async def convert_and_ingest_pdf_async(background: BackgroundTasks, file: UploadFile = File(...), pages: str = 'all'):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is supported.")
    
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        def process_pdf_in_thread(content, pages):
            try:
                processed, created = _process_pdf_bytes(content, pages)
                logging.info(f"Background task completed: Processed {processed} records, created {created} new entries in Django database.")
                return processed, created
            except Exception as e:
                logging.error(f"Background task failed: {str(e)}", exc_info=True)
                return 0, 0
        
        background.add_task(process_pdf_in_thread, content, pages)
        
        return {
            "status": "accepted", 
            "message": "PDF ingestion started in background with parallel page processing. Check logs for completion status.",
            "processing_mode": "parallel",
            "pages_setting": pages
        }
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error preparing PDF ingestion: {str(e)}"
        logging.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
