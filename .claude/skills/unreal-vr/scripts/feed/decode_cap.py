import json, base64, sys
def find(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'data' and isinstance(v, str) and len(v) > 1000:
                return v
            r = find(v)
            if r:
                return r
    if isinstance(o, list):
        for v in o:
            r = find(v)
            if r:
                return r
for name in sys.argv[1:]:
    d = find(json.load(open(name + '.txt')))
    open(name + '.png', 'wb').write(base64.b64decode(d))
    print(name, 'ok')
