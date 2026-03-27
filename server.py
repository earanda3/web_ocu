#!/usr/bin/env python3
import http.server
import socketserver
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

def start_server(port):
    try:
        with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
            print(f"Servidor iniciat correctament al port {port}")
            print(f"Obre el navegador a: http://localhost:{port}")
            print("Prem Ctrl+C per aturar el servidor")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"El port {port} ja està en ús, provant amb el port {port + 1}...")
            start_server(port + 1)
        else:
            raise

if __name__ == "__main__":
    try:
        start_server(PORT)
    except KeyboardInterrupt:
        print("\nServidor aturat.")
        sys.exit(0)
