import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Download,
  Database,
  FileCheck
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploadProps {
  onUploadComplete?: (result: any) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
}

export function FileUpload({ 
  onUploadComplete,
  acceptedFileTypes = ['.pdf'],
  maxFileSize = 25 * 1024 * 1024 // 25MB
}: FileUploadProps) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{
    success: boolean;
    message: string;
    data?: any;
  } | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadResult(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate realistic upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 85) {
            clearInterval(progressInterval);
            return 85;
          }
          return prev + Math.random() * 15;
        });
      }, 150);

      // Call FastAPI ingestion endpoint
      const base = import.meta.env.VITE_FASTAPI_BASE ?? 'http://localhost:8001';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);
      const url = `${base}/api/v1/ingestion/convert_and_ingest_async`;
      const res = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeout);
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Ingestion failed');
      }
      const data = await res.json();
      const result = {
        success: true,
        message: data.message,
        data: {
          recordsProcessed: data.records_processed ?? data.recordsProcessed ?? 0,
          validRecords: data.new_records_created ?? data.newRecordsCreated ?? 0,
          invalidRecords: 0,
          filename: file.name,
          uploadDate: new Date().toISOString(),
          processingTime: "",
          dataQuality: ""
        }
      };
      setUploadResult(result);
      onUploadComplete?.(result);

    } catch (error) {
      setUploadResult({
        success: false,
        message: error instanceof Error ? error.message : 'Processing failed - please verify data format'
      });
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxSize: maxFileSize,
    multiple: false
  });

  const reset = () => {
    setUploadProgress(0);
    setUploading(false);
    setUploadResult(null);
  };

  return (
    <Card className="shadow-professional">
      <CardHeader>
        <CardTitle className="text-heading flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          Data Integration Portal
        </CardTitle>
        <p className="text-caption">Import environmental monitoring datasets for analysis</p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Upload Interface */}
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200",
            isDragActive 
              ? "border-primary bg-primary/5 scale-[1.02]" 
              : "border-border/50 hover:border-primary/50 hover:bg-muted/20"
          )}
        >
          <input {...getInputProps()} />
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Upload className="h-8 w-8 text-primary" />
            </div>
            
            {isDragActive ? (
              <div>
                <p className="text-heading text-primary">
                  Release to upload dataset
                </p>
                <p className="text-caption">
                  Processing will begin automatically
                </p>
              </div>
            ) : (
              <div>
                <p className="text-subheading text-foreground">
                  Import Environmental Data
                </p>
                <p className="text-body text-muted-foreground">
                  Drag and drop your dataset file, or click to browse
                </p>
              </div>
            )}
            
            <div className="text-caption text-muted-foreground space-y-1">
              <p>Supported formats: {acceptedFileTypes.join(', ')}</p>
              <p>Maximum file size: {(maxFileSize / (1024 * 1024)).toFixed(0)}MB</p>
              <p>Expected columns: site_id, latitude, longitude, sample_date, metal concentrations</p>
            </div>
          </div>
        </div>

        {/* Validation Errors */}
        {fileRejections.length > 0 && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Upload rejected:</strong> {fileRejections[0].errors[0].message}
            </AlertDescription>
          </Alert>
        )}

        {/* Processing Progress */}
        {uploading && (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-body font-medium">Processing dataset...</span>
              <span className="text-caption font-mono">{uploadProgress.toFixed(0)}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
            <div className="text-caption text-muted-foreground text-center">
              {uploadProgress < 30 && "Validating file format..."}
              {uploadProgress >= 30 && uploadProgress < 60 && "Parsing data structure..."}
              {uploadProgress >= 60 && uploadProgress < 85 && "Quality assessment in progress..."}
              {uploadProgress >= 85 && "Finalizing import..."}
            </div>
          </div>
        )}

        {/* Results Display */}
        {uploadResult && (
          <Alert variant={uploadResult.success ? "default" : "destructive"}>
            <div className="flex items-start gap-3">
              {uploadResult.success ? (
                <CheckCircle className="h-5 w-5 text-excellent mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 mt-0.5" />
              )}
              <div className="flex-1">
                <AlertDescription className="text-body">
                  {uploadResult.message}
                </AlertDescription>
                
                {uploadResult.success && uploadResult.data && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-lg border border-border/30">
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div>
                        <div className="text-caption text-muted-foreground">Records Processed</div>
                        <div className="stat-value text-lg">{uploadResult.data.recordsProcessed.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-caption text-muted-foreground">Data Quality</div>
                        <div className="stat-value text-lg text-excellent">{uploadResult.data.dataQuality}</div>
                      </div>
                      <div>
                        <div className="text-caption text-muted-foreground">Valid Records</div>
                        <div className="text-body font-medium">{uploadResult.data.validRecords.toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-caption text-muted-foreground">Processing Time</div>
                        <div className="text-body font-medium font-mono">{uploadResult.data.processingTime}</div>
                      </div>
                    </div>
                    
                    {uploadResult.data.invalidRecords > 0 && (
                      <div className="p-3 bg-poor/10 border border-poor/20 rounded-md">
                        <div className="text-caption text-poor font-medium">
                          {uploadResult.data.invalidRecords} records require attention
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            {uploadResult.success && (
              <div className="flex gap-3 mt-4">
                <Button size="sm" onClick={reset} variant="outline">
                  Import Additional Data
                </Button>
                <Button size="sm" variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Processing Report
                </Button>
              </div>
            )}
          </Alert>
        )}

        {/* Template and Documentation */}
        <div className="pt-4 border-t border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileCheck className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-body font-medium">Need formatting guidance?</p>
                <p className="text-caption text-muted-foreground">
                  Download our data template and integration guidelines
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="text-sm">
                <FileText className="h-4 w-4 mr-2" />
                Template
              </Button>
              <Button variant="outline" size="sm" className="text-sm">
                Documentation
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}