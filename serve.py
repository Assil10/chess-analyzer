#!/usr/bin/env python3
"""
Simple HTTP server to serve the Chess Analysis Viewer React app.
Run this script and open http://localhost:8000 in your browser.
"""

import http.server
import socketserver
import os
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    print(f"🚀 Starting Chess Analysis Viewer server...")
    print(f"📁 Serving files from: {os.getcwd()}")
    print(f"🌐 Open your browser to: http://localhost:{PORT}")
    print(f"⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"✅ Server running on port {PORT}")
            print(f"📱 Serving: index.html, ChessBoardViewer.jsx, app.jsx, sample_analysis.json")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port or stop the other service.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
