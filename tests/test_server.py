"""
Super simple test server - minimal version
"""
import http.server
import socketserver
import os

PORT = 8080  # Use a different port

# Simple HTML content
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
        h1 { font-size: 3em; }
    </style>
</head>
<body>
    <h1>🌌 CameronPAD Test Server</h1>
    <p>If you can see this, the server is working!</p>
    <p>Server running on port 8080</p>
    <h2>✅ Success!</h2>
</body>
</html>"""

# Write HTML to file
with open("test.html", "w") as f:
    f.write(html)

print(f"Starting test server on port {PORT}...")
print(f"Open your browser to: http://localhost:{PORT}/test.html")
print("Press Ctrl+C to stop")

try:
    with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Server running on http://localhost:{PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists("test.html"):
        os.remove("test.html")