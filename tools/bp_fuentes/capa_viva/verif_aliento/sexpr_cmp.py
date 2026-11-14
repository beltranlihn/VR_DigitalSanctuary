import json,re
SRC=open(r'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts/breath_air.dsl',encoding='utf-8').read()
READ=json.load(open('graphs_dump.json'))
def tok(s):
    s=re.sub(r';;[^\n]*','',s)
    out=[];i=0
    while i<len(s):
        c=s[i]
        if c in '()': out.append(c); i+=1
        elif c.isspace(): i+=1
        elif c=='"':
            j=s.index('"',i+1); out.append(s[i:j+1]); i=j+1
        elif c==':' and s[i+1]=='"':
            j=s.index('"',i+2); out.append(s[i:j+1]); i=j+1
        else:
            j=i
            while j<len(s) and not s[j].isspace() and s[j] not in '()': 
                if s[j]=='(' : break
                j+=1
            # handle names like Clamp(Float): include parens if directly followed by Float)
            t=s[i:j]
            m=re.match(r'\((Float|Float\))',s[j:j+7])
            while j<len(s) and s[j]=='(' and re.match(r'\((Float|Int|Vector|Rotator|Integer)\)',s[j:]):
                k=s.index(')',j); t+=s[j:k+1]; j=k+1
            out.append(t); i=j
    return out
def parse(ts):
    stack=[[]]
    for t in ts:
        if t=='(': stack.append([])
        elif t==')': x=stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t)
    return stack[0]
def normsym(s):
    if isinstance(s,list): return s
    s=re.sub(r'^Variables\|[^|]*\|','',s)
    s=re.sub(r'^\|','',s)
    s=re.sub(r'^(Get|Set)b([A-Z])',r'\1\2',s)
    s={'Math|Vector|vector-vector':'-','Math|Vector|vector+vector':'+','Math|Vector|vector*vector':'*','neg':'-'}.get(s,s)
    s=s.replace('ParameterValueOnMaterials','ParameterValueonMaterials')
    if s=='Development|SetHiddenInGame': s='Development|SetHiddeninGame'
    if re.match(r'^-?\d+(\.\d+)?$',s): s=repr(float(s))
    return s
def expand(e,env):
    if isinstance(e,list):
        e=[expand(x,env) for x in e]
        e=[normsym(x) if not isinstance(x,list) else x for x in e]
        if e and e[0]=='Math|Float|Clamp(Float)':
            while len(e)<4: e.append(['0.0','1.0'][len(e)-2])
        if e and e[0]=='Math|Float|Max(Float)' and len(e)==2: e.append('0.0')
        if e and e[0]=='Math|Float|MakeLiteralFloat': return e[1]
        # drop keywords
        out=[]; skip=False
        for x in e:
            if isinstance(x,str) and x.startswith(':') and not x.startswith(':"'): continue
            out.append(x)
        return out
    if e in env: return env[e]
    return normsym(e)
def body(fn):
    # fn = ['fn', name, args, stmts...]
    env={}; stm=[]
    for s in fn[3:]:
        if isinstance(s,list) and s and s[0]=='bind':
            env[s[1]]=expand(s[2],env)
        else:
            stm.append(expand(s,env))
    return stm
src={f[1]:f for f in parse(tok(SRC)) if isinstance(f,list) and f and f[0]=='fn'}
for g in ['AirMPC','PushAir','AirReset','AirStep','AirPerf','AirVisible','AirMountCam','AirMount','AirTick','PreviewAir']:
    r=parse(tok(READ[g]['dsl']))[0]
    a=body(src[g]); b=body(r)
    same = json.dumps(a)==json.dumps(b)
    print(g,'sentencias',len(a),len(b),'IGUAL' if same else 'DISTINTO')
    if not same:
        for i,(x,y) in enumerate(zip(a,b)):
            if json.dumps(x)!=json.dumps(y):
                print('  #',i); print('   src ',json.dumps(x)[:600]); print('   read',json.dumps(y)[:600])
