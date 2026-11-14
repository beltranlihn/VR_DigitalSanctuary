import json,sys
d=json.load(open('nodes_dump.json'))
def short(r): return r['refPath'].split('.')[-1] if isinstance(r,dict) else str(r)
for g in sys.argv[1:]:
    print('=====',g)
    for n in d[g]:
        print(' ', short(n['node']), n['type_id'])
        for p in n['input_pins']:
            c=[short(x['node'])+'#'+str(x['index_id']) for x in p['connected_pins']]
            print('     in ', p['name'], '|', p['type_id'], '| val=', repr(p['value'])[:80], '| <-', c)
        for p in n['output_pins']:
            c=[short(x['node'])+'#'+str(x['index_id']) for x in p['connected_pins']]
            if p['type_id']!='exec' or c: print('     out', p['name'], '|', p['type_id'], '| ->', c)
