# cortar_master.py - corta el master exportado de Ableton en un wav por clip de VO, en los bordes de los clips del .als.
# Cada clip va desde su inicio hasta el inicio del clip siguiente (o fin + COLA s si hay mas espacio), para conservar la
# cola de los efectos (reverb/delay); despues se recorta el silencio final por umbral, dejando un fundido corto.
# Salida: wav 48 kHz 16 bit mono (lo que piden las VO en Unreal), ordenados por acto como la tanda generada.
import gzip,json,os,sys,subprocess,numpy as np,xml.etree.ElementTree as ET,wave
ALS=sys.argv[1]; MASTER=sys.argv[2]; OUT=sys.argv[3]
COLA=4.0          # s maximos de cola despues del fin del clip
UMBRAL_DB=-60.0   # recorte del silencio final
r=ET.fromstring(gzip.open(ALS).read())
bpm=float(r.find('.//MainTrack//Tempo/Manual').get('Value')); spb=60.0/bpm
tr=[t for t in r.findall('.//Tracks/AudioTrack') if any('VO_' in (c.find('Name').get('Value') or '') for c in t.findall('.//Events/AudioClip'))][0]
clips=sorted([(float(c.find('CurrentStart').get('Value')),float(c.find('CurrentEnd').get('Value')),c.find('Name').get('Value')) for c in tr.findall('.//Events/AudioClip')])
raw=subprocess.run(['ffmpeg','-v','error','-i',MASTER,'-ac','1','-ar','48000','-f','f32le','-'],capture_output=True).stdout
x=np.frombuffer(raw,np.float32); sr=48000
lista=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vo_lista.json'),encoding='utf-8'))
act={c['id']:c['act'] for c in lista}
rep=[]
for i,(a,b,n) in enumerate(clips):
    t0=a*spb; t1=b*spb; tn=clips[i+1][0]*spb if i+1<len(clips) else len(x)/sr
    fin=min(t1+COLA,tn)
    seg=x[int(t0*sr):int(fin*sr)].copy()
    # recorte del silencio final (despues del fin del clip), con 50 ms de fundido
    lim=10**(UMBRAL_DB/20); k=len(seg)
    piso=int((t1-t0)*sr)
    while k>piso and np.abs(seg[max(0,k-480):k]).max()<lim: k-=480
    seg=seg[:k]; f=min(len(seg),2400); seg[-f:]*=np.linspace(1,0,f)
    fi=min(len(seg),480); seg[:fi]*=np.linspace(0,1,fi)   # 10 ms de entrada: sin click si entra la cola del clip anterior
    vid=n.split('_',1)[1] if '_' in n else n
    d=os.path.join(OUT,act.get(vid,'otros')); os.makedirs(d,exist_ok=True)
    p=os.path.join(d,n+'.wav'); pk=float(np.abs(seg).max())
    with wave.open(p,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(seg,-1,1)*32767).astype('<i2').tobytes())
    rep.append((n,round(t0,3),round(len(seg)/sr,2),round(20*np.log10(pk+1e-9),1)))
# ruido entre clips (control: lo demas apagado?)
gaps=[]
for i in range(len(clips)-1):
    g0=clips[i][1]*spb+COLA; g1=clips[i+1][0]*spb
    if g1-g0>0.5: gaps.append(20*np.log10(np.abs(x[int(g0*sr):int(g1*sr)]).max()+1e-9))
for row in rep: print(row)
print('bpm',bpm,'clips',len(rep),'master',round(len(x)/sr,1),'s | pico en huecos (dB):',round(max(gaps),1) if gaps else None)
