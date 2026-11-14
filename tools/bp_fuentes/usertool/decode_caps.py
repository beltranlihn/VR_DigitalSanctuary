import re,base64,glob,os
for f in sorted(glob.glob('cap_*.txt')):
    s=open(f,encoding='utf-8',errors='ignore').read()
    m=re.search(r'[A-Za-z0-9+/=]{5000,}',s)
    if not m: print(f,'sin base64'); continue
    b=base64.b64decode(m.group(0)); out=f[:-4]+'.png'; open(out,'wb').write(b); print(out,len(b))
