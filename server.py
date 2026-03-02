"""
HTTPS Server for CSV Feed Testing
A FastAPI-based HTTPS server that serves CSV files for testing feed import/export functionality.
"""

import csv
import json
import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "archive"))
CERTS_DIR = Path(os.getenv("CERTS_DIR", "certs"))
SERVER_PORT = int(os.getenv("SERVER_PORT", "8443"))
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SSL_CERT_PATH = CERTS_DIR / os.getenv("SSL_CERT_FILE", "server.crt")
SSL_KEY_PATH = CERTS_DIR / os.getenv("SSL_KEY_FILE", "server.key")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CERTS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting HTTPS CSV Server...")
    logger.info(f"Data directory: {DATA_DIR.absolute()}")
    logger.info(f"Archive directory: {ARCHIVE_DIR.absolute()}")
    
    # Check if running on Render
    render_port = os.getenv("PORT")
    if render_port:
        logger.info(f"Running on Render - HTTPS handled by platform")
        logger.info(f"Server will run on http://0.0.0.0:{render_port}")
    else:
        logger.info(f"Certificates directory: {CERTS_DIR.absolute()}")
        logger.info(f"Server will run on https://{SERVER_HOST}:{SERVER_PORT}")
        
        # Check if SSL certificates exist (only for non-Render deployments)
        if not SSL_CERT_PATH.exists() or not SSL_KEY_PATH.exists():
            logger.warning(
                f"SSL certificates not found at {SSL_CERT_PATH} and {SSL_KEY_PATH}. "
                "Please generate certificates using generate_certs.py"
            )
    
    yield
    
    logger.info("Shutting down HTTPS CSV Server...")


# Create FastAPI app
app = FastAPI(
    title="HTTPS CSV Feed Server",
    description="A simple HTTPS server for serving CSV files for feed import/export testing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests."""
    logger.info(f"{request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint that lists available CSV files."""
    try:
        csv_files = list(DATA_DIR.glob("*.csv"))
        
        if not csv_files:
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>HTTPS CSV Feed Server</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    h1 { color: #333; }
                    .info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }
                    .warning { background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>HTTPS CSV Feed Server</h1>
                    <div class="info">
                        <p><strong>Status:</strong> Server is running</p>
                        <p><strong>No CSV files found</strong> in the data directory.</p>
                        <p>Please add CSV files to the <code>data/</code> directory.</p>
                    </div>
                    <div class="warning">
                        <p><strong>Available Endpoints:</strong></p>
                        <ul>
                            <li><code>GET /</code> - This page</li>
                            <li><code>GET /archive</code> - List archive files (served as <strong>JSON by default</strong>)</li>
                            <li><code>GET /health</code> - Health check</li>
                            <li><code>GET /{filename}.csv</code> - Download CSV file (data)</li>
                            <li><code>GET /{filename}.csv/json</code> - CSV as JSON array (data)</li>
                            <li><code>POST /upload</code> - Upload CSV (multipart)</li>
                            <li><code>POST /export</code> - Push CSV (body + filename)</li>
                        </ul>
                    </div>
                    <p><a href="/archive">Archive (JSON by default)</a></p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        file_list = "\n".join([
            f'<li><a href="/{file.name}">{file.name}</a> ({file.stat().st_size} bytes)</li>'
            for file in csv_files
        ])
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HTTPS CSV Feed Server</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; }}
                .info {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ padding: 10px; margin: 5px 0; background: #f9f9f9; border-radius: 4px; }}
                a {{ color: #1976d2; text-decoration: none; font-weight: bold; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>HTTPS CSV Feed Server</h1>
                <div class="info">
                    <p><strong>Status:</strong> Server is running</p>
                    <p><strong>Available CSV Files:</strong></p>
                    <ul>
                        {file_list}
                    </ul>
                </div>
                <div class="info">
                    <p><strong>Example Usage:</strong></p>
                    <pre>curl -k https://localhost:{SERVER_PORT}/testa_product.csv</pre>
                </div>
                <p><a href="/archive">Archive (JSON by default)</a></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    archive_count = len(list(ARCHIVE_DIR.glob("*.csv"))) if ARCHIVE_DIR.exists() else 0
    return {
        "status": "healthy",
        "data_directory": str(DATA_DIR.absolute()),
        "archive_directory": str(ARCHIVE_DIR.absolute()),
        "certs_directory": str(CERTS_DIR.absolute()),
        "ssl_cert_exists": SSL_CERT_PATH.exists(),
        "ssl_key_exists": SSL_KEY_PATH.exists(),
        "csv_files_count": len(list(DATA_DIR.glob("*.csv"))),
        "archive_csv_files_count": archive_count,
    }


def _validate_csv_filename(name: str) -> str:
    """Ensure filename is safe and ends with .csv."""
    name = name.strip()
    if ".." in name or "/" in name or "\\" in name or not name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not name.lower().endswith(".csv"):
        name = f"{name}.csv"
    return name


def _read_csv_as_json(file_path: Path) -> list:
    """Read a CSV file and return rows as list of dicts."""
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@app.post("/upload")
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    filename: Optional[str] = Form(None, description="Override filename (optional)"),
):
    """
    Upload (push) a CSV file to the server.
    Use multipart/form-data with a file field; optionally set 'filename' to choose the stored name.
    """
    try:
        name = filename or file.filename or "uploaded.csv"
        name = _validate_csv_filename(name)
        file_path = DATA_DIR / name

        content = await file.read()
        file_path.write_bytes(content)
        size = len(content)

        logger.info(f"Uploaded CSV: {name} ({size} bytes)")
        return {
            "status": "ok",
            "message": "CSV uploaded successfully",
            "filename": name,
            "size_bytes": size,
            "url": f"/{name}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@app.post("/export")
async def export_csv(request: Request):
    """
    Push CSV content in the request body (Content-Type: text/csv).
    Optional: ?filename=myfeed.csv or header X-Filename: myfeed.csv
    """
    content_type = request.headers.get("content-type", "")
    if "text/csv" not in content_type and "application/octet-stream" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be text/csv or application/octet-stream",
        )

    filename = request.query_params.get("filename") or request.headers.get("x-filename")
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Provide filename via ?filename=myfile.csv or X-Filename header",
        )

    try:
        name = _validate_csv_filename(filename)
        body = await request.body()
        file_path = DATA_DIR / name
        file_path.write_bytes(body)
        size = len(body)

        logger.info(f"Exported CSV: {name} ({size} bytes)")
        return {
            "status": "ok",
            "message": "CSV exported successfully",
            "filename": name,
            "size_bytes": size,
            "url": f"/{name}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")


# ---------- Archive: served as JSON by default ----------
@app.get("/archive", response_class=HTMLResponse)
async def list_archive():
    """List CSV files in the archive directory. Archive files are served as JSON by default."""
    if not ARCHIVE_DIR.exists():
        return HTMLResponse(
            content="<!DOCTYPE html><html><body><div class='container'><h1>Archive</h1><p>Archive directory not found.</p></div></body></html>"
        )
    csv_files = list(ARCHIVE_DIR.glob("*.csv"))
    if not csv_files:
        file_list = "<li>No CSV files in archive.</li>"
    else:
        file_list = "\n".join([
            f'<li><a href="/archive/{f.name}">{f.name}</a> (JSON, {f.stat().st_size} bytes) '
            f'| <a href="/archive/{f.name}?format=csv">CSV</a></li>'
            for f in sorted(csv_files)
        ])
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Archive - CSV Feed Server</title></head>
    <body style="font-family: Arial; margin: 40px;">
        <div class="container">
            <h1>Archive</h1>
            <p>Archive files are served as <strong>JSON by default</strong>. Use <code>?format=csv</code> for raw CSV.</p>
            <ul>{file_list}</ul>
            <p><a href="/">Back to Data</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/archive/{filename}")
async def get_archive_file(
    filename: str,
    format: Optional[str] = Query(None, description="Use 'csv' for raw CSV; default is JSON"),
):
    """
    Serve archive CSV as JSON by default. Add ?format=csv for raw CSV.
    Example: GET /archive/olist_products_dataset.csv  -> JSON array (for ADF REST).
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.lower().endswith(".csv"):
        filename = f"{filename}.csv"
    file_path = ARCHIVE_DIR / filename
    if not ARCHIVE_DIR.exists() or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Archive file '{filename}' not found")
    if format and format.lower() == "csv":
        logger.info(f"Serving archive as CSV: {filename} ({file_path.stat().st_size} bytes)")
        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    rows = _read_csv_as_json(file_path)
    logger.info(f"Serving archive as JSON: {filename} ({len(rows)} rows)")
    return rows


@app.get("/{filename}/json")
async def get_csv_as_json(filename: str):
    """
    Serve CSV file as a single JSON array. Valid for Azure Data Factory REST:
    Format = JSON, Collection reference = (leave empty).
    Example: GET /product.csv/json
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV filenames are supported (e.g. product.csv)")

    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    rows = _read_csv_as_json(file_path)
    logger.info(f"Serving CSV as JSON array: {filename} ({len(rows)} rows)")
    return rows


@app.get("/{filename}")
async def get_csv_file(filename: str):
    """
    Serve CSV files from the data directory.

    Args:
        filename: Name of the CSV file to serve

    Returns:
        FileResponse with the CSV file content
    """
    # Security: Prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(f"Attempted directory traversal: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = DATA_DIR / filename
    
    # Check if file exists
    if not file_path.exists():
        logger.warning(f"File not found: {filename}")
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    
    # Only serve CSV files
    if not filename.lower().endswith('.csv'):
        logger.warning(f"Attempted to access non-CSV file: {filename}")
        raise HTTPException(status_code=400, detail="Only CSV files are available")
    
    logger.info(f"Serving file: {filename} ({file_path.stat().st_size} bytes)")
    
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*"
        }
    )


def main():
    """Main function to run the server."""
    # Check if running on Render (Render provides HTTPS automatically)
    render_port = os.getenv("PORT")
    if render_port:
        logger.info(f"Running on Render - HTTPS handled by platform")
        logger.info(f"Starting server on http://0.0.0.0:{render_port}")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(render_port),
            log_level="info"
        )
        return
    
    # Local/other deployment with SSL certificates
    if not SSL_CERT_PATH.exists() or not SSL_KEY_PATH.exists():
        logger.error(
            f"\n{'='*60}\n"
            "ERROR: SSL certificates not found!\n"
            f"Certificate: {SSL_CERT_PATH}\n"
            f"Key: {SSL_KEY_PATH}\n\n"
            "Please generate certificates using:\n"
            "  python generate_certs.py\n\n"
            f"{'='*60}\n"
        )
        return
    
    logger.info(f"Starting server on https://{SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        ssl_keyfile=str(SSL_KEY_PATH),
        ssl_certfile=str(SSL_CERT_PATH),
        log_level="info"
    )


if __name__ == "__main__":
    main()
