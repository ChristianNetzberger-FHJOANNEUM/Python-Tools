"""
Dedicated Slideshow Server for Testing
Serves the Pasang-Wedding slideshow from the Git deployment directory
"""

import http.server
import socketserver
import socket
import os
import logging
from pathlib import Path

# Fixed slideshow directory
SLIDESHOW_DIR = Path(r"C:\_Git\Slideshows\Pasang-Wedding")
PORT = 8080

# Suppress HTTP request logging
class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Only log errors (status code >= 400)
        if args[1][0] in ('4', '5'):
            super().log_message(format, *args)
        # Suppress all successful requests (200, 304, etc.)


def get_local_ip():
    """Get local IP address for smartphone access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def generate_qr_code(url):
    """Generate QR code for easy smartphone access (optional)"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        
        # Print QR code to terminal
        qr.print_ascii(invert=True)
        return True
    except ImportError:
        return False


def main():
    # Check if directory exists
    if not SLIDESHOW_DIR.exists():
        print(f"❌ Error: Slideshow directory not found!")
        print(f"   Expected: {SLIDESHOW_DIR}")
        print(f"\n💡 Make sure you've exported the gallery to this directory.")
        return
    
    # Check if index.html exists
    index_file = SLIDESHOW_DIR / "index.html"
    if not index_file.exists():
        print(f"❌ Error: index.html not found in {SLIDESHOW_DIR}")
        print(f"\n💡 Export the gallery first using the Export dialog.")
        return
    
    # Change to slideshow directory
    os.chdir(SLIDESHOW_DIR)
    
    # Get local IP
    local_ip = get_local_ip()
    smartphone_url = f"http://{local_ip}:{PORT}/index.html"
    
    # Start server with quiet handler
    Handler = QuietHTTPRequestHandler
    
    print("\n" + "="*60)
    print("🎬 SLIDESHOW SERVER STARTED")
    print("="*60)
    print(f"\n📂 Serving: {SLIDESHOW_DIR}")
    print(f"🌐 Port: {PORT}")
    print(f"📡 WiFi IP: {local_ip}")
    print(f"\n💻 Local Access:")
    print(f"   → http://localhost:{PORT}/index.html")
    print(f"\n📱 Smartphone Access (same WiFi):")
    print(f"   → {smartphone_url}")
    
    # Try to generate QR code
    print(f"\n📷 QR Code for easy mobile access:")
    if generate_qr_code(smartphone_url):
        print(f"   ↑ Scan with your smartphone camera!")
    else:
        print(f"   (Install 'qrcode' for QR code: pip install qrcode[pil])")
    
    print(f"\n⚠️  Make sure Windows Firewall allows port {PORT}")
    print(f"   Run as Admin:")
    print(f"   New-NetFirewallRule -DisplayName \"Slideshow Server\" \\")
    print(f"       -Direction Inbound -Protocol TCP -LocalPort {PORT} -Action Allow")
    print(f"\n🛑 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped. Goodbye!")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"\n❌ Error: Port {PORT} is already in use!")
            print(f"💡 Try closing other servers or use a different port.")
        else:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
