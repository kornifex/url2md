import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

HTML = "text/html"

# path → (status, content type, body, extra headers)
ROUTES: dict[str, tuple[int, str, bytes, dict[str, str]]] = {
    "/links/page.html": (
        200,
        HTML,
        b'<html><body><h1>Title</h1><p><a href="/docs/guide">Guide</a> '
        b'<img src="img/logo.png" alt="logo"></p></body></html>',
        {},
    ),
    "/base.html": (
        200,
        HTML,
        b'<html><head><base href="https://cdn.example/assets/"></head>'
        b'<body><a href="file.pdf">File</a></body></html>',
        {},
    ),
    "/latin1-header.html": (
        200,
        f"{HTML}; charset=iso-8859-1",
        "<html><body><p>Éléphant à côté</p></body></html>".encode("latin-1"),
        {},
    ),
    "/latin1-meta.html": (
        200,
        HTML,
        '<html><head><meta charset="iso-8859-1"></head><body><p>Éléphant à côté</p></body></html>'
        "".encode("latin-1"),
        {},
    ),
    "/js.html": (
        200,
        HTML,
        b"<html><body><div id=app></div><script>setTimeout(() => {"
        b"document.getElementById('app').innerHTML = '<h1>Rendered by JS</h1>'}, 200)"
        b"</script></body></html>",
        {},
    ),
    "/to-login": (302, HTML, b"", {"Location": "/login"}),
    "/login": (200, HTML, b"<html><body><h1>Log in</h1></body></html>", {}),
    "/trailing": (301, HTML, b"", {"Location": "/trailing/"}),
    "/trailing/": (200, HTML, b"<html><body><p>Same page</p></body></html>", {}),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, content_type, body, headers = ROUTES.get(
            self.path, (404, HTML, b"<html><body>Not found</body></html>", {})
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="session")
def server():
    """Base URL of a local HTTP server serving ROUTES."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
