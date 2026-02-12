import http.server
import socketserver
import webbrowser
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent / 'frontend'

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def run_frontend():
    print(f"🌐 Frontend server running at http://localhost:{PORT}")
    print("📊 Connecting to trading system API at http://localhost:8000")
    print("🔌 WebSocket connecting to ws://localhost:8767")
    print("\nPress Ctrl+C to stop\n")
    
    # Open browser automatically
    webbrowser.open(f'http://localhost:{PORT}')
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    run_frontend()