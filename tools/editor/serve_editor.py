"""Veation VR Studio · local server (stdlib only). Edits the timing of the Soul Charger experience.

Serves web/ (the editor at /editor-obra/app/ and the 3D prototype at /prototipo-narrativo/, same origin so the editor can
drive the prototype's 3D view) and the score files in obra/:

  GET  /obra/<path>          read files under obra/ (score, Unreal contract, roles)
  PUT  /api/score            save obra/score/score.json (schema 2 or 3; the schema only goes up: an older score over a newer one
                             is refused with 409 code 'schema-down', even with X-Force). Headers X-Base-Rev / X-Base-Hash say which
                             version the editor opened: if the disk changed since (someone else saved), 409 with who and when,
                             unless X-Force: 1.
                             Then the invariants (tools/score/check.mjs, run with node inside the write lock, against the score
                             on disk): a rule the new score breaks (a new anchor loop, an anchor to nothing, an id used twice,
                             the typical total out of range...) is refused with 422 {code: 'invariants', errors: [{code, msg,
                             ids}]} and NOTHING is written (the editor offers to save a copy: POST /api/score/copy). If the check
                             cannot run (no node, VVR_CHECK=off, a timeout, an internal error) the save goes ahead and the answer
                             says check: 'structural-only' | 'failed' (and why); it is logged. VVR_NODE = path of node.
                             The previous file is COPIED to obra/score/history/ (unique names, last 40) and the new one is
                             written atomically (temp file + fsync + replace, retried), one save at a time.
  GET  /api/media             the local audio of the piece (read-only): {ID: {url, dur, src}}. Final voice mix first,
                             then the earlier voice takes. Folder: VVR_MEDIA or Recursos/Soul Charger - Escritorio 2026-10/Audio.
                             Then the sound effects and ambiences named in obra/audio/media_map.json (src 'fx'; a path is
                             relative to that folder, or 'unreal:' = VR_Test/, 'recursos:' = Recursos/; a voice is never
                             mapped, a path that leaves its root or a missing file is skipped), and the map's 'unmapped' reasons
  GET  /media/<path>         one of those files
  GET  /api/media/fx/<ID>    the file mapped to a sound id (only files the map names)
  POST /api/guion/scan       read guion.js (tools/score/extract_v1.mjs, run with node, its own default output only): writes
                             obra/score/score.extracted.json and nothing else, never the score, and answers {ok, extracted:
                             '/obra/score/score.extracted.json', at}. The editor then fetches that file and compares it with the
                             score (js/importdiff.js: File > Check guion.js for changes…). No body, no parameters: what is read
                             and where it goes are not up to the request. 503 without node, 500 when the extraction fails
                             (the answer says why). VVR_PROTO = a COPY of web/prototipo-narrativo to read instead (tests only).
  POST /api/score/copy?who=B&why=…   keep a score as obra/score/copias/score-<who>-<why>-<time>.json (conflicts, old drafts)
  POST /api/audio?name=ID    save an uploaded WAV to obra/audio/inbox/<ID>.wav (ID = the element id; 409 if it exists
                             unless &overwrite=1). Imported into Unreal later, in the queue.
  POST /api/audio/rename?from=A&to=B   rename a WAV waiting in the inbox (the sound was renamed in the editor)
  PUT  /api/partitura/propuesta   save obra/unreal/partitura_propuesta.json: timing changes for DA_Partitura_Obra that a
                             session with Unreal open applies (the editor never writes .uasset)

Usage: python tools/editor/serve_editor.py [port] [--open | --app]   (default 8767) → http://localhost:8767/editor-obra/app/
       --open opens the editor in the default browser (also when the server is already running).
       --app  opens it in its own window, like an application (Edge or Chrome app mode: no tabs, no address bar).
       On Windows, double-click tools/editor/abrir-editor.bat (app window).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
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
PROPUESTA = os.path.join(OBRA, 'unreal', 'partitura_propuesta.json')
PDEF = os.path.join(OBRA, 'unreal', 'partitura_def.json')
SOUND_ID = re.compile(r'(FX|VO|AMB)_[A-Za-z0-9_]{1,60}')
ELEM_ID = re.compile(r'el_[A-Za-z0-9]{3,40}')
COPIES = os.path.join(OBRA, 'score', 'copias')
LOCK = threading.Lock()
# the invariants run outside the browser by the same module (design B section 8.4: a second engine in Python would have to be
# kept identical forever). NODE and CHECKER are read at call time (the tests change them)
NODE = os.environ.get('VVR_NODE') or shutil.which('node')
CHECKER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'score', 'check.mjs'))
CHECK_TIMEOUT = 20
# guion.js is read by the same extractor the command line uses; its output is always the one default file (EXTRACTED() is read at call time:
# the tests move OBRA), and a scan never waits for a save (its own lock)
EXTRACTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'score', 'extract_v1.mjs'))
EXTRACT_TIMEOUT = 90
SCAN_LOCK = threading.Lock()
EXTRACTED = lambda: os.path.join(OBRA, 'score', 'score.extracted.json')
MEDIA =os.environ.get('VVR_MEDIA') or os.path.join(ROOT, 'Recursos', 'Soul Charger - Escritorio 2026-10', 'Audio')
MEDIA_DIRS = [('mix', 'Soul Charger VO MEZCLA final'), ('take', 'Soul Charger VO 2026-10-01'), ('take', 'Soul Charger VO')]
AUDIO_EXT = ('.wav', '.mp3', '.ogg')
AUDIO_TYPE = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg'}
MAP_ID = re.compile(r'[A-Z][A-Z0-9]*_[A-Za-z0-9_]{1,60}')
_media = {'at': 0, 'index': {}, 'files': {}, 'unmapped': {}, 'error': None}


def map_roots():
    # where a mapped sound may live: fixed here (the map names files, never folders); read at call time (tests move ROOT)
    return {'': MEDIA, 'unreal': os.path.join(ROOT, 'VR_Test'), 'recursos': os.path.join(ROOT, 'Recursos')}


def inside(full, base):
    try:
        return os.path.commonpath([os.path.abspath(full), os.path.abspath(base)]) == os.path.abspath(base)
    except ValueError:   # another drive
        return False


def resolve_mapped(rel):
    # 'path' (media root) or 'root:path' → the file, or None if the root is unknown, the path leaves it, or it is no audio file
    if not isinstance(rel, str) or not rel.strip():
        return None
    root, sep, p = rel.partition(':')
    if not sep:
        root, p = '', rel
    base = map_roots().get(root)
    if base is None or os.path.isabs(p) or p.startswith(('/', '\\')):
        return None
    full = os.path.abspath(os.path.join(base, p))
    if not inside(full, base) or not full.lower().endswith(AUDIO_EXT) or not os.path.isfile(full):
        return None
    return full


def load_map():
    path = os.path.join(OBRA, 'audio', 'media_map.json')
    if not os.path.isfile(path):
        return {}, None
    try:
        m = json.load(open(path, encoding='utf-8'))
        assert isinstance(m.get('map'), dict), "'map' must be an object"
        return m, None
    except Exception as e:  # a broken map never breaks the voices
        return {}, 'obra/audio/media_map.json: %s' % e


def wav_seconds(path):
    # RIFF header only: data bytes / byte rate (no decoding)
    try:
        with open(path, 'rb') as f:
            h = f.read(12)
            if h[:4] != b'RIFF' or h[8:12] != b'WAVE':
                return None
            rate = None
            while True:
                ck = f.read(8)
                if len(ck) < 8:
                    return None
                cid, size = ck[:4], int.from_bytes(ck[4:], 'little')
                if cid == b'fmt ':
                    fmt = f.read(size)
                    rate = int.from_bytes(fmt[8:12], 'little')
                    continue
                if cid == b'data':
                    return round(size / rate, 3) if rate else None
                f.seek(size + (size & 1), 1)
    except Exception:
        return None


def media_index():
    # cached 30 s: the folders change rarely; the first source that has an ID wins (final mix before takes)
    if time.time() - _media['at'] < 30:
        return _media['index']
    idx = {}
    for src, sub in MEDIA_DIRS:
        base = os.path.join(MEDIA, sub)
        for dp, _, files in os.walk(base):
            for fn in sorted(files):
                if not fn.lower().endswith(AUDIO_EXT):
                    continue
                vid = re.sub(r'^\d+_', '', os.path.splitext(fn)[0])
                if vid in idx:
                    continue
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, MEDIA).replace(os.sep, '/')
                idx[vid] = {'url': '/media/' + '/'.join(urllib_quote(x) for x in rel.split('/')), 'src': src,
                            'dur': wav_seconds(full) if fn.lower().endswith('.wav') else None, 'file': fn}
    # sound effects and ambiences: only what the versioned map names (a voice keeps its name matching, never mapped)
    m, err = load_map()
    files, gains, why = {}, m.get('gain') or {}, m.get('why') or {}
    for sid, rel in (m.get('map') or {}).items():
        if not MAP_ID.fullmatch(str(sid)) or sid.startswith('VO_') or sid in idx:
            continue
        full = resolve_mapped(rel)
        if not full:
            continue
        e = {'url': '/api/media/fx/' + urllib_quote(sid), 'src': 'fx', 'file': os.path.basename(full), 'path': rel,
             'dur': wav_seconds(full) if full.lower().endswith('.wav') else None}
        g = gains.get(sid)
        if isinstance(g, (int, float)) and not isinstance(g, bool) and 0 <= g <= 1:
            e['gain'] = g
        if isinstance(why.get(sid), str):
            e['why'] = why[sid]
        idx[sid], files[sid] = e, full
    un = {k: v for k, v in (m.get('unmapped') or {}).items() if isinstance(k, str) and isinstance(v, str)}
    _media.update(at=time.time(), index=idx, files=files, unmapped=un, error=err)
    return idx


def urllib_quote(x):
    from urllib.parse import quote
    return quote(x)   # one write at a time (ThreadingHTTPServer serves requests in parallel)


def sha12(data):
    return hashlib.sha1(data).hexdigest()[:12]


def atomic_write(path, data):
    # never a moment without the file: unique temp in the same folder, fsync, replace (retried: Windows Defender/indexer)
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + os.path.basename(path) + '.', dir=d)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        for i in range(6):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i == 5:
                    raise
                time.sleep(0.1 * (i + 1))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def check_score(sc):
    # the same references the editor needs to compute (web/editor-obra/app/js/edits.js validate): schema 2 or 3. The server stays
    # dumb and fast: shape and references only, never what they mean (the editor and tools/score judge that)
    v = sc.get('schema')
    assert type(v) is int and v in (2, 3), 'not a schema 2 or 3 score'
    assert isinstance(sc.get('acts'), list) and isinstance(sc.get('groups'), list), 'acts / groups missing'
    for k in ('beats', 'lanes', 'elements'):
        assert isinstance(sc.get(k), dict), k + ' missing'
    for a in sc['acts']:
        for b in a.get('beats', []):
            assert b in sc['beats'], 'act %s points to a missing moment' % a.get('id')
    gids = {g['id'] for g in sc['groups']}
    for g in sc['groups']:
        for l in g.get('lanes', []):
            assert l in sc['lanes'], 'group %s points to a missing lane' % g['id']
    for i, e in sc['elements'].items():
        assert e.get('beat') in sc['beats'] and e.get('lane') in sc['lanes'] and e.get('group') in gids, '%s: missing moment, lane or group' % e.get('key', i)
        for f in ('at', 'end'):
            r = (e.get(f) or {}).get('ref')
            assert not r or r in sc['beats'] or r in sc['elements'], '%s: %s points to something that does not exist' % (e.get('key', i), f)
    if v == 3:
        check_schema3(sc)


def check_schema3(sc):
    # branches, alt anchors and gate.blocking: what the engine reads to time the piece (design B section 2). Same rules as Edits.validate
    br = sc.get('branches')
    assert br is None or isinstance(br, dict), 'branches is not an object'
    br = br or {}
    for on, b in br.items():
        opts = b.get('options') if isinstance(b, dict) else None
        assert isinstance(opts, dict) and len(opts) >= 2, 'branch %s: it needs at least two options' % on
        assert on and '=' not in on and all(o and '=' not in o for o in opts), 'branch %s: names are words without "="' % on
        assert b.get('default') in opts and (b.get('onTimeout') is None or b.get('onTimeout') in opts), 'branch %s: default or onTimeout is not one of its options' % on

    def has_option(on, value):
        return isinstance(on, str) and on in br and value in br[on]['options']

    def alt_ok(x, who, is_beat):
        alt = x.get('alt')
        if alt is None:
            return
        assert isinstance(alt, dict), '%s: alt is not an object' % who
        for k, v in alt.items():
            on, sep, value = k.partition('=')
            assert sep and on and value and '=' not in value and has_option(on, value), '%s: alt "%s" is not a branch option of the score' % (who, k)
            assert isinstance(v, dict) and v and set(v) <= {'at', 'end'}, '%s: alt "%s" holds an at and/or an end anchor' % (who, k)
            assert not (is_beat and 'end' in v), '%s: a moment has no end anchor to change' % who
            for f, a in v.items():
                assert isinstance(a, dict), '%s: an anchor is an object' % who
                r = a.get('ref')
                assert not r or r in sc['beats'] or r in sc['elements'], '%s: alt "%s" %s points to something that does not exist' % (who, k, f)

    for i, e in sc['elements'].items():
        who = e.get('key', i)
        b = e.get('branch')
        assert b is None or (isinstance(b, dict) and has_option(b.get('on'), b.get('value'))), '%s: its branch is not a branch option of the score' % who
        alt_ok(e, who, False)
        g = e.get('gate')
        assert not (isinstance(g, dict) and 'blocking' in g and not isinstance(g['blocking'], bool)), '%s: blocking is true or false' % who
    for i, b in sc['beats'].items():
        alt_ok(b, 'moment %s' % b.get('key', i), True)
    check_bind(sc)


# What a score says about Unreal once it is bound (Edits.validateBind: marks of the moments, bind of the elements). Same rules, kept
# in step by tools/editor/server_test.py; the vocabulary is the one of js/marks.js (the phase numbers of Unreal are not stored)
MARK_NAME = re.compile(r'^(OBRA\.(DISC|END)|HALL\.(START|INTRO)|HALL\.[123]\.\d{1,2}|S[0-4]\.(OPEN|ALMA|INTRO|BEGIN|OUTRO|CHARGE|BYE|REQEND)|FINAL\.(DARK|RETURN|RESULTS|EXIT|CREDITS|FADE)|SHARE\.(ASK|YES|NO))$')
MARK_SUB = re.compile(r'^(HALL\.([123]\.\d+|INTRO)|.*\.REQEND|SHARE\..*)$')
MARK_RELS = ('start', 'el', 'in', 'sub', 'preview')
BIND_ACTIONS = ('vo_alma', 'vo_2d', 'sound', 'sound_at', 'appear', 'disappear', 'ghost', 'ambience', 'title', 'veil', 'wait')
BIND_TARGET = re.compile(r'^(role|tag):.+$')


def check_bind(sc):
    def text(v):
        return isinstance(v, str) and v != ''

    placed = {}
    for i, b in sc['beats'].items():
        marks = b.get('marks')
        if marks is None:
            continue
        who = 'moment %s' % b.get('key', i)
        assert isinstance(marks, list), '%s: marks is not a list' % who
        own = 0
        for n, m in enumerate(marks):
            assert isinstance(m, dict), '%s: a mark is an object' % who
            name = m.get('name')
            assert isinstance(name, str) and MARK_NAME.match(name) and name != 'S4.BYE', '%s: %s is not a mark Unreal emits' % (who, name)
            assert m.get('rel') in MARK_RELS, '%s: %s has relation "%s"' % (who, name, m.get('rel'))
            if m['rel'] != 'el':
                own += 1
                assert own == 1 and n == 0, '%s: its own relation to Unreal is one entry, the first' % who
            else:
                el = m.get('el')
                assert text(el) and el in sc['elements'] and sc['elements'][el].get('beat') == i, '%s: %s is the edge of an element that is not in this moment' % (who, name)
                assert m.get('edge') in ('start', 'end'), '%s: %s has no edge' % (who, name)
            by = m.get('by')
            assert by is None or (isinstance(by, list) and all(text(x) for x in by)), '%s: the knobs (by) of %s are a list of names' % (who, name)
            for f in ('why', 'note', 'elKey'):
                assert m.get(f) is None or isinstance(m[f], str), '%s: the %s of %s is text' % (who, f, name)
            if m['rel'] in ('start', 'el') and not MARK_SUB.match(name):
                assert name not in placed, '%s is placed twice (moments %s and %s)' % (name, placed.get(name), b.get('key', i))
                placed[name] = b.get('key', i)
    for i, e in sc['elements'].items():
        bd = e.get('bind')
        if bd is None:
            continue
        who = e.get('key', i)
        assert isinstance(bd, dict), '%s: bind is not an object' % who
        assert bd.get('action') is None or bd['action'] in BIND_ACTIONS, '%s: "%s" is not an action Unreal knows' % (who, bd.get('action'))
        assert bd.get('asset') is None or text(bd['asset']), '%s: the asset is the name of an Unreal asset' % who
        assert bd.get('target') is None or (isinstance(bd['target'], str) and BIND_TARGET.match(bd['target'])), '%s: the target is role:<name> or tag:<name>' % who
        assert bd.get('branch') is None, '%s: bind.branch is reserved' % who


def full_check(raw):
    """The invariants of the score in `raw` against the one on disk, by node (tools/score/check.mjs --stdin --base). Returns
    (errors, mode, why): errors = the rules it breaks ([] when it holds or was not checked); mode = 'full' | 'structural-only'
    (not run: no node, or VVR_CHECK=off) | 'failed' (it could not give a verdict: timeout, bad input, an internal error).
    Never raises, and a check that cannot run never stops a save (fail open, logged): the editor ran the same check before
    sending, and the structure was already checked here. Only a clean verdict (exit 1 with the errors in its JSON) refuses."""
    if os.environ.get('VVR_CHECK', '').strip().lower() in ('off', '0', 'no', 'false'):
        sys.stderr.write('check skipped: VVR_CHECK=off\n')
        return [], 'structural-only', 'VVR_CHECK=off'
    if not NODE:
        sys.stderr.write('check skipped: node was not found (install Node.js or set VVR_NODE)\n')
        return [], 'structural-only', 'node was not found'
    cmd = [NODE, CHECKER, '--stdin', '--json']
    if os.path.isfile(SCORE):
        cmd += ['--base', SCORE]
    contract = os.path.join(OBRA, 'unreal', 'contract.json')
    if os.path.isfile(contract):
        cmd += ['--contract', contract]
    try:
        p = subprocess.run(cmd, input=raw, capture_output=True, timeout=CHECK_TIMEOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except FileNotFoundError:
        sys.stderr.write('check skipped: cannot run %s\n' % NODE)
        return [], 'structural-only', 'node was not found'
    except subprocess.TimeoutExpired:
        sys.stderr.write('check failed: no answer in %s s\n' % CHECK_TIMEOUT)
        return [], 'failed', 'it took more than %s s' % CHECK_TIMEOUT
    except Exception as e:
        sys.stderr.write('check failed: %s\n' % e)
        return [], 'failed', str(e)
    try:
        out = json.loads(p.stdout.decode('utf-8'))
    except Exception:
        out = None
    if p.returncode == 0 and isinstance(out, dict) and out.get('ok') is True:
        return [], 'full', None
    if p.returncode == 1 and isinstance(out, dict) and out.get('ok') is False and isinstance(out.get('errors'), list) and out['errors']:
        return out['errors'], 'full', None
    lines = [l.strip() for l in p.stderr.decode('utf-8', 'replace').splitlines() if l.strip()]   # exit 2 or a crash: not a verdict
    why = next((l for l in lines if 'rror' in l), lines[0] if lines else 'no verdict')[:200]
    sys.stderr.write('check failed (exit %s): %s\n' % (p.returncode, why))
    return [], 'failed', why


def scan_guion():
    """Read guion.js: run the extractor (node tools/score/extract_v1.mjs --out <obra>/score/score.extracted.json) and say where the
    extraction is. The only file it writes is score.extracted.json (extract_v1 itself refuses the score, the fixture and Unreal's
    folder); the request decides nothing. Returns (status, answer): 200 {ok, extracted, at, bytes}; 503 no node; 500 it failed (why)."""
    if not NODE:
        return 503, {'error': 'node was not found: install Node.js (or set VVR_NODE) to read guion.js'}
    out = EXTRACTED()
    with SCAN_LOCK:
        t0 = time.time()
        try:
            p = subprocess.run([NODE, EXTRACTOR, '--out', out], capture_output=True, timeout=EXTRACT_TIMEOUT,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except subprocess.TimeoutExpired:
            return 500, {'error': 'reading guion.js took more than %s s' % EXTRACT_TIMEOUT}
        except Exception as e:
            return 500, {'error': 'could not run the extractor: %s' % e}
        if p.returncode != 0:
            lines = [l.strip() for l in (p.stderr or p.stdout).decode('utf-8', 'replace').splitlines() if l.strip()]
            why = next((l for l in lines if 'rror' in l), lines[0] if lines else 'exit %s' % p.returncode)
            return 500, {'error': 'the extraction of guion.js failed: %s' % why[:300]}
        try:
            size = os.path.getsize(out)
            assert os.path.getmtime(out) >= t0 - 2
        except Exception:
            return 500, {'error': 'the extraction ran but score.extracted.json is not there'}
    return 200, {'ok': True, 'extracted': '/obra/score/score.extracted.json', 'at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'bytes': size, 'ms': int((time.time() - t0) * 1000)}


def stamp():
    t = time.time()
    return time.strftime('%Y%m%d-%H%M%S', time.localtime(t)) + '-%03d' % int(t * 1000 % 1000)


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.webmanifest': 'application/manifest+json',
                      '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ico': 'image/x-icon'}

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

    def _send_audio(self, full):
        # streamed: an ambience is 30-50 MB
        self.send_response(200)
        self.send_header('Content-Type', AUDIO_TYPE[os.path.splitext(full)[1].lower()])
        self.send_header('Content-Length', str(os.path.getsize(full)))
        self.end_headers()
        try:
            with open(full, 'rb') as f:
                shutil.copyfileobj(f, self.wfile, 1 << 20)
        except (ConnectionError, OSError):   # the page went away mid-file (reload, Sound off)
            pass

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
        if path == '/api/media':
            items = media_index()
            return self._json(200, {'root': MEDIA, 'items': items, 'unmapped': _media['unmapped'], 'mapError': _media['error']})
        if path.startswith('/api/media/fx/'):
            from urllib.parse import unquote
            media_index()
            full = _media['files'].get(unquote(path[len('/api/media/fx/'):]))
            if not full or not os.path.isfile(full):
                return self._json(404, {'error': 'not found'})
            return self._send_audio(full)
        if path.startswith('/media/'):
            from urllib.parse import unquote
            full = os.path.abspath(os.path.join(MEDIA, unquote(path[len('/media/'):])))
            if not inside(full, MEDIA) or not os.path.isfile(full) or not full.lower().endswith(AUDIO_EXT):
                return self._json(404, {'error': 'not found'})
            return self._send_audio(full)
        if path.startswith('/obra/'):
            full = os.path.abspath(os.path.join(OBRA, path[len('/obra/'):]))
            if path == '/obra/unreal/partitura_propuesta.json' and inside(full, OBRA) and not os.path.isfile(full):
                # nothing has been sent to Unreal: the editor asks for this file every 20 s and at every focus, and a 404 is a red error in the
                # console each time. `null` says the same thing (no proposal) without the noise; the editor reads both as "no proposal"
                return self._json(200, None)
            if not inside(full, OBRA) or not os.path.isfile(full):   # inside(), not startswith: a folder next to obra/ (obra-old/) shares its prefix
                return self._json(404, {'error': 'not found', 'path': path})
            data = open(full, 'rb').read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json' if full.endswith('.json') else 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def _put_propuesta(self):
        # agreed with the director (obra/unreal/LEEME.md): same format as partitura.json -> 'valores', only the knobs that change
        try:
            doc = json.loads(self._body().decode('utf-8'))
            kinds = {k['name']: k['type'] for k in json.load(open(PDEF, encoding='utf-8'))['knobs']}
            vals = doc.get('valores'); assert isinstance(vals, dict), 'valores must be an object'
            num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v < 100000
            for k, v in vals.items():
                assert k in kinds, 'unknown knob %r' % k
                ok = (isinstance(v, list) and len(v) == 5 and all(map(num, v))) if kinds[k] == 'a5' else num(v)
                assert ok, '%s: bad value %r' % (k, v)
            for k, m in (doc.get('motivos') or {}).items():
                assert k in vals and isinstance(m, dict), 'motivos[%s] without a value' % k
        except Exception as e:  # never write something the applier can't trust
            return self._json(400, {'error': 'not a valid proposal: %s' % e})
        try:  # Unreal is applying the previous one right now: never swap the file under its feet
            cur = json.load(open(PROPUESTA, encoding='utf-8')) if os.path.isfile(PROPUESTA) else {}
        except Exception:
            cur = {}
        if cur.get('estado') == 'aplicando':
            return self._json(409, {'error': 'Unreal is applying the previous changes right now; try again in a minute'})
        if not doc['valores']:  # nothing proposed: no file, so nobody applies an empty proposal
            if os.path.isfile(PROPUESTA):
                os.remove(PROPUESTA)
            return self._json(200, {'ok': True, 'n': 0})
        with LOCK:
            atomic_write(PROPUESTA, json.dumps(doc, ensure_ascii=False, indent=1).encode('utf-8'))
        return self._json(200, {'ok': True, 'n': len(doc['valores'])})

    def do_PUT(self):
        if urlparse(self.path).path == '/api/partitura/propuesta':
            return self._put_propuesta()
        if urlparse(self.path).path != '/api/score':
            return self._json(404, {'error': 'unknown endpoint'})
        raw = self._body()
        try:
            score = json.loads(raw.decode('utf-8'))
            check_score(score)
        except Exception as e:  # never write something that is not a score
            return self._json(400, {'error': 'not a valid score: %s' % e})
        h = self.headers
        with LOCK:
            cur = open(SCORE, 'rb').read() if os.path.isfile(SCORE) else None
            disk = {}
            if cur is not None:
                try:
                    disk = json.loads(cur.decode('utf-8'))
                except Exception:
                    disk = {}
            if cur is not None and h.get('X-Force') != '1':
                base_rev, base_hash = h.get('X-Base-Rev'), h.get('X-Base-Hash')
                changed = (base_rev is not None and str(disk.get('rev')) != base_rev) or (base_hash and sha12(cur) != base_hash)
                if changed:  # someone saved after this editor opened the score: never erase their work silently
                    return self._json(409, {'error': 'the score changed on disk', 'rev': disk.get('rev'), 'savedBy': disk.get('savedBy'), 'savedAt': disk.get('savedAt'), 'hash': sha12(cur)})
            # the schema only goes up (design B section 2): an editor that knows an older one would erase what the newer one added. Not even with X-Force
            ds = disk.get('schema') if isinstance(disk, dict) else None
            if type(ds) is int and ds > score['schema']:
                msg = ('the score on disk is schema %d and this one is schema %d: an older score cannot replace it. '
                       'Reload the editor (File > Reload from disk) or keep this one as a copy' % (ds, score['schema']))
                return self._json(409, {'code': 'schema-down', 'error': msg, 'diskSchema': ds, 'schema': score['schema']})
            # the rules of the piece (design B section 8.4), after the conflict tests and before anything is written: a refused score
            # leaves the file and its history exactly as they were
            errors, mode, why = full_check(raw)
            if errors:
                return self._json(422, {'code': 'invariants', 'error': 'the score breaks a rule', 'errors': errors})
            if cur is not None:  # copy, never move: score.json is never missing
                os.makedirs(HISTORY, exist_ok=True)
                try:
                    rv = json.loads(cur.decode('utf-8')).get('rev')
                except Exception:
                    rv = 'x'
                dest = os.path.join(HISTORY, 'score-r%s-%s.json' % (rv, stamp()))
                n = 2
                while os.path.exists(dest):
                    dest = dest[:-5] + '-%d.json' % n
                    n += 1
                with open(dest, 'wb') as f:
                    f.write(cur)
                old = sorted((f for f in os.listdir(HISTORY) if f.startswith('score-')), key=lambda f: os.path.getmtime(os.path.join(HISTORY, f)))
                for f in old[:-KEEP]:
                    os.remove(os.path.join(HISTORY, f))
            data = json.dumps(score, ensure_ascii=False, indent=1).encode('utf-8')
            atomic_write(SCORE, data)
        ans = {'ok': True, 'rev': score.get('rev'), 'saved': time.strftime('%H:%M:%S'), 'hash': sha12(data), 'check': mode}
        if why:
            ans['checkWhy'] = why   # saved without the full check: the editor says so
        return self._json(200, ans)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == '/api/guion/scan':
            self._body()   # read and ignored: nothing the page sends changes what is read or where it goes
            code, ans = scan_guion()
            return self._json(code, ans)
        if u.path == '/api/score/copy':
            q = parse_qs(u.query)
            who = re.sub(r'[^A-Za-z0-9]', '', (q.get('who') or ['x'])[0])[:12] or 'x'
            why = re.sub(r'[^A-Za-z0-9-]', '', (q.get('why') or ['copy'])[0])[:30] or 'copy'
            try:
                sc = json.loads(self._body().decode('utf-8'))
                assert type(sc.get('schema')) is int and sc['schema'] in (2, 3), 'not a schema 2 or 3 score'
            except Exception as e:
                return self._json(400, {'error': 'not a score: %s' % e})
            dest = os.path.join(COPIES, 'score-%s-%s-%s.json' % (who, why, stamp()))
            atomic_write(dest, json.dumps(sc, ensure_ascii=False, indent=1).encode('utf-8'))
            return self._json(200, {'ok': True, 'path': os.path.relpath(dest, ROOT).replace(os.sep, '/')})
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
        q = parse_qs(u.query)
        name = (q.get('name') or [''])[0]
        if not (SOUND_ID.fullmatch(name) or ELEM_ID.fullmatch(name)):
            return self._json(400, {'error': 'bad name (an element id el_…, or FX_/VO_/AMB_ + letters, digits, _)'})
        data = self._body()
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            return self._json(400, {'error': 'not a WAV file'})
        dest = os.path.join(INBOX, name + '.wav')
        if os.path.exists(dest) and (q.get('overwrite') or ['0'])[0] != '1':
            return self._json(409, {'error': name + '.wav is already in the inbox'})
        atomic_write(dest, data)
        return self._json(200, {'ok': True, 'path': os.path.relpath(dest, ROOT).replace('\\', '/'), 'bytes': len(data)})


def open_app(url):
    # an application window: Edge ships with Windows, Chrome if present; otherwise the default browser
    cands = [os.path.expandvars(p) for p in (r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe',
                                               r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe',
                                               r'%ProgramFiles%\Google\Chrome\Application\chrome.exe',
                                               r'%LocalAppData%\Google\Chrome\Application\chrome.exe')]
    for exe in cands:
        if os.path.isfile(exe):
            subprocess.Popen([exe, '--app=' + url, '--window-size=1600,940'])
            return
    import webbrowser
    webbrowser.open(url)


class Server(ThreadingHTTPServer):
    # on Windows SO_REUSEADDR lets a second server share the port silently: there it must fail, so a second launch notices
    allow_reuse_address = sys.platform != 'win32'
    daemon_threads = True


if __name__ == '__main__':
    args = sys.argv[1:]
    port = next((int(a) for a in args if a.isdigit()), 8767)
    url = 'http://localhost:%d/editor-obra/app/' % port
    if '--open' in args or '--app' in args:
        import threading
        import webbrowser
        threading.Timer(0.6, open_app if '--app' in args else webbrowser.open, [url]).start()
    try:
        server = Server(('127.0.0.1', port), Handler)
    except OSError:  # already running (another window): the browser still opens on it
        print('Veation VR Studio is already running on %s' % url)
        sys.exit(0)
    print('Veation VR Studio on %s  (close this window to stop it)' % url)
    server.serve_forever()
