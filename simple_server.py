#!/usr/bin/env python3
import http.server
import socketserver
import os

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/tao' or self.path == '/download/tao.pdf':
            # Serve the PDF directly
            try:
                with open('tao.pdf', 'rb') as f:
                    pdf_data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', 'attachment; filename="tao.pdf"')
                self.send_header('Content-Length', str(len(pdf_data)))
                self.end_headers()
                
                self.wfile.write(pdf_data)
                return
            except Exception as e:
                self.send_error(500, f"Error: {str(e)}")
                return
        
        # Default behavior for other files
        super().do_GET()

def run_server(port=8000):
    os.chdir('/Users/zen/CascadeProjects/pdf-platform')
    
    try:
        with socketserver.TCPServer(("", port), SimpleHandler) as httpd:
            print(f"Servidor simple executant-se a http://localhost:{port}")
            print("Pressiona Ctrl+C per aturar el servidor")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor aturat.")
    except OSError as e:
        if e.errno == 48:
            print(f"Port {port} ja està en ús. Provant amb el port {port + 1}...")
            run_server(port + 1)
        else:
            print(f"Error iniciant el servidor: {e}")

if __name__ == "__main__":
    run_server()
