#!/usr/bin/env python3
import http.server
import socketserver
import os

class BasicHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            # Serve HTML
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
                self.end_headers()
                
                self.wfile.write(html_content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Error loading HTML: {str(e)}")
                
        elif self.path.startswith('/fonts/'):
            # Serve font files
            font_name = self.path[7:]  # Remove '/fonts/'
            font_path = f'fonts/{font_name}'
            
            try:
                with open(font_path, 'rb') as f:
                    font_data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'font/ttf')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(font_data)))
                self.end_headers()
                
                self.wfile.write(font_data)
            except Exception as e:
                self.send_error(404, f"Font not found: {str(e)}")
                
        elif self.path == '/download/tao.pdf':
            # Serve PDF
            try:
                with open('tao.pdf', 'rb') as f:
                    pdf_data = f.read()
                
                print(f"Serving PDF: {len(pdf_data)} bytes")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Disposition', 'attachment; filename="tao.pdf"')
                self.send_header('Content-Length', str(len(pdf_data)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', 'default-src \'self\'')
                self.end_headers()
                
                self.wfile.write(pdf_data)
            except Exception as e:
                self.send_error(500, f"Error serving PDF: {str(e)}")
        else:
            self.send_error(404, "File not found")

def run_server(port=8000):
    os.chdir('/Users/zen/CascadeProjects/pdf-platform')
    
    try:
        with socketserver.TCPServer(("0.0.0.0", port), BasicHandler) as httpd:
            local_ip = "192.168.0.14"  # Your local IP
            print(f"Servidor bàsic executant-se a:")
            print(f"  Local: http://localhost:{port}")
            print(f"  Xarxa: http://{local_ip}:{port}")
            print(f"\n📱 Per accedir des del telèfon: http://{local_ip}:{port}")
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
