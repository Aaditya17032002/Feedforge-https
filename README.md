# HTTPS CSV Feed Server

A simple, production-ready HTTPS server built with FastAPI for serving CSV files. Perfect for testing feed import/export functionality in feed management systems.

## Features

- ✅ HTTPS server with self-signed SSL certificates
- ✅ Serves CSV files from a configurable data directory
- ✅ CORS enabled for cross-origin requests
- ✅ Health check endpoint
- ✅ Request logging for debugging
- ✅ Clean, well-documented code
- ✅ Configurable via environment variables
- ✅ Error handling and security measures

## Project Structure

```
project/
├── server.py              # FastAPI HTTPS server
├── generate_certs.py      # SSL certificate generation script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── data/                 # Directory for CSV files
│   └── product.csv       # Sample product feed CSV
└── certs/                # Directory for SSL certificates
    ├── server.crt        # SSL certificate (generated)
    └── server.key        # SSL private key (generated)
```

## Prerequisites

- Python 3.8 or higher
- OpenSSL (for certificate generation)
  - **Windows**: Download from [Win32OpenSSL](https://slproweb.com/products/Win32OpenSSL.html)
  - **macOS**: `brew install openssl`
  - **Linux**: `sudo apt-get install openssl` (Ubuntu/Debian) or `sudo yum install openssl` (CentOS/RHEL)

## Installation

1. **Clone or download this project**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate SSL certificates:**
   ```bash
   python generate_certs.py
   ```
   
   This will create self-signed certificates in the `certs/` directory:
   - `server.crt` - SSL certificate
   - `server.key` - Private key

## Configuration

The server can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `data` | Directory containing CSV files |
| `CERTS_DIR` | `certs` | Directory containing SSL certificates |
| `SERVER_PORT` | `8443` | Port to run the server on |
| `SERVER_HOST` | `0.0.0.0` | Host to bind the server to |
| `SSL_CERT_FILE` | `server.crt` | SSL certificate filename |
| `SSL_KEY_FILE` | `server.key` | SSL private key filename |
| `CORS_ORIGINS` | `*` | Comma-separated list of allowed CORS origins |
| `SSL_COMMON_NAME` | `localhost` | Common Name for SSL certificate |
| `SSL_VALIDITY_DAYS` | `365` | Certificate validity period in days |

### Example Configuration

**Windows (PowerShell):**
```powershell
$env:SERVER_PORT="8443"
$env:DATA_DIR="data"
python server.py
```

**Linux/macOS:**
```bash
export SERVER_PORT=8443
export DATA_DIR=data
python server.py
```

## Running the Server

### Basic Usage

```bash
python server.py
```

The server will start on `https://localhost:8443` (or your configured port).

### Using uvicorn directly

```bash
uvicorn server:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/server.key --ssl-certfile certs/server.crt
```

## API Endpoints

### `GET /`
Returns an HTML page listing all available CSV files in the data directory.

**Example:**
```bash
curl -k https://localhost:8443/
```

### `GET /health`
Health check endpoint that returns server status and configuration.

**Example:**
```bash
curl -k https://localhost:8443/health
```

**Response:**
```json
{
  "status": "healthy",
  "data_directory": "/path/to/data",
  "certs_directory": "/path/to/certs",
  "ssl_cert_exists": true,
  "ssl_key_exists": true,
  "csv_files_count": 1
}
```

### `GET /{filename}`
Serves CSV files from the data directory.

**Example:**
```bash
curl -k https://localhost:8443/product.csv
```

**Response Headers:**
- `Content-Type: text/csv`
- `Content-Disposition: attachment; filename="product.csv"`
- `Access-Control-Allow-Origin: *`

## Testing

### Using curl

```bash
# Test health endpoint
curl -k https://localhost:8443/health

# Download CSV file
curl -k https://localhost:8443/product.csv -o product.csv

# View CSV content
curl -k https://localhost:8443/product.csv
```

### Using Python requests

```python
import requests

# Disable SSL verification for self-signed certificates
response = requests.get('https://localhost:8443/product.csv', verify=False)
print(response.text)
```

### Using Browser

1. Navigate to `https://localhost:8443/`
2. Accept the SSL security warning (this is normal for self-signed certificates)
3. Click on any CSV file link to download it

## CSV File Format

The sample `product.csv` file includes the following columns:

- `id` - Product identifier
- `title` - Product title
- `description` - Product description
- `price` - Product price
- `availability` - Stock status (in stock, out of stock, etc.)
- `link` - Product URL
- `image_link` - Product image URL
- `brand` - Product brand
- `condition` - Product condition (new, used, refurbished)
- `gtin` - Global Trade Item Number
- `mpn` - Manufacturer Part Number

## Adding/Modifying CSV Files

1. Place your CSV files in the `data/` directory
2. Access them via `https://localhost:8443/{filename}.csv`
3. The server automatically detects new files

**Example:**
```bash
# Copy a CSV file to the data directory
cp my_products.csv data/

# Access it via
curl -k https://localhost:8443/my_products.csv
```

## SSL Certificate Details

### Self-Signed Certificates

The generated certificates are self-signed, which means:
- ✅ Perfect for local testing and development
- ✅ Works with `curl -k` flag
- ⚠️ Browsers will show a security warning (you can accept it)
- ⚠️ Not suitable for production use

### Certificate Information

- **Validity**: 365 days (configurable)
- **Common Name**: localhost (configurable)
- **Key Size**: 2048 bits
- **Subject Alternative Names**: Includes localhost, *.localhost, 127.0.0.1, ::1

### Regenerating Certificates

To regenerate certificates:

```bash
python generate_certs.py
```

You'll be prompted to confirm if certificates already exist.

## Security Considerations

1. **Directory Traversal Protection**: The server prevents accessing files outside the data directory
2. **File Type Validation**: Only CSV files are served
3. **CORS**: Configurable CORS origins (default: all origins)
4. **Self-Signed Certificates**: Suitable for testing only, not production

## Troubleshooting

### Certificate Errors

**Error**: `SSL certificates not found`

**Solution**: Run `python generate_certs.py` to generate certificates.

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Change the port using `SERVER_PORT` environment variable or stop the process using the port.

### OpenSSL Not Found

**Error**: `OpenSSL is not installed`

**Solution**: Install OpenSSL (see Prerequisites section).

### Browser SSL Warning

**Issue**: Browser shows "Your connection is not private"

**Solution**: This is expected for self-signed certificates. Click "Advanced" → "Proceed to localhost" (or similar).

## Example Usage in Feed Management System

```python
import requests
import csv
import io

# Download CSV feed via HTTPS
response = requests.get(
    'https://localhost:8443/product.csv',
    verify=False  # Disable SSL verification for self-signed cert
)

# Parse CSV
csv_content = response.text
reader = csv.DictReader(io.StringIO(csv_content))

for row in reader:
    print(f"Product: {row['title']} - ${row['price']}")
```

## License

This project is provided as-is for testing purposes.

## Support

For issues or questions, please check:
1. Certificate generation completed successfully
2. Port is not already in use
3. CSV files are in the `data/` directory
4. Python dependencies are installed

## Future Enhancements

Potential features for future versions:
- Authentication token support
- Multiple file format support (JSON, XML)
- Rate limiting
- File upload endpoint
- Admin dashboard
- Certificate auto-renewal
