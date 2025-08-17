import http.server
import socketserver
import json
from gpt_oss_cli.client import RouterClient
from gpt_oss_cli.config import ClientSettings

PORT = 8000

# Initialize the client (no need for API key or base_url now)
settings = ClientSettings()
client = RouterClient(settings)

class ChatHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        # Get the content length and read the data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Parse the data (message from the user)
        data = json.loads(post_data)
        user_message = data.get('message', '')

        if user_message:
            try:
                # Get the FAQ answer based on the user question
                response = client.get_faq_answer(user_message)
                response_data = {'response': response}
            except Exception as e:
                response_data = {'error': str(e)}
        else:
            response_data = {'error': 'No message provided'}

        # Send response back to the frontend
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the HTML file directly
        with open("index.html", "rb") as file:
            self.wfile.write(file.read())

# Create and start the server
with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
    print(f"Server started at http://127.0.0.1:{PORT}")
    httpd.serve_forever()
