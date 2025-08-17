import http.server
import socketserver
import json
import os
from urllib.parse import urlparse

# NOTE: this imports the single-file client you already updated
from gpt_oss_cli import RouterClient, ClientSettings

PORT = int(os.getenv("PORT", "8000"))
ROOT = os.path.dirname(os.path.abspath(__file__))

# Read settings from .env if present; api_key is optional (no header sent if missing)
settings = ClientSettings()
client = RouterClient(settings)


class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html at /
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/chat":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send_json({"error": "Invalid JSON"}, status=400)

        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return self._send_json({"error": "No message provided"}, status=400)

        try:
            # Uses the helper; internally it calls the same /chat/completions endpoint
            reply = client.get_faq_answer(user_message)
            self._send_json({"response": reply})
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(ROOT)  # ensure index.html is found
    with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
        print(f"Server started at http://127.0.0.1:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
