from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import tempfile
import pandas as pd
import os
import sys
import django
import logging
import math
import concurrent.futures
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import tabula
except Exception as e: # pragma: no cover
    tabula = None
    logging.error(f"Failed to import tabula-py: {e}")

# Ensure Django project is on sys.path so 'aquaguard_django' can be imported
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
DJANGO_SERVICE_DIR = os.path.join(PROJECT_ROOT, 'django-service')
logging.info(f"ingestion.py path setup -> CURRENT_DIR={CURRENT_DIR}")
logging.info(f"ingestion.py path setup -> PROJECT_ROOT={PROJECT_ROOT}")
logging.info(f"ingestion.py path setup -> DJANGO_SERVICE_DIR={DJANGO_SERVICE_DIR}")
if DJANGO_SERVICE_DIR not in sys.path:
    sys.path.insert(0, DJANGO_SERVICE_DIR)
    logging.info("ingestion.py path setup -> inserted DJANGO_SERVICE_DIR into sys.path")
else:
    logging.info("ingestion.py path setup -> DJANGO_SERVICE_DIR already in sys.path")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aquaguard_django.settings')
logging.info(f"ingestion.py -> DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE')}")
try:
    django.setup()
    from data_management.models import GroundWaterSample  # type: ignore
    logging.info("Django setup complete.")
except Exception as e:
    logging.critical(f"FATAL: Django setup failed! Check settings and paths. Error: {e}")
    # Re-raise the error so the server stops if Django fails to load
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

def _process_pdf_page(tmp_path: str, page: int) -> list:
    """Process a single page of a PDF file and return the extracted data frames."""
    if tabula is None:
        logging.error("tabula-py dependency is missing or failed to load.")
        raise HTTPException(status_code=500, detail="tabula-py not available on server")
    
    logging.info(f"Processing page {page} of PDF")
    data_frames = []
    
    try:
        # Use lattice=True first, as it's better for tables with visible lines
        data_frames = tabula.read_pdf(tmp_path, pages=str(page), multiple_tables=True, lattice=True, guess=False)
    except Exception as e:
        logging.warning(f"tabula lattice mode failed for page {page}: {e}. Retrying with stream mode.")
    
    if not data_frames:
        try:
            # Retry with stream mode 
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
    if tabula is None:
        logging.error("tabula-py dependency is missing or failed to load.")
        raise HTTPException(status_code=500, detail="tabula-py not available on server")

    tmp_path = None
    try:
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
            logging.info(f"Processing all {total_pages} pages of PDF")
        else:
            # Parse pages string (e.g., "1,3-5,7")
            pages_to_process = []
            for part in pages.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages_to_process.extend(range(start, end + 1))
                else:
                    pages_to_process.append(int(part))
            logging.info(f"Processing specific pages: {pages_to_process}")
        
        # Process pages in parallel
        data_frames = []
        failed_pages = []
        successful_pages = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(pages_to_process), 5)) as executor:
            future_to_page = {executor.submit(_process_pdf_page, tmp_path, page): page for page in pages_to_process}
            for future in concurrent.futures.as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    page_data_frames = future.result()
                    if page_data_frames:
                        data_frames.extend(page_data_frames)
                        successful_pages.append(page)
                        logging.info(f"Successfully processed page {page}, found {len(page_data_frames)} tables")
                    else:
                        logging.warning(f"No tables found on page {page}")
                        failed_pages.append(page)
                except Exception as e:
                    logging.error(f"Error processing page {page}: {e}")
                    failed_pages.append(page)
        
        # Log summary of parallel processing
        logging.info(f"Parallel processing summary: {len(successful_pages)} pages successful, {len(failed_pages)} pages failed")
        if failed_pages:
            logging.warning(f"Failed pages: {failed_pages}")
        
        if not data_frames:
            logging.error("No data frames extracted from any page")
            raise HTTPException(status_code=400, detail="No tables found in the PDF after extraction attempts.")
                
    except Exception as e:
        logging.critical(f"Error during PDF extraction or file handling: {e}")
        raise
        
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logging.info(f"Cleaned up temp file: {tmp_path}")
            except Exception as e:
                logging.error(f"Failed to clean up temp file {tmp_path}: {e}")
                
    if not data_frames:
        raise HTTPException(status_code=400, detail="No tables found in the PDF after extraction attempts.")

    # Combine all extracted tables
    df = pd.concat(data_frames, ignore_index=True)
    
    # --- FIX 1: MANUAL COLUMN MAPPING AND HEADER REMOVAL ---
    if len(df.columns) > 0:
        # We need exactly 24 columns for the data. If more were extracted, it's junk.
        if len(df.columns) >= len(CORE_DATA_COLUMNS):
            df = df.iloc[:, :len(CORE_DATA_COLUMNS)] # Slice to keep only the expected number of columns
            df.columns = CORE_DATA_COLUMNS
            
            # Drop the first row, which is the junk header row detected by tabula
            df = df.iloc[1:].reset_index(drop=True)
            
            logging.info(f"FIXED Extraction columns: {list(df.columns)}")
            
        else:
             logging.error(f"Extracted fewer columns ({len(df.columns)}) than expected data columns ({len(CORE_DATA_COLUMNS)}).")
             # We assume the first row is still junk data for the header
             df = df.iloc[1:].reset_index(drop=True)
             df.columns = CORE_DATA_COLUMNS[:len(df.columns)]
             
    # --------------------------------------------------------
    
    df.dropna(how='all', inplace=True)
    # The first column 'S.No' often includes non-numeric headers from subsequent rows, 
    # so we drop rows where 'S.No' is clearly not numeric data after cleaning.
    df = df[pd.to_numeric(df['S.No'], errors='coerce').notna()]
    
    df.replace(['-', 'ND', 'LOR', ''], pd.NA, inplace=True) 
    
    try:
        logging.info(f"Total data rows to process: {len(df)}")
        logging.info(f"First 2 rows preview (after fixing headers): {df.head(2).to_dict('records')}")
    except Exception:
        pass

    records = df.to_dict('records')
    samples = []
    processed = 0
    
    def get_numeric(rec: dict, keys: list[str]):
        """
        Robustly fetches numeric data from a record using fixed column names.
        Includes aggressive string cleaning for coordinates/values.
        """
        for k in keys:
            if k in rec and rec.get(k) is not None:
                val_raw = str(rec.get(k))
                val_str = val_raw.strip()
                
                # FIX: Aggressively clean the string: remove commas, non-standard spaces, etc.
                val_str = val_str.replace(',', '').replace(' ', '')
                
                if val_str:
                    # Coerce errors will result in NaN, which is checked later
                    val = pd.to_numeric(val_str, errors='coerce') 
                    if pd.notna(val):
                        # Convert numpy float/int to standard Python float
                        return float(val) 
        return None # Return None instead of pd.NA for easier Django compatibility

    for idx, rec in enumerate(records):
        processed += 1
        s_no_val_str = rec.get('S.No') # Get raw string for logging
        lon_val_str = rec.get('Longitude') # Get raw string for logging
        lat_val_str = rec.get('Latitude') # Get raw string for logging
        
        s_no_val = None 
        lon_val = None
        lat_val = None

        try:
            # --- MANDATORY FIELD VALIDATION (Using the fixed, non-aliased names) ---
            s_no_val = get_numeric(rec, ['S.No']) 
            lon_val = get_numeric(rec, ['Longitude'])
            lat_val = get_numeric(rec, ['Latitude'])

            # Reject row if any required field is invalid or missing (None is the result of failed conversion now)
            if s_no_val is None or lon_val is None or lat_val is None:
                # Log the RAW string values to help debug the failure reason
                logging.warning(
                    f"Skipping record {idx} due to missing required field. "
                    f"(S.No_raw: {s_no_val_str!r}, Lon_raw: {lon_val_str!r}, Lat_raw: {lat_val_str!r})"
                )
                continue
            
            s_no_int = int(s_no_val) # Cast to int after check
            
            year_val = get_numeric(rec, ['Year'])
            year_int = int(year_val) if year_val is not None else 0 # Year should be an IntegerField

            # --- MODEL INSTANTIATION ---
            # All fields mapping to Django DecimalField should receive float or None
            
            # FIX: Explicitly cast non-numeric inputs (State, District, Location) to str 
            # to safely call .strip(), even if Pandas accidentally converted them to float.
            sample = GroundWaterSample(
                s_no=s_no_int,
                state=str(rec.get('State') or "").strip(),
                district=str(rec.get('District') or "").strip(),
                location=str(rec.get('Location') or "").strip(), # FIX APPLIED HERE
                # Coordinates (DecimalField in Django model, passing Python floats or None)
                longitude=lon_val, 
                latitude=lat_val,
                year=year_int,
                
                # Heavy metals and core parameters (DecimalField, passing Python floats or None)
                ph=get_numeric(rec, ['pH']),
                ec_us_cm=get_numeric(rec, ['EC (µS/cm)']),
                co3_mg_l=get_numeric(rec, ['CO3 (mg/L)']),
                hco3_mg_l=get_numeric(rec, ['HCO3 (mg/L)']),
                cl_mg_l=get_numeric(rec, ['Cl (mg/L)']),
                f_mg_l=get_numeric(rec, ['F (mg/L)']),
                total_hardness_mg_l=get_numeric(rec, ['Total Hardness (mg/L)']),
                fe_ppm=get_numeric(rec, ['Fe (ppm)']),
                as_ppb=get_numeric(rec, ['As (ppb)']),
                u_ppb=get_numeric(rec, ['U (ppb)']),
                
                # --- NEW FIELDS FOR COMPLETE DATA INGESTION ---
                # NOTE: These names must match your Django model field names
                so4_mg_l=get_numeric(rec, ['SO4 (mg/L)']),
                no3_mg_l=get_numeric(rec, ['NO3 (mg/L)']),
                po4_mg_l=get_numeric(rec, ['PO4 (mg/L)']),
                ca_mg_l=get_numeric(rec, ['Ca (mg/L)']),
                mg_mg_l=get_numeric(rec, ['Mg (mg/L)']),
                na_mg_l=get_numeric(rec, ['Na (mg/L)']),
                k_mg_l=get_numeric(rec, ['K (mg/L)']),
                # -----------------------------------------------
            )
            samples.append(sample)
        except Exception as e:
            # Log specific record processing failures
            logging.warning(f"Failed to process record idx={idx} (S.No={s_no_val}, Lon={lon_val}): {e}", exc_info=True)
            continue

    # --- DEDUPLICATION AND INSERTION ---
    to_insert: list[GroundWaterSample] = []
    incoming_snos = set()
    
    # Filter for unique serial numbers within the current batch
    for s in samples:
        if s.s_no not in incoming_snos:
            incoming_snos.add(s.s_no)
            to_insert.append(s)

    # Check against database for existing records
    try:
        current_batch_snos = [s.s_no for s in to_insert]
        existing_snos = set(GroundWaterSample.objects.filter(s_no__in=current_batch_snos).values_list('s_no', flat=True))
        
        final_insert_list = [s for s in to_insert if s.s_no not in existing_snos]
        
        logging.info(f"Incoming unique S.Nos: {len(to_insert)}. Existing S.Nos found in DB: {len(existing_snos)}. Final list to insert: {len(final_insert_list)}")
        if existing_snos:
            logging.warning(f"Skipped S.Nos because they already exist: {list(existing_snos)[:5]}...")
            
    except Exception as e:
        logging.error(f"Failed DEDUPLICATION CHECK against DB: {e}. Attempting full insert with ignore_conflicts.")
        final_insert_list = to_insert

    created = GroundWaterSample.objects.bulk_create(final_insert_list, ignore_conflicts=True)
    
    # Report generation
    skipped_duplicates = len(to_insert) - len(final_insert_list)
    logging.info(f"Successfully created {len(created)} records. Processed total of {processed} records. Skipped duplicates: {skipped_duplicates}")
    
    return processed, len(created)


@router.post("/convert_and_ingest", response_model=IngestionResponse)
async def convert_and_ingest_pdf(file: UploadFile = File(...), pages: str = '1'):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is supported.")
    try:
        content = await file.read()
        # Offload blocking work to thread pool
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
        # Check if the error is related to tabula or Java
        if "java" in str(e).lower() or "not found" in str(e).lower():
             detail_msg = "Critical Error: Java Runtime Environment (JRE) is required for tabula-py and appears to be missing or misconfigured."
        else:
             detail_msg = f"Ingestion error: {e}"

        raise HTTPException(status_code=500, detail=detail_msg)


@router.post("/convert_and_ingest_async", status_code=202)
async def convert_and_ingest_pdf_async(background: BackgroundTasks, file: UploadFile = File(...), pages: str = 'all'):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is supported.")
    
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Create a synchronous function that will be run in a thread
        def process_pdf_in_thread(content, pages):
            try:
                # This runs in a thread, so it's safe to use synchronous Django operations
                processed, created = _process_pdf_bytes(content, pages)
                logging.info(f"Background task completed: Processed {processed} records, created {created} new entries in Django database.")
                return processed, created
            except Exception as e:
                logging.error(f"Background task failed: {str(e)}", exc_info=True)
                return 0, 0
        
        # Add the task to run in background
        background.add_task(process_pdf_in_thread, content, pages)
        
        # Provide more detailed response about parallel processing
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
