"""
Super simple test server - ASCII only
"""
import http.server
import socketserver
import os

PORT = 8080

# Simple HTML content - ASCII only
html = """<!DOCTYPE html>
<html>
<head>
    <title>CameronPAD Test</title>
    <style>
        body { 
            font-family: Arial; 
            background: #0a0e1a; 
            color: #4fc3f7; 
            text-align: center; 
            padding: 50px; 
        }
        h1 { font-size: 3em; color: #4fc3f7; }
        .success { color: #4caf50; font-size: 2em; }
    </style>
</head>
<body>
    <h1>CameronPAD Test Server</h1>
    <p>If you can see this, the server is working!</p>
    <p>Server running on port 8080</p>
    <div class="success">SUCCESS!</div>
    <p>Now you can proceed to install the full dependencies</p>
</body>
</html>"""

# Write HTML to file
with open("test.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Starting test server on port {PORT}...")
print(f"Open your browser to: http://localhost:{PORT}/test.html")
print("Press Ctrl+C to stop")

try:
    with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Server running on http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("Server stopped")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists("test.html"):
        os.remove("test.html")