import json,sys
d=json.load(open(sys.argv[1]))
def short(r): return r['refPath'].split('.')[-1]
for g,nodes in d.items():
    byn={short(n['node']):n for n in nodes}
    execnodes=[k for k,n in byn.items() if any(p['type_id']=='Exec' for p in n['input_pins']+n['output_pins'])]
    roots=[k for k,n in byn.items() if ('FunctionEntry' in k or 'Event' in k) ]
    seen=set(); order=[]
    st=list(roots)
    while st:
        k=st.pop(0)
        if k in seen: continue
        seen.add(k); order.append(k)
        for p in byn[k]['output_pins']:
            if p['type_id']=='Exec':
                for c in p['connected_pins']:
                    st.append(short(c['node']))
    unreached=[k for k in execnodes if k not in seen]
    # data pins unconnected on impure nodes that are object refs (self etc)
    print(g,'exec_nodes',len(execnodes),'alcanzados',len([k for k in execnodes if k in seen]),'no alcanzados',unreached)
    # pure nodes with no output connections (orphans)
    orph=[k for k,n in byn.items() if k not in execnodes and not any(c for p in n['output_pins'] for c in p['connected_pins'])]
    if orph: print('   huerfanos puros', orph)
