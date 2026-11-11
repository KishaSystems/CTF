#!/usr/bin/env python3
import http.server
import socketserver

FLAG = "CTF{c00k13s_4r3_n0t_s3ss10ns}"
PORT = 8000

PAGE = """<!DOCTYPE html>
<html><head><title>ORION Portal</title></head>
<body>
<h1>ORION Portal</h1>
<p>Welcome, guest. Your session cookie has been set.</p>
<p>Administrators can visit <a href="/admin">/admin</a>.</p>
</body></html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        cookie = self.headers.get("Cookie", "")
        if self.path.startswith("/admin"):
            if "admin=true" in cookie:
                self.send_response(200)
                body = "<html><body><h1>Admin panel</h1><p>Flag: " + FLAG + "</p></body></html>"
            else:
                self.send_response(403)
                body = "<html><body><h1>403 Forbidden</h1><p>Admins only.</p></body></html>"
        else:
            self.send_response(200)
            body = PAGE
        self.send_header("Set-Cookie", "admin=false; Path=/")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("ORION Portal running at http://localhost:%d" % PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
