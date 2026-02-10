"""
SSL Certificate Generation Script
Generates self-signed SSL certificates for HTTPS server testing.
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta

CERTS_DIR = Path(os.getenv("CERTS_DIR", "certs"))
CERT_FILE = CERTS_DIR / "server.crt"
KEY_FILE = CERTS_DIR / "server.key"
COMMON_NAME = os.getenv("SSL_COMMON_NAME", "localhost")
VALIDITY_DAYS = int(os.getenv("SSL_VALIDITY_DAYS", "365"))


def check_openssl():
    """Check if OpenSSL is available."""
    try:
        result = subprocess.run(
            ["openssl", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"OpenSSL found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: OpenSSL is not installed or not in PATH")
        print("\nPlease install OpenSSL:")
        print("  Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("  macOS: brew install openssl")
        print("  Linux: sudo apt-get install openssl (Ubuntu/Debian)")
        print("         sudo yum install openssl (CentOS/RHEL)")
        return False


def generate_certificates():
    """Generate self-signed SSL certificates."""
    # Ensure certs directory exists
    CERTS_DIR.mkdir(exist_ok=True)
    
    # Check if certificates already exist
    if CERT_FILE.exists() or KEY_FILE.exists():
        response = input(
            f"Certificates already exist at {CERTS_DIR}.\n"
            "Do you want to overwrite them? (y/N): "
        )
        if response.lower() != 'y':
            print("Certificate generation cancelled.")
            return False
    
    print(f"\nGenerating SSL certificates...")
    print(f"  Common Name: {COMMON_NAME}")
    print(f"  Validity: {VALIDITY_DAYS} days")
    print(f"  Certificate: {CERT_FILE}")
    print(f"  Private Key: {KEY_FILE}\n")
    
    # Generate private key
    print("Step 1: Generating private key...")
    try:
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", str(KEY_FILE),
                "2048"
            ],
            check=True,
            capture_output=True
        )
        print("  ✓ Private key generated")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error generating private key: {e}")
        return False
    
    # Generate certificate signing request and self-signed certificate
    print("Step 2: Generating self-signed certificate...")
    try:
        # Create a temporary config file for OpenSSL
        config_content = f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
OU = Organizational Unit
CN = {COMMON_NAME}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = {COMMON_NAME}
DNS.2 = *.{COMMON_NAME}
IP.1 = 127.0.0.1
IP.2 = ::1
"""
        config_file = CERTS_DIR / "openssl.conf"
        config_file.write_text(config_content)
        
        subprocess.run(
            [
                "openssl", "req",
                "-new",
                "-x509",
                "-key", str(KEY_FILE),
                "-out", str(CERT_FILE),
                "-days", str(VALIDITY_DAYS),
                "-config", str(config_file),
                "-extensions", "v3_req"
            ],
            check=True,
            capture_output=True
        )
        
        # Clean up config file
        config_file.unlink()
        
        print("  ✓ Certificate generated")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error generating certificate: {e}")
        if KEY_FILE.exists():
            KEY_FILE.unlink()
        return False
    
    # Set appropriate permissions (Unix-like systems)
    if sys.platform != "win32":
        os.chmod(KEY_FILE, 0o600)
        os.chmod(CERT_FILE, 0o644)
    
    print(f"\n{'='*60}")
    print("✓ SSL certificates generated successfully!")
    print(f"{'='*60}")
    print(f"\nCertificate: {CERT_FILE.absolute()}")
    print(f"Private Key: {KEY_FILE.absolute()}")
    print(f"\nCertificate is valid for {VALIDITY_DAYS} days")
    print(f"Common Name: {COMMON_NAME}")
    print(f"\nYou can now start the server with: python server.py")
    print(f"{'='*60}\n")
    
    return True


def main():
    """Main function."""
    print("="*60)
    print("SSL Certificate Generator for HTTPS CSV Server")
    print("="*60)
    
    if not check_openssl():
        sys.exit(1)
    
    if generate_certificates():
        print("\nNote: This is a self-signed certificate.")
        print("Browsers will show a security warning - this is normal for testing.")
        print("You can accept the warning or add the certificate to your trusted store.")
    else:
        print("\nFailed to generate certificates.")
        sys.exit(1)


if __name__ == "__main__":
    main()
