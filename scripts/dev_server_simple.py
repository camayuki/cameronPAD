"""
Super simple development server - no fancy dependencies
Just creates a basic HTML page to test that everything is working
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Simple HTML content
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CameronPAD - Development Setup</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 100%);
            color: #e8eaed;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            max-width: 600px;
            padding: 3rem;
            background: rgba(26, 31, 53, 0.8);
            border-radius: 15px;
            border: 1px solid #3d4785;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            text-align: center;
        }
        
        h1 {
            color: #4fc3f7;
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 0 0 20px rgba(79, 195, 247, 0.5);
        }
        
        .status {
            background: rgba(76, 175, 80, 0.2);
            border: 1px solid #4caf50;
            border-radius: 8px;
            padding: 1rem;
            margin: 2rem 0;
            color: #4caf50;
        }
        
        .next-steps {
            background: rgba(79, 195, 247, 0.1);
            border: 1px solid #4fc3f7;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
            text-align: left;
        }
        
        .next-steps h3 {
            color: #4fc3f7;
            margin-top: 0;
        }
        
        .step {
            margin: 1rem 0;
            padding-left: 1rem;
        }
        
        .emoji {
            font-size: 1.2em;
            margin-right: 0.5rem;
        }
        
        a {
            color: #4fc3f7;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌌 CameronPAD</h1>
        
        <div class="status">
            <h2>✅ Development Server Running!</h2>
            <p>Your basic development environment is now active.</p>
        </div>
        
        <div class="next-steps">
            <h3>🚀 Next Steps to Complete Setup:</h3>
            
            <div class="step">
                <span class="emoji">1️⃣</span>
                <strong>Install Dependencies:</strong><br>
                Open PowerShell and run:<br>
                <code>py -m pip install fastapi uvicorn jinja2 python-multipart</code>
            </div>
            
            <div class="step">
                <span class="emoji">2️⃣</span>
                <strong>Install Additional Packages:</strong><br>
                <code>py -m pip install sqlalchemy aiosqlite pydantic python-dotenv bcrypt</code>
            </div>
            
            <div class="step">
                <span class="emoji">3️⃣</span>
                <strong>Run Full CameronPAD:</strong><br>
                Once dependencies are installed, run:<br>
                <code>Start-CameronPAD</code>
            </div>
            
            <div class="step">
                <span class="emoji">🔐</span>
                <strong>Default Login:</strong><br>
                Username: <code>admin</code><br>
                Password: <code>admin123!</code>
            </div>
        </div>
        
        <p><strong>🌐 Server running on:</strong> <a href="http://127.0.0.1:8000">http://127.0.0.1:8000</a></p>
        <p><em>Press Ctrl+C in the terminal to stop the server</em></p>
    </div>
</body>
</html>
"""

def create_simple_server():
    """Create a simple HTTP server for development"""
    PORT = 8000
    
    # Create a temporary index.html file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    
    print("🚀 Starting CameronPAD Simple Development Server...")
    print(f"🌐 Server URL: http://127.0.0.1:{PORT}")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the server
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            
            # Try to open browser automatically
            try:
                webbrowser.open(f"http://127.0.0.1:{PORT}")
                print("🌐 Opening browser automatically...")
            except:
                print("💡 Open your browser manually to: http://127.0.0.1:8000")
            
            # Serve forever
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"❌ Port {PORT} is already in use. Please close any other servers and try again.")
        else:
            print(f"❌ Error starting server: {e}")
    finally:
        # Clean up
        if os.path.exists("index.html"):
            os.remove("index.html")

if __name__ == "__main__":
    create_simple_server()