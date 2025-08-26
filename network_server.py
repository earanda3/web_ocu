#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import urllib.parse
import socket
from pathlib import Path

class NetworkHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the correct directory as the current working directory
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/api/pdfs':
            self.serve_pdf_list()
            return
        elif self.path.startswith('/download/'):
            self.serve_pdf_download()
            return
        
        super().do_GET()

    def serve_pdf_list(self):
        """Serve a JSON list of available PDF files"""
        try:
            pdf_files = []
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            
            for file_path in current_dir.glob('*.pdf'):
                file_stat = file_path.stat()
                pdf_files.append({
                    'name': file_path.name,
                    'size': file_stat.st_size
                })
            
            # Sort by name
            pdf_files.sort(key=lambda x: x['name'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            json_data = json.dumps(pdf_files, ensure_ascii=False)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error loading PDF list: {str(e)}")

    def serve_pdf_download(self):
        """Serve PDF file for download"""
        try:
            # Extract filename from URL
            filename = urllib.parse.unquote(self.path[10:])  # Remove '/download/'
            file_path = Path(os.path.dirname(os.path.abspath(__file__))) / filename
            
            if not file_path.exists() or not file_path.suffix.lower() == '.pdf':
                self.send_error(404, "PDF file not found")
                return
                
            # Send file with proper PDF headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(file_path.stat().st_size))
            self.end_headers()
            
            # Send the actual file
            with open(file_path, 'rb') as f:
                self.copyfile(f, self.wfile)
                
        except Exception as e:
            self.send_error(500, f"Error serving PDF: {str(e)}")

    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "localhost"

def run_server(port=8000):
    """Run the network-accessible server"""
    # Set the current directory to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Bind to all network interfaces (0.0.0.0) to allow external access
        with socketserver.TCPServer(("0.0.0.0", port), NetworkHandler) as httpd:
            local_ip = get_local_ip()
            print(f"🌐 Servidor web executant-se!")
            print(f"")
            print(f"📱 Accés local (Chrome):     http://localhost:{port}")
            print(f"📱 Accés des del telèfon:    http://{local_ip}:{port}")
            print(f"")
            print(f"💡 Assegura't que el telèfon està connectat a la mateixa xarxa WiFi")
            print(f"")
            print("Pressiona Ctrl+C per aturar el servidor")
            print("-" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Servidor aturat.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"⚠️ Port {port} ja està en ús. Provant amb el port {port + 1}...")
            run_server(port + 1)
        else:
            print(f"❌ Error iniciant el servidor: {e}")

if __name__ == "__main__":
    run_server()
