#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import urllib.parse
from pathlib import Path

class PDFHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
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
            self.send_header('Content-Disposition', 'attachment; filename="tao.pdf"')
            self.send_header('Content-Length', str(file_path.stat().st_size))
            self.end_headers()
            
            # Send the actual file
            with open(file_path, 'rb') as f:
                self.copyfile(f, self.wfile)
                
        except Exception as e:
            self.send_error(500, f"Error serving PDF: {str(e)}")

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server(port=8000):
    """Run the PDF platform server"""
    try:
        with socketserver.TCPServer(("", port), PDFHandler) as httpd:
            print(f"Servidor executant-se a http://localhost:{port}")
            print("Pressiona Ctrl+C per aturar el servidor")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor aturat.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Port {port} ja està en ús. Provant amb el port {port + 1}...")
            run_server(port + 1)
        else:
            print(f"Error iniciant el servidor: {e}")

if __name__ == "__main__":
    run_server()
