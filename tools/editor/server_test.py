"""server_test.py - checks the save rules of serve_editor.py on a TEMPORARY copy of obra/ (the real score is never touched).
  python tools/editor/server_test.py      -> exit 0 if all pass
"""
import json, os, shutil, subprocess, sys, tempfile, threading, time, urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import serve_editor as S  # noqa: E402

tmp = tempfile.mkdtemp(prefix='vvr-server-test-')
OB = os.path.join(tmp, 'obra')
shutil.copytree(os.path.join(S.ROOT, 'obra', 'score'), os.path.join(OB, 'score'), ignore=shutil.ignore_patterns('history', 'copias'))
# the score under test is the frozen fixture (schema 2, F0): the owner's edits of the live score must not change these checks
shutil.copyfile(os.path.join(S.ROOT, 'tools', 'score', 'fixtures', 'f0-score.json'), os.path.join(OB, 'score', 'score.json'))
os.makedirs(os.path.join(OB, 'unreal'))
S.OBRA, S.SCORE, S.HISTORY, S.COPIES, S.INBOX = OB, os.path.join(OB, 'score', 'score.json'), os.path.join(OB, 'score', 'history'), os.path.join(OB, 'score', 'copias'), os.path.join(OB, 'audio', 'inbox')
S.ROOT = tmp
srv = ThreadingHTTPServer(('127.0.0.1', 0), S.Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d' % srv.server_address[1]
fails = 0


def req(method, path, body=None, headers=None):
    r = urllib.request.Request(BASE + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(r) as f:
            return f.status, json.loads(f.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')


def check(name, ok, info=''):
    global fails
    print(('  ok   ' if ok else '  FAIL ') + name + ('  · ' + info if info else ''))
    fails += 0 if ok else 1


raw = open(S.SCORE, 'rb').read()
score = json.loads(raw)
h0, rev0 = S.sha12(raw), score['rev']
put = lambda sc, rev, h, force=False: req('PUT', '/api/score', json.dumps(sc).encode(), {'X-Base-Rev': str(rev), 'X-Base-Hash': h or '', 'X-Force': '1' if force else '0'})

# A saves on top of what it opened
a = dict(score, rev=rev0 + 1, savedBy='A')
st, j = put(a, rev0, h0)
check('A saves rev %d' % (rev0 + 1), st == 200 and j.get('hash'), str(st))
hA = j.get('hash')
# B opened the same version and saves later: refused, with who saved
b = dict(score, rev=rev0 + 1, savedBy='B')
st, j = put(b, rev0, h0)
check('B (opened the old version) is refused with who saved', st == 409 and j.get('savedBy') == 'A', '%s %s' % (st, j.get('savedBy')))
check("A's work is still on disk", json.load(open(S.SCORE, encoding='utf-8')).get('savedBy') == 'A')
# B chooses to overwrite
st, j = put(b, rev0, h0, force=True)
check('B can overwrite on purpose (X-Force)', st == 200 and json.load(open(S.SCORE, encoding='utf-8')).get('savedBy') == 'B')
# same rev, different content on disk (e.g. a git pull): refused by the hash
disk = json.load(open(S.SCORE, encoding='utf-8'))
st, j = put(dict(disk, savedBy='C'), disk['rev'], 'deadbeef0000')
check('same rev but different content on disk is refused (hash)', st == 409)
# a broken score never reaches the disk
st, j = put({'schema': 2, 'elements': {}}, disk['rev'], S.sha12(open(S.SCORE, 'rb').read()))
check('a broken score is refused', st == 400, j.get('error', ''))
# 6 saves at the same time: no crash, score.json always there, every old version in history with its own name
cur = S.sha12(open(S.SCORE, 'rb').read()); rv = json.load(open(S.SCORE, encoding='utf-8'))['rev']
res = []
ths = [threading.Thread(target=lambda i=i: res.append(put(dict(disk, rev=rv + 1, savedBy='T%d' % i), rv, cur, force=True))) for i in range(6)]
[t.start() for t in ths]; [t.join() for t in ths]
check('6 simultaneous saves: no errors', all(r[0] == 200 for r in res), str([r[0] for r in res]))
check('score.json is there and valid', json.load(open(S.SCORE, encoding='utf-8')).get('schema') == 2)
hist = os.listdir(S.HISTORY)
check('history keeps every previous version with its own name', len(hist) == len(set(hist)) and len(hist) >= 8, '%d files' % len(hist))
# copies
st, j = req('POST', '/api/score/copy?who=B&why=conflict', json.dumps(score).encode())
check('a copy is kept in obra/score/copias/', st == 200 and os.path.isfile(os.path.join(tmp, j.get('path', ''))), j.get('path', ''))
# GET /obra/ serves what is under obra/ and nothing else: a folder NEXT to it shares its prefix (obra-old/), which a startswith test lets through
os.makedirs(os.path.join(tmp, 'obra-old'))
with open(os.path.join(tmp, 'obra-old', 'secret.json'), 'w') as f:
    f.write('{"secret": 1}')
st, j = req('GET', '/obra/../obra-old/secret.json')
check('GET /obra/../obra-old/x is not served (a folder that only shares the prefix)', st == 404 and 'secret' not in j, str(st))
st, j = req('GET', '/obra/../score/score.json')
check('GET /obra/../x is not served either', st == 404, str(st))
st, j = req('GET', '/obra/score/score.json')
check('what is under obra/ is still served', st == 200 and j.get('schema') == 2, str(st))
# nothing sent to Unreal yet: partitura_propuesta.json is asked every 20 s; `null` (no proposal), not a 404 that shows as a red console error each time
st, j = req('GET', '/obra/unreal/partitura_propuesta.json')
check('GET /obra/unreal/partitura_propuesta.json with nothing sent is 200 null (no red 404 in the console every 20 s)', st == 200 and j is None, '%s %r' % (st, j))
st, j = req('GET', '/obra/unreal/not_there.json')
check('any other file that is not there is still a 404', st == 404, str(st))
# the rules of the piece (lote 5 design B section 8.4): tools/score/check.mjs runs with node inside the write lock, against the score on
# disk, after the conflict tests and before anything is written. Only what is NEW is refused (the two known anchor loops are not)
cur = lambda: json.load(open(S.SCORE, encoding='utf-8'))
chash = lambda: S.sha12(open(S.SCORE, 'rb').read())
nhist = lambda: len(os.listdir(S.HISTORY))
clone = lambda o: json.loads(json.dumps(o))


def put_next(sc, force=False):
    c = cur()
    return put(dict(sc, rev=c['rev'] + 1, savedBy='CHK'), c['rev'], chash(), force)


def looped(sc, nth=0):
    # a new anchor loop: an element of a moment hangs from the end of an element of the next moment, which follows this one
    # (nth: which moment pair, so a second loop can be made on top of the first)
    n = clone(sc)
    order = [b for a in n['acts'] for b in a['beats']]
    for i in range(3, len(order) - 1):
        a, b = order[i], order[i + 1]
        at = n['beats'][b].get('at') or {}
        if at.get('ref') != a or at.get('edge') != 'end':
            continue
        ea = next((k for k, e in n['elements'].items() if e['beat'] == a and e['group'] not in ('fx', 'amb') and not e.get('help') and not (e.get('end') or {}).get('ref')), None)
        eb = next((k for k, e in n['elements'].items() if e['beat'] == b and not e.get('help')), None)
        if ea and eb:
            if nth:
                nth -= 1
                continue
            n['elements'][ea]['at'] = {'ref': eb, 'edge': 'end', 'off': 0}
            return n
    raise Exception('no moment pair for a loop')


def refused_422(name, sc, code, force=False, needle=None):
    h, n = chash(), nhist()
    st, j = put_next(sc, force)
    errs = j.get('errors') or []
    check('%s: 422, nothing written (file and history as they were)' % name,
          st == 422 and j.get('code') == 'invariants' and j.get('error') == 'the score breaks a rule' and any(e.get('code') == code and e.get('msg') and isinstance(e.get('ids'), list) for e in errs)
          and (needle is None or any(needle in e.get('msg', '') for e in errs)) and chash() == h and nhist() == n, '%s %s' % (st, [(e.get('code'), e.get('msg')) for e in errs][:2]))


base2 = cur()
st, j = put_next(base2)
check('the score with its two known anchor loops saves, and the answer says the full check ran', st == 200 and j.get('check') == 'full' and 'checkWhy' not in j, '%s %s' % (st, j))
loop = looped(cur())
refused_422('a NEW anchor loop', loop, 'S.CYCLE.NEW', needle='anchor loop')
refused_422('  not even with X-Force (that only skips the conflict, never the rules)', loop, 'S.CYCLE.NEW', force=True)
st, j = put_next(loop)
check('  the 422 lists the errors with code, message and the ids to select', j.get('errors') and all(set(e) >= {'code', 'msg', 'ids'} for e in j['errors']) and j['errors'][0]['ids'], str(j.get('errors', [])[:1]))
bt_dang = clone(cur()); bt_dang['beats'][next(iter(bt_dang['beats']))]['at'] = {'ref': 'bt_gone', 'edge': 'end', 'off': 0}
refused_422('a moment anchored to nothing', bt_dang, 'S.ANCHOR.MISSING', needle='Moment')
help_dang = clone(cur()); hid = next(i for i, e in help_dang['elements'].items() if e.get('help')); help_dang['elements'][hid]['help'] = 'el_gone'
refused_422('a help line whose wait does not exist', help_dang, 'S.ANCHOR.MISSING', needle='is the help of')
el_dang = clone(cur()); el_dang['elements'][next(iter(el_dang['elements']))]['at'] = {'ref': 'el_gone', 'edge': 'end', 'off': 0}
h, n = chash(), nhist(); st, j = put_next(el_dang)
check('an element anchored to nothing is already stopped by the quick structural check (400), before node runs', st == 400 and chash() == h and nhist() == n, str(st))
dup = clone(cur()); some_bt, some_el = next(iter(dup['beats'])), next(iter(dup['elements'])); dup['elements'][some_bt] = clone(dup['elements'][some_el])
refused_422('an id in both the moments and the elements', dup, 'S.IDS.DUP', needle='used more than once')
dup2 = clone(cur()); dup2['acts'].append(clone(dup2['acts'][0]))
refused_422('an act listed twice', dup2, 'S.IDS.DUP')
huge = clone(cur()); last_bt = [b for a in huge['acts'] for b in a['beats']][-1]
hk = next(k for k, e in huge['elements'].items() if e['beat'] == last_bt and e.get('dur') and e['group'] not in ('fx', 'amb') and not e.get('help')); huge['elements'][hk]['dur'] = {'mode': 'fixed', 'value': 4000}
refused_422('a typical total of more than an hour', huge, 'S.TOTAL', needle='over 60:00')
check('a refused score can still be kept: /api/score/copy does not judge it (the card offers it)', req('POST', '/api/score/copy?who=B&why=rule-broken', json.dumps(loop).encode())[0] == 200)
check('the file on disk is still the last good one', cur().get('savedBy') == 'CHK')

# a check that cannot run never stops a save (fail open), and says so: no node, VVR_CHECK=off, a timeout, bad input, a crash
node0, checker0, to0 = S.NODE, S.CHECKER, S.CHECK_TIMEOUT
S.NODE = None
st, j = put_next(loop)
check('no node on the server: the save goes through, check: structural-only, and says why', st == 200 and j.get('check') == 'structural-only' and 'node' in j.get('checkWhy', '') and cur().get('savedBy') == 'CHK', '%s %s' % (st, j))
S.NODE = os.path.join(tmp, 'no-such-node')
st, j = put_next(loop)
check('a node that cannot be started (VVR_NODE pointing nowhere) is the same', st == 200 and j.get('check') == 'structural-only', '%s %s' % (st, j))
S.NODE = node0
os.environ['VVR_CHECK'] = 'off'
st, j = put_next(loop)
check('VVR_CHECK=off: not run on purpose, check: structural-only', st == 200 and j.get('check') == 'structural-only' and j.get('checkWhy') == 'VVR_CHECK=off', '%s %s' % (st, j))
del os.environ['VVR_CHECK']
st, j = put_next(loop)
check('what was saved without the check is the base now: the same score saves again (grandfathered), check: full', st == 200 and j.get('check') == 'full', '%s %s' % (st, j))
refused_422('  a SECOND new loop on top of it is refused again', looped(cur(), 1), 'S.CYCLE.NEW')
# a fake checker stands for node: every way a verdict can fail to come
fake = os.path.join(tmp, 'fake_check.py')
open(fake, 'w').write("""import json, os, sys, time
mode = os.environ.get('FAKE_CHECK', '')
sys.stdin.buffer.read()
if mode == 'verdict':
    print(json.dumps({'ok': False, 'errors': [{'code': 'S.CYCLE.NEW', 'msg': 'fake loop', 'ids': ['x']}]})); sys.exit(1)
if mode == 'crash':
    sys.stderr.write('Error: boom\\n   at somewhere\\n'); sys.exit(1)
if mode == 'badinput':
    sys.stderr.write('check.mjs: the score on standard input is not valid JSON\\n'); sys.exit(2)
if mode == 'slow':
    time.sleep(5)
if mode == 'garbage':
    print('not json'); sys.exit(0)
if mode == 'empty1':
    print(json.dumps({'ok': False, 'errors': []})); sys.exit(1)
print(json.dumps({'ok': True, 'errors': [], 'warnings': []}))
""")
S.NODE, S.CHECKER = sys.executable, fake
fresh = lambda: dict(cur(), savedBy='FAKE')
os.environ['FAKE_CHECK'] = 'verdict'
h, n = chash(), nhist(); st, j = put_next(fresh())
check('(fake checker) exit 1 with its errors in the JSON is a verdict: 422', st == 422 and j['errors'][0]['msg'] == 'fake loop' and chash() == h and nhist() == n, str(st))
for mode, why in (('crash', 'boom'), ('badinput', 'not valid JSON'), ('garbage', 'no verdict'), ('empty1', 'no verdict')):
    os.environ['FAKE_CHECK'] = mode
    st, j = put_next(fresh())
    check('(fake checker) %s is not a verdict: the save goes through, check: failed, with the reason' % mode, st == 200 and j.get('check') == 'failed' and why in j.get('checkWhy', ''), '%s %s' % (st, j))
os.environ['FAKE_CHECK'] = 'slow'; S.CHECK_TIMEOUT = 0.5
t0 = time.time(); st, j = put_next(fresh())
check('(fake checker) no answer in time: the save goes through, check: failed, and the wait was bounded', st == 200 and j.get('check') == 'failed' and 'more than' in j.get('checkWhy', '') and time.time() - t0 < 4, '%s %s %.1fs' % (st, j, time.time() - t0))
os.environ['FAKE_CHECK'] = 'ok'; S.CHECK_TIMEOUT = to0
st, j = put_next(fresh())
check('(fake checker) exit 0 with ok: check: full', st == 200 and j.get('check') == 'full')
S.NODE, S.CHECKER = node0, os.path.join(tmp, 'no-such-check.mjs')
st, j = put_next(fresh())
check('a checker script that is not there (node exits 1 without a verdict): failed, the save goes through', st == 200 and j.get('check') == 'failed', '%s %s' % (st, j))
S.CHECKER = checker0
del os.environ['FAKE_CHECK']
# no score on disk yet: nothing to compare with (no --base), the check still runs
score_path0 = S.SCORE
S.SCORE = os.path.join(tmp, 'elsewhere', 'score.json')
st, j = put(dict(base2, rev=1, savedBy='FIRST'), 0, '', True)
check('the very first save (no score on disk) is checked without a base: it holds, check: full', st == 200 and j.get('check') == 'full' and os.path.isfile(S.SCORE), '%s %s' % (st, j))
S.SCORE = score_path0
check('the history still has every version that was replaced (a refused save never touched it)', nhist() >= 8)

# schema 3 (lote 5 design B section 2, step 4): the server saves schema 2 and 3, checks the references schema 3 adds (branch, alt,
# blocking), and the schema only goes up: an old tab can never save a schema 2 score over a schema 3 one
def disk_score():
    return json.load(open(S.SCORE, encoding='utf-8'))


def disk_hash():
    return S.sha12(open(S.SCORE, 'rb').read())


base = disk_score()
key_id = lambda k: next(i for i, e in base['elements'].items() if e['key'] == k)
share, v36c, v37, v35c, gb = key_id('G_SHARE'), key_id('VO_36c'), key_id('VO_37'), key_id('VO_35c'), key_id('G_BREATH')


def s3_body(rev):
    s = json.loads(json.dumps(base))
    s.update(schema=3, rev=rev, savedBy='S3')
    s['branches'] = {'share': {'name': 'Share or not', 'gate': share, 'options': {'yes': {'label': 'SHARE'}, 'no': {'label': "DON'T SHARE"}}, 'default': 'yes', 'onTimeout': 'no'}}
    s['elements'][v36c]['branch'] = {'on': 'share', 'value': 'yes'}
    s['elements'][v37]['alt'] = {'share=no': {'at': {'ref': v35c, 'edge': 'end', 'off': 0}}}
    s['elements'][gb]['gate']['blocking'] = False
    return s


def refused(name, fn, needle):
    s = s3_body(disk_score()['rev'] + 1)
    fn(s)
    st, j = put(s, disk_score()['rev'], disk_hash())
    check('a schema 3 score with %s is refused with its reason' % name, st == 400 and needle in j.get('error', ''), '%s %s' % (st, j.get('error', '')))


h_before = disk_hash()
refused('a schema newer than the server reads', lambda s: s.update(schema=4), 'not a schema 2 or 3')
refused('the schema written as text', lambda s: s.update(schema='3'), 'not a schema 2 or 3')
refused('an element in a branch that does not exist', lambda s: s['elements'][v36c].update(branch={'on': 'nope', 'value': 'yes'}), 'its branch is not a branch option')
refused('an element in an option that does not exist', lambda s: s['elements'][v36c].update(branch={'on': 'share', 'value': 'maybe'}), 'its branch is not a branch option')
refused('a decision with one option', lambda s: s['branches']['share']['options'].pop('no'), 'at least two options')
refused('a default that is not an option', lambda s: s['branches']['share'].update(default='maybe'), 'default or onTimeout')
refused('an alternative anchor to something that does not exist', lambda s: s['elements'][v37]['alt']['share=no']['at'].update(ref='el_gone'), 'points to something that does not exist')
refused('an alternative of an option that does not exist', lambda s: s['elements'][v37].update(alt={'share=maybe': {'at': {'ref': v35c, 'edge': 'end'}}}), 'not a branch option of the score')
refused('an alternative with an end on a moment', lambda s: s['beats'][base['elements'][v37]['beat']].update(alt={'share=no': {'end': {'ref': v35c, 'edge': 'end'}}}), 'a moment has no end anchor')
refused('blocking written as text', lambda s: s['elements'][gb]['gate'].update(blocking='no'), 'blocking is true or false')
check('  none of them wrote anything', disk_hash() == h_before)
rv = disk_score()['rev']
st, j = put(s3_body(rv + 1), rv, disk_hash())
check('a well-formed schema 3 (branch, alt, a stage-clock wait) saves', st == 200 and disk_score().get('schema') == 3 and disk_score()['branches']['share']['default'] == 'yes', str(st))

# the schema only goes up
rv, hv, n_hist = disk_score()['rev'], disk_hash(), len(os.listdir(S.HISTORY))
down = dict(base, rev=rv + 1, savedBy='OLD')
st, j = put(down, rv, hv)
check('an old editor saving schema 2 over the schema 3 on disk is refused: 409 code schema-down, and the reason', st == 409 and j.get('code') == 'schema-down' and 'schema 3' in j.get('error', '') and 'schema 2' in j.get('error', ''), '%s %s' % (st, j.get('error', '')))
st, j = put(down, rv, hv, force=True)
check('  not even with X-Force (overwrite theirs with mine)', st == 409 and j.get('code') == 'schema-down', str(st))
check('  the file on disk and its history are untouched', disk_hash() == hv and len(os.listdir(S.HISTORY)) == n_hist and disk_score().get('schema') == 3)
st, j = put(down, rv - 1, 'deadbeef0000')
check('  an editor that also opened an older rev gets the ordinary conflict first (who saved), so its card can offer a copy', st == 409 and 'code' not in j and j.get('savedBy') == 'S3', '%s %s' % (st, j))
st, j = put(dict(s3_body(rv + 1), savedBy='S3b'), rv, hv)
check('schema 3 over schema 3 saves as ever', st == 200 and disk_score().get('savedBy') == 'S3b', str(st))
check('a copy of a schema 3 score is kept (the conflict card of a schema 3 editor needs it); an unknown schema is not', req('POST', '/api/score/copy?who=B&why=conflict', json.dumps(s3_body(9)).encode())[0] == 200
      and req('POST', '/api/score/copy?who=B&why=conflict', json.dumps(dict(base, schema=4)).encode())[0] == 400 and req('POST', '/api/score/copy?who=B&why=conflict', json.dumps(base).encode())[0] == 200)

# the upgrade to schema 3 (Edits.migrate3, lote 5 design B section 10) writes what this server accepts: schema 3 over the schema 2 score on
# disk, with the full check; and the way back is refused. It runs on the frozen fixture (never the live score) in a score of its own
REPO = os.path.dirname(os.path.dirname(HERE))
MIGRATE = ("const fs=require('fs'),p=require('path'),R=process.argv[1];"
           "const E=require(p.join(R,'web/editor-obra/app/js/engine.js')),X=require(p.join(R,'web/editor-obra/app/js/edits.js'));"
           "const s=JSON.parse(fs.readFileSync(p.join(R,'tools/score/fixtures/f0-score.json'),'utf8')),c=JSON.parse(fs.readFileSync(p.join(R,'tools/score/fixtures/contract-f0.json'),'utf8'));"
           "const r=X.migrate3(s,E,c,{who:'T'});if(!r.next){process.stderr.write(JSON.stringify(r.report.refusals));process.exit(1)}"
           "process.stdout.write(JSON.stringify(r.next))")
BIND = ("const fs=require('fs'),p=require('path'),R=process.argv[1];"
        "const E=require(p.join(R,'web/editor-obra/app/js/engine.js')),X=require(p.join(R,'web/editor-obra/app/js/edits.js'));"
        "const rd=f=>JSON.parse(fs.readFileSync(p.join(R,f),'utf8'));"
        "const s=rd('tools/score/fixtures/f0-score.json'),c=rd('tools/score/fixtures/contract-f0.json');"
        "const m=X.migrate3(s,E,c,{who:'T'});if(!m.next){process.stderr.write(JSON.stringify(m.report.refusals));process.exit(1)}"
        "const b=X.bindUnreal(m.next,rd('tools/score/fixtures/marks-seed-v1.json'),rd('tools/score/fixtures/idmap-20261008.json'),c,rd('obra/unreal/roles.json'),{Engine:E});"
        "if(!b.next){process.stderr.write(JSON.stringify(b.report.refusals));process.exit(1)}"
        "process.stdout.write(JSON.stringify(b.next))")
if S.NODE:
    mg = subprocess.run([S.NODE, '-e', MIGRATE, REPO], capture_output=True, timeout=60)
    check('node upgrades the frozen fixture to schema 3 (Edits.migrate3)', mg.returncode == 0, mg.stderr.decode('utf-8', 'replace')[:200])
    if mg.returncode == 0:
        keep = S.SCORE
        S.SCORE = os.path.join(tmp, 'upgrade', 'score.json')
        os.makedirs(os.path.dirname(S.SCORE))
        fx = json.load(open(os.path.join(REPO, 'tools', 'score', 'fixtures', 'f0-score.json'), encoding='utf-8'))
        open(S.SCORE, 'w', encoding='utf-8').write(json.dumps(fx))
        h2 = disk_hash()
        up = dict(json.loads(mg.stdout), rev=fx['rev'] + 1, savedBy='UP')
        st, j = put(up, fx['rev'], h2)
        check('the upgraded score (schema 3, branches, baseline, uidMap) saves over the schema 2 one: 200, check: full', st == 200 and j.get('check') == 'full' and disk_score().get('schema') == 3, '%s %s' % (st, j.get('error') or j.get('errors') or ''))
        check('  what is on disk is what was sent: 592 elements, 665 stable names, no golden', len(disk_score()['elements']) == 592 and len(disk_score()['uidMap']) == 665 and 'golden' not in disk_score() and disk_score()['branches']['share']['default'] == 'yes')
        rv, hv = disk_score()['rev'], disk_hash()
        st, j = put(dict(fx, rev=rv + 1, savedBy='OLD'), rv, hv)
        check('  the way back (the schema 2 score over the upgraded one) is refused: 409 schema-down', st == 409 and j.get('code') == 'schema-down' and disk_hash() == hv, '%s %s' % (st, j.get('code')))
        # "Bind to Unreal" (Edits.bindUnreal, lote 5 design A section 3): marks in the moments and a bind on the elements, over the upgraded
        # score. The server saves it with the full check and refuses a malformed one (400, nothing written); a schema 2 score with marks is
        # refused by the check (422): marks and bind belong to schema 3
        bd = subprocess.run([S.NODE, '-e', BIND, REPO], capture_output=True, timeout=60)
        check('node binds the upgraded fixture to Unreal (Edits.bindUnreal, frozen seed and idmap)', bd.returncode == 0, bd.stderr.decode('utf-8', 'replace')[:200])
        if bd.returncode == 0:
            bound = json.loads(bd.stdout)
            rv, hv = disk_score()['rev'], disk_hash()
            st, j = put(dict(bound, rev=rv + 1, savedBy='BIND'), rv, hv)
            on = disk_score()
            check('the bound score (marks in 73 moments, a bind on 378 elements) saves over the upgraded one: 200, check: full', st == 200 and j.get('check') == 'full'
                  and sum(1 for b in on['beats'].values() if b.get('marks')) == 73 and sum(1 for e in on['elements'].values() if e.get('bind')) == 378, '%s %s' % (st, j.get('error') or j.get('errors') or ''))
            bkey = lambda k: next(i for i, e in bound['elements'].items() if e['key'] == k)
            bbeat = lambda k: next(i for i, b in bound['beats'].items() if b['key'] == k)

            def bad_bind(name, fn, needle):
                x = json.loads(json.dumps(bound))
                fn(x)
                r0, h0 = disk_score()['rev'], disk_hash()
                st, j = put(dict(x, rev=r0 + 1, savedBy='BAD'), r0, h0)
                check('a bound score with %s is refused (400) with its reason, nothing written' % name, st == 400 and needle in j.get('error', '') and disk_hash() == h0, '%s %s' % (st, j.get('error', '')))
            bad_bind('marks that are not a list', lambda x: x['beats'][bbeat('1.4')].update(marks={'name': 'S0.OPEN'}), 'marks is not a list')
            bad_bind('a mark Unreal does not emit', lambda x: x['beats'][bbeat('1.4')]['marks'][0].update(name='S9.OPEN'), 'not a mark Unreal emits')
            bad_bind('S4.BYE (the last stage has no farewell)', lambda x: x['beats'][bbeat('1.4')]['marks'][0].update(name='S4.BYE'), 'not a mark Unreal emits')
            bad_bind('a relation that does not exist', lambda x: x['beats'][bbeat('1.4')]['marks'][0].update(rel='around'), 'has relation')
            bad_bind('an el mark on an element of another moment', lambda x: x['beats'][bbeat('V2')]['marks'][0].update(el=bkey('FX_BELLRING')), 'not in this moment')
            def del_marked(x):   # the clip an el mark hangs on is deleted (its name stays in the uidMap as deleted-here, as the editor does)
                el = x['beats'][bbeat('V2')]['marks'][0]['el']
                del x['elements'][el]
                for u in x.get('uidMap', {}).values():
                    if u.get('id') == el:
                        u['state'] = 'deleted-here'
            bad_bind('an el mark whose clip was deleted (nothing for it to hang on: the editor takes the mark with the clip)', del_marked, 'not in this moment')
            bad_bind('an el mark without its edge', lambda x: x['beats'][bbeat('V2')]['marks'][0].pop('edge'), 'has no edge')
            bad_bind('two relations of its own in one moment', lambda x: x['beats'][bbeat('1.4')]['marks'].append({'name': 'S0.OPEN', 'rel': 'preview'}), 'one entry, the first')
            bad_bind('a phase mark placed twice', lambda x: x['beats'][bbeat('1.4')].update(marks=[{'name': 'S0.OPEN', 'rel': 'start'}]), 'placed twice')
            bad_bind('knobs (by) that are not a list', lambda x: x['beats'][bbeat('1.2')]['marks'][0].update(by='Titulo_SaleIni'), 'list of names')
            bad_bind('a bind that is not an object', lambda x: x['elements'][bkey('VO_10')].update(bind='vo_alma'), 'bind is not an object')
            bad_bind('an action that is not in the catalog', lambda x: x['elements'][bkey('VO_10')]['bind'].update(action='shout'), 'is not an action')
            bad_bind('a target without role: or tag:', lambda x: x['elements'][bkey('VO_10')]['bind'].update(target='Alma'), 'role:<name> or tag:<name>')
            bad_bind('an asset that is not a name', lambda x: x['elements'][bkey('VO_10')]['bind'].update(asset=''), 'name of an Unreal asset')
            bad_bind('bind.branch set (reserved)', lambda x: x['elements'][bkey('VO_10')]['bind'].update(branch={'on': 'share', 'value': 'yes'}), 'reserved')
            r0, h0 = disk_score()['rev'], disk_hash()
            st, j = put(dict(json.loads(json.dumps(bound)), rev=r0 + 1, savedBy='BIND2'), r0, h0)
            check('  the same bound score again (a save with nothing new) is fine: 200', st == 200 and disk_score().get('savedBy') == 'BIND2', str(st))
            # marks in a schema 2 score: the structural check lets it through (it is dumb on purpose), the full check (the editor's own validation) refuses
            S.SCORE = os.path.join(tmp, 'bind2', 'score.json')
            os.makedirs(os.path.dirname(S.SCORE))
            open(S.SCORE, 'w', encoding='utf-8').write(json.dumps(fx))
            h2 = disk_hash()
            two = json.loads(json.dumps(fx))
            two['rev'] += 1
            next(iter(two['beats'].values()))['marks'] = [{'name': 'HALL.START', 'rel': 'start'}]
            st, j = put(two, fx['rev'], h2)
            check('marks in a schema 2 score are refused by the check: 422 invariants (they belong to schema 3), nothing written', st == 422 and j.get('code') == 'invariants' and any("can't have marks" in e.get('msg', '') for e in j.get('errors', [])) and disk_hash() == h2, '%s %s' % (st, [e.get('msg') for e in j.get('errors', [])][:1]))
        S.SCORE = keep
else:
    print('  info  node was not found: the upgraded score was not offered to the server')

# "Check guion.js for changes" (lote 5 design B section 7.1, step 12): POST /api/guion/scan runs tools/score/extract_v1.mjs with its own output
# (<obra>/score/score.extracted.json) and nothing else: it never writes the score, and the request decides nothing
if S.NODE:
    ext_path = os.path.join(OB, 'score', 'score.extracted.json')
    score_file = S.SCORE
    real_score, real_ext = os.path.join(HERE, '..', '..', 'obra', 'score', 'score.json'), os.path.join(HERE, '..', '..', 'obra', 'score', 'score.extracted.json')
    st_real = (os.stat(real_score).st_mtime_ns, S.sha12(open(real_score, 'rb').read())) if os.path.isfile(real_score) else None
    ext_real = os.stat(real_ext).st_mtime_ns if os.path.isfile(real_ext) else None
    if os.path.isfile(ext_path):
        os.remove(ext_path)
    snap = lambda: {f: (os.stat(os.path.join(OB, 'score', f)).st_mtime_ns, os.path.getsize(os.path.join(OB, 'score', f))) for f in os.listdir(os.path.join(OB, 'score')) if os.path.isfile(os.path.join(OB, 'score', f))}
    before = snap()
    st, j = req('POST', '/api/guion/scan')
    after = snap()
    check('POST /api/guion/scan reads guion.js: 200 and where the extraction is', st == 200 and j.get('ok') is True and j.get('extracted') == '/obra/score/score.extracted.json' and j.get('at') and j.get('bytes', 0) > 100000, '%s %s' % (st, j.get('error') or j.get('ms')))
    ex = json.load(open(ext_path, encoding='utf-8')) if os.path.isfile(ext_path) else {}
    check('  it wrote score.extracted.json (an extraction of today\'s guion.js: schema 2, 592 elements, 73 moments, its golden table) and the editor can fetch it', ex.get('schema') == 2 and len(ex.get('elements', {})) == 592 and len(ex.get('beats', {})) == 73 and 'golden' in ex and req('GET', '/obra/score/score.extracted.json')[0] == 200)
    check('  score.json is untouched: same size, same modification time (the file the scan was asked about)', before.get('score.json') is not None and after.get('score.json') == before.get('score.json'))
    check('  the only change in obra/score is that one file (nothing else written, nothing removed)', set(after) - set(before) == {'score.extracted.json'} and set(before) <= set(after) and all(after[f] == before[f] for f in before))
    check('  and the real project\'s score and extraction were not touched by this test (the scan went to the temp obra/)', (st_real is None or (os.stat(real_score).st_mtime_ns, S.sha12(open(real_score, 'rb').read())) == st_real) and (ext_real is None or os.stat(real_ext).st_mtime_ns == ext_real))
    # the request decides nothing: a path in the query, a body, and the real score's name are all ignored
    b4 = snap()
    st, j = req('POST', '/api/guion/scan?out=../score/score.json&file=obra/score/score.json&path=x', json.dumps({'out': score_file, 'extracted': score_file}).encode())
    af = snap()
    check('  a query or a body that names a path changes nothing: it still writes only score.extracted.json', st == 200 and af.get('score.json') == b4.get('score.json') and sorted(set(af) - set(b4)) == [] and j.get('extracted') == '/obra/score/score.extracted.json')
    # a copy of the prototype with an extra cue is read when VVR_PROTO says so (tests only): the extraction has one more clip
    proto = os.path.join(tmp, 'proto-ghost'); os.makedirs(proto)
    for f in ('guion.js', 'timeline.js', 'world.js', 'ensayo.js'):
        shutil.copy(os.path.join(HERE, '..', '..', 'web', 'prototipo-narrativo', f), os.path.join(proto, f))
    g = open(os.path.join(proto, 'guion.js'), encoding='utf-8').read()
    g2 = g.replace("  ghostSpan('GHOST_BELL'", "  fx('FX_GHOSTAPPEAR', 2, 'extra cue');\n  ghostSpan('GHOST_BELL'")
    assert g2 != g
    open(os.path.join(proto, 'guion.js'), 'w', encoding='utf-8').write(g2)
    os.environ['VVR_PROTO'] = proto
    st, j = req('POST', '/api/guion/scan')
    ex2 = json.load(open(ext_path, encoding='utf-8'))
    check('  with VVR_PROTO on a copy of guion.js that has one more cue: the extraction has it (593 clips) and the copy\'s name', st == 200 and len(ex2['elements']) == 593 and 'proto-ghost' in ex2['source']['file'].replace(os.sep, '/'), '%s %s' % (st, len(ex2.get('elements', {}))))
    del os.environ['VVR_PROTO']
    st, j = req('POST', '/api/guion/scan')
    check('  and back to the real guion.js when it is not set (592 clips)', st == 200 and len(json.load(open(ext_path, encoding='utf-8'))['elements']) == 592)
    # the extractor's own refusal: it never overwrites a file that is not an earlier extraction
    keep_ext = open(ext_path, 'rb').read()
    open(ext_path, 'w', encoding='utf-8').write('{"not": "an extraction"}')
    st, j = req('POST', '/api/guion/scan')
    check('  a score.extracted.json that is not an earlier extraction is never overwritten: 500 with the reason', st == 500 and 'not an earlier extraction' in j.get('error', '') and open(ext_path, encoding='utf-8').read() == '{"not": "an extraction"}', str(j.get('error'))[:120])
    open(ext_path, 'wb').write(keep_ext)
    # failures say why and write nothing
    node0, ext0 = S.NODE, S.EXTRACTOR
    S.NODE = None
    st, j = req('POST', '/api/guion/scan')
    check('  no node: 503, with what to do', st == 503 and 'node' in j.get('error', ''))
    S.NODE = node0
    S.EXTRACTOR = os.path.join(tmp, 'no-such-extractor.mjs')
    st, j = req('POST', '/api/guion/scan')
    check('  an extractor that cannot run: 500 with the reason, the earlier extraction stays', st == 500 and j.get('error') and open(ext_path, 'rb').read() == keep_ext, str(j.get('error'))[:100])
    S.EXTRACTOR = ext0
    # GET is not a scan (a link or an image tag cannot trigger it)
    try:
        gst = urllib.request.urlopen(urllib.request.Request(BASE + '/api/guion/scan', method='GET')).status
    except urllib.error.HTTPError as e:
        gst = e.code
    check('  GET /api/guion/scan is nothing (only POST reads guion.js: a link or an image tag cannot trigger it)', gst in (404, 405), str(gst))
else:
    print('  info  node was not found: the guion.js scan was not offered to the server')

# WAV in the inbox by element id; no silent overwrite
wav = b'RIFF' + b'\0' * 4 + b'WAVE' + b'\0' * 32
check('WAV saved by element id', req('POST', '/api/audio?name=el_test123', wav)[0] == 200)
check('a second WAV with the same name is refused', req('POST', '/api/audio?name=el_test123', wav)[0] == 409)
check('...unless overwrite=1 (same element loads a new file)', req('POST', '/api/audio?name=el_test123&overwrite=1', wav)[0] == 200)

# the recordings are read-only: the final mix wins over an earlier take, nothing outside the folder is served
S.MEDIA = os.path.join(tmp, 'media'); S._media.update(at=0, index={})
mix_dir, take_dir = os.path.join(S.MEDIA, 'Soul Charger VO MEZCLA final', '1_Inicio'), os.path.join(S.MEDIA, 'Soul Charger VO')
os.makedirs(mix_dir); os.makedirs(take_dir)
pcm = b'\0' * 96000   # 1 s of 48 kHz mono 16-bit
hdr = b'RIFF' + (36 + len(pcm)).to_bytes(4, 'little') + b'WAVEfmt ' + (16).to_bytes(4, 'little') + (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') \
    + (48000).to_bytes(4, 'little') + (96000).to_bytes(4, 'little') + (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + b'data' + len(pcm).to_bytes(4, 'little')
open(os.path.join(mix_dir, '01_VO_99a.wav'), 'wb').write(hdr + pcm)
open(os.path.join(take_dir, 'VO_99a.mp3'), 'wb').write(b'ID3')
open(os.path.join(take_dir, 'VO_99b.mp3'), 'wb').write(b'ID3')
open(os.path.join(tmp, 'outside.wav'), 'wb').write(hdr + pcm)
st, j = req('GET', '/api/media')
it = j.get('items', {})
check('media index: final mix first, with its length from the header', it.get('VO_99a', {}).get('src') == 'mix' and abs((it['VO_99a'].get('dur') or 0) - 1.0) < 1e-6, str(it.get('VO_99a')))
check('media index: an earlier take where there is no mix', it.get('VO_99b', {}).get('src') == 'take')


def raw_get(path):
    try:
        with urllib.request.urlopen(BASE + path) as f:
            return f.status, f.read()
    except urllib.error.HTTPError as e:
        return e.code, b''


st, body = raw_get(it['VO_99a']['url'])
check('a recording is served as is', st == 200 and body == hdr + pcm, str(st))
check('nothing outside the media folder is served', raw_get('/media/%2e%2e/outside.wav')[0] == 404 and raw_get('/media/..%2F..%2Fobra%2Fscore%2Fscore.json')[0] == 404 and raw_get('/media/D:%2Fx.wav')[0] == 404)

# sound effects: only the files obra/audio/media_map.json names, inside the media root or a fixed root ('unreal:', 'recursos:')
fx_dir, rec_dir, ue_dir = os.path.join(S.MEDIA, 'FX'), os.path.join(tmp, 'Recursos', 'Music'), os.path.join(tmp, 'VR_Test', 'Content', 'x')
for d in (fx_dir, rec_dir, ue_dir):
    os.makedirs(d)
half = hdr[:40] + (48000).to_bytes(4, 'little') + b'\0' * 48000   # 0.5 s
open(os.path.join(fx_dir, 'Door.wav'), 'wb').write(hdr + pcm)
open(os.path.join(fx_dir, 'notes.txt'), 'w').write('not audio')
open(os.path.join(rec_dir, 'Amb 1.wav'), 'wb').write(half)
open(os.path.join(ue_dir, 'FX_98.wav'), 'wb').write(hdr + pcm)
os.makedirs(os.path.join(OB, 'audio'), exist_ok=True)
MAP = os.path.join(OB, 'audio', 'media_map.json')
json.dump({'version': 1, 'note': 'test', 'map': {
    'FX_99': 'FX/Door.wav', 'AMB_99': 'recursos:Music/Amb 1.wav', 'FX_98': 'unreal:Content/x/FX_98.wav',
    'FX_ESC': '../outside.wav', 'FX_ESC2': 'unreal:../outside.wav', 'FX_ESC3': 'recursos:../outside.wav', 'FX_ABS': os.path.join(tmp, 'outside.wav'),
    'FX_ROOT': 'nope:outside.wav', 'FX_SLASH': 'recursos:/outside.wav', 'FX_GONE': 'FX/nothing.wav', 'FX_TXT': 'FX/notes.txt',
    'VO_99a': 'FX/Door.wav', 'VO_77': 'FX/Door.wav', 'lower_id': 'FX/Door.wav'},
    'gain': {'AMB_99': 0.4, 'FX_98': 7}, 'why': {'FX_99': 'the door'}, 'unmapped': {'FX_NONE': 'no file yet'}}, open(MAP, 'w'))
S._media['at'] = 0
st, j = req('GET', '/api/media')
it = j.get('items', {})
fx = it.get('FX_99', {})
check('a mapped sound effect is in the index as fx, with its length from the header and why', fx.get('src') == 'fx' and abs((fx.get('dur') or 0) - 1.0) < 1e-6 and fx.get('why') == 'the door' and fx.get('path') == 'FX/Door.wav', str(fx))
check("mapped files under 'recursos:' and 'unreal:' are in the index, with Unreal's volume", it.get('AMB_99', {}).get('gain') == 0.4 and abs((it.get('AMB_99', {}).get('dur') or 0) - .5) < 1e-6 and it.get('FX_98', {}).get('src') == 'fx' and 'gain' not in it.get('FX_98', {}), str(it.get('AMB_99')))
check('a mapped path that leaves its root is skipped (../, absolute, unknown root)', not any(k in it for k in ('FX_ESC', 'FX_ESC2', 'FX_ESC3', 'FX_ABS', 'FX_ROOT', 'FX_SLASH')))
check('a missing mapped file, or one that is not audio, is skipped', 'FX_GONE' not in it and 'FX_TXT' not in it and 'lower_id' not in it)
check('voices keep their name matching: the map never replaces or adds a voice', it.get('VO_99a', {}).get('src') == 'mix' and 'VO_77' not in it)
check('the reasons of what is not mapped travel with the index', j.get('unmapped') == {'FX_NONE': 'no file yet'} and j.get('mapError') is None)
st, body = raw_get(fx.get('url', '/x'))
check('a mapped sound effect is served as is', st == 200 and body == hdr + pcm, str(st))
st, body = raw_get(it.get('AMB_99', {}).get('url', '/x'))
check("a mapped file under 'recursos:' is served as is", st == 200 and body == half, str(st))
check('only mapped ids are served (nothing by path, nothing skipped)', raw_get('/api/media/fx/FX_ESC')[0] == 404 and raw_get('/api/media/fx/FX_GONE')[0] == 404 and raw_get('/api/media/fx/..%2F..%2Fobra%2Fscore%2Fscore.json')[0] == 404 and raw_get('/api/media/fx/VO_99a')[0] == 404)
os.remove(os.path.join(fx_dir, 'Door.wav'))
check('a mapped file deleted after the index was built is not served', raw_get(fx['url'])[0] == 404)
open(MAP, 'w').write('{ broken')
S._media['at'] = 0
st, j = req('GET', '/api/media')
check('a broken map never breaks the voices, and says why', 'VO_99a' in j.get('items', {}) and 'FX_99' not in j.get('items', {}) and 'media_map.json' in (j.get('mapError') or ''), str(j.get('mapError')))

srv.shutdown()
shutil.rmtree(tmp, ignore_errors=True)
print('\n%s' % ('%d FAILED' % fails if fails else 'all ok'))
sys.exit(1 if fails else 0)
