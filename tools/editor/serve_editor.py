"""Soul Charger editor · local server (stdlib only).

Serves web/ (the editor at /editor-obra/app/ and the 3D prototype at /prototipo-narrativo/, same origin so the editor can
drive the prototype's 3D view) and the score files in obra/:

  GET  /obra/<path>          read files under obra/ (score, Unreal contract, roles)
  PUT  /api/score            save obra/score/score.json (keeps a timestamped copy in obra/score/history/, last 40)
  POST /api/audio?name=ID    save an uploaded WAV to obra/audio/inbox/<ID>.wav (imported into Unreal later, in the queue)
  POST /api/audio/rename?from=A&to=B   rename a WAV waiting in the inbox (the sound was renamed in the editor)

Usage: python tools/editor/serve_editor.py [port] [--open]   (default 8767) → http://localhost:8767/editor-obra/app/
       --open opens the editor in the default browser (also when the server is already running).
       On Windows, double-click tools/editor/abrir-editor.bat.
"""
import json
import os
import re
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WEB = os.path.join(ROOT, 'web')
OBRA = os.path.join(ROOT, 'obra')
SCORE = os.path.join(OBRA, 'score', 'score.json')
HISTORY = os.path.join(OBRA, 'score', 'history')
INBOX = os.path.join(OBRA, 'audio', 'inbox')
KEEP = 40
SOUND_ID = re.compile(r'(FX|VO|AMB)_[A-Za-z0-9_]{1,60}')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):  # quiet: only errors and writes
        if not (args and str(args[1]).startswith('2')) or self.command != 'GET':
            sys.stderr.write('%s %s\n' % (self.command, fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(n) if n else b''

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/editor-obra/app/')
            self.end_headers()
            return
        if path.startswith('/obra/'):
            full = os.path.abspath(os.path.join(OBRA, path[len('/obra/'):]))
            if not full.startswith(OBRA) or not os.path.isfile(full):
                return self._json(404, {'error': 'not found', 'path': path})
            data = open(full, 'rb').read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json' if full.endswith('.json') else 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_PUT(self):
        if urlparse(self.path).path != '/api/score':
            return self._json(404, {'error': 'unknown endpoint'})
        try:
            score = json.loads(self._body().decode('utf-8'))
            assert score.get('schema') == 2 and isinstance(score.get('elements'), dict)
        except Exception as e:  # never write something that is not a score
            return self._json(400, {'error': 'not a valid score: %s' % e})
        os.makedirs(HISTORY, exist_ok=True)
        if os.path.isfile(SCORE):
            stamp = time.strftime('%Y%m%d-%H%M%S')
            os.replace(SCORE, os.path.join(HISTORY, 'score-%s.json' % stamp))
            old = sorted(f for f in os.listdir(HISTORY) if f.startswith('score-'))
            for f in old[:-KEEP]:
                os.remove(os.path.join(HISTORY, f))
        tmp = SCORE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(score, f, ensure_ascii=False, indent=1)
        os.replace(tmp, SCORE)
        return self._json(200, {'ok': True, 'rev': score.get('rev'), 'saved': time.strftime('%H:%M:%S')})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == '/api/audio/rename':
            q = parse_qs(u.query)
            a, b = (q.get('from') or [''])[0], (q.get('to') or [''])[0]
            if not (SOUND_ID.fullmatch(a) and SOUND_ID.fullmatch(b)):
                return self._json(400, {'error': 'bad sound name (FX_/VO_/AMB_ + letters, digits, _)'})
            src, dest = os.path.join(INBOX, a + '.wav'), os.path.join(INBOX, b + '.wav')
            if not os.path.isfile(src):
                return self._json(404, {'error': 'not in the inbox: ' + a})
            if os.path.exists(dest):
                return self._json(409, {'error': b + '.wav is already in the inbox'})
            os.replace(src, dest)
            return self._json(200, {'ok': True, 'path': os.path.relpath(dest, ROOT).replace(os.sep, '/')})
        if u.path != '/api/audio':
            return self._json(404, {'error': 'unknown endpoint'})
        name = (parse_qs(u.query).get('name') or [''])[0]
        if not SOUND_ID.fullmatch(name):
            return self._json(400, {'error': 'bad sound name (FX_/VO_/AMB_ + letters, digits, _)'})
        data = self._body()
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return self._json(400, {'error': 'not a WAV file'})
        os.makedirs(INBOX, exist_ok=True)
        dest = os.path.join(INBOX, name + '.wav')
        with open(dest, 'wb') as f:
            f.write(data)
        return self._json(200, {'ok': True, 'path': os.path.relpath(dest, ROOT).replace('\\', '/'), 'bytes': len(data)})


class Server(ThreadingHTTPServer):
    # on Windows SO_REUSEADDR lets a second server share the port silently: there it must fail, so a second launch notices
    allow_reuse_address = sys.platform != 'win32'
    daemon_threads = True


if __name__ == '__main__':
    args = sys.argv[1:]
    port = next((int(a) for a in args if a.isdigit()), 8767)
    url = 'http://localhost:%d/editor-obra/app/' % port
    if '--open' in args:
        import threading
        import webbrowser
        threading.Timer(0.6, webbrowser.open, [url]).start()
    try:
        server = Server(('127.0.0.1', port), Handler)
    except OSError:  # already running (another window): the browser still opens on it
        print('The editor is already running on %s' % url)
        sys.exit(0)
    print('Soul Charger editor on %s' % url)
    server.serve_forever()
