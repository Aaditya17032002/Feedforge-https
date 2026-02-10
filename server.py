"""
HTTPS Server for CSV Feed Testing
A FastAPI-based HTTPS server that serves CSV files for testing feed import/export functionality.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
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
                            <li><code>GET /health</code> - Health check</li>
                            <li><code>GET /{filename}.csv</code> - Download CSV file</li>
                        </ul>
                    </div>
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
    return {
        "status": "healthy",
        "data_directory": str(DATA_DIR.absolute()),
        "certs_directory": str(CERTS_DIR.absolute()),
        "ssl_cert_exists": SSL_CERT_PATH.exists(),
        "ssl_key_exists": SSL_KEY_PATH.exists(),
        "csv_files_count": len(list(DATA_DIR.glob("*.csv")))
    }


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
