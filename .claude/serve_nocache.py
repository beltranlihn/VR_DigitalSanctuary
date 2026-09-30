"""Servidor local del prototipo web sin caché (para que cada recarga traiga los scripts recién editados).
Uso: python .claude/serve_nocache.py <puerto> <carpeta>"""
import http.server, functools, sys
port, root = int(sys.argv[1]), sys.argv[2]
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate'); self.send_header('Expires', '0'); super().end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=root)).serve_forever()
