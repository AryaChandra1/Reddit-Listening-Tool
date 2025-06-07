from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# Change to the app directory
os.chdir('/app')

# Create a simple HTTP server
server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
print("Server started at http://0.0.0.0:8080")

# Serve until interrupted
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("Server stopped.")
    server.server_close()