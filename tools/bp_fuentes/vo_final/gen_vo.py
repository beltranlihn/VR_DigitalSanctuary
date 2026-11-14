# gen_vo.py - genera las 64 VO de vo_lista.json con ElevenLabs y las ordena en el Escritorio para mezclar en Ableton.
# Uso: python gen_vo.py <voice_id> [solo_ids_coma]   (sin procesamiento: nada de de-esser; wav PCM 24 kHz 16 bit mono,
# el maximo sin perdida que permite el plan). Receta: Multilingual v2, la de S2 (stability .75, similarity .80, style 0, speed .85).
import json,os,sys,wave,urllib.request,time
HERE=os.path.dirname(os.path.abspath(__file__))
KEY=open(os.path.expanduser('~/.secrets/elevenlabs.txt')).read().strip()
VID=sys.argv[1]
ONLY=set(sys.argv[2].split(',')) if len(sys.argv)>2 else None
DEST=os.path.join(os.path.expanduser('~'),'Desktop',os.environ.get('VO_DIR','Soul Charger VO 2026-10-01'))
SPEED=float(os.environ.get('VO_SPEED','1.0'))
SET=dict(stability=0.75,similarity_boost=0.80,style=0.0,speed=SPEED,use_speaker_boost=True)
L=json.load(open(os.path.join(HERE,'vo_lista.json'),encoding='utf-8'))
os.makedirs(DEST,exist_ok=True)
ok=0; bad=[]
for c in L:
    if ONLY and c['id'] not in ONLY: continue
    d=os.path.join(DEST,c['act']); os.makedirs(d,exist_ok=True)
    f=os.path.join(d,'%02d_%s.wav'%(c['n'],c['id']))
    body={'text':c['text'],'model_id':'eleven_multilingual_v2','voice_settings':SET}
    r=urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VID}?output_format=pcm_24000',data=json.dumps(body).encode(),
                             headers={'xi-api-key':KEY,'Content-Type':'application/json'})
    for intento in range(3):
        try:
            with urllib.request.urlopen(r,timeout=120) as resp: b=resp.read()
            with wave.open(f,'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(b)
            ok+=1; print('ok',os.path.basename(f),round(len(b)/48000,2),'s'); break
        except Exception as e:
            msg=str(getattr(e,'read',lambda:b'')()[:200]); time.sleep(3)
    else:
        bad.append((c['id'],msg)); print('FALLO',c['id'],msg)
with open(os.path.join(DEST,'00_LISTA_VO.txt'),'w',encoding='utf-8') as t:
    t.write('Soul Charger - Voice overs (2026-10-01)\nVoz: %s | eleven_multilingual_v2 | stability .75 similarity .80 style 0 speed %s | sin procesamiento | wav 24 kHz 16 bit mono\n\n'%(VID,SPEED))
    a=None
    for c in L:
        if c['act']!=a: a=c['act']; t.write('\n== %s ==\n'%a)
        t.write('%02d  %-8s %s\n'%(c['n'],c['id'],c['text']))
print('generados',ok,'fallos',bad)
