# importar_mezcla.py - copia los wav de la mezcla de Beltran a Content/ (auto-import del editor, gotcha 434):
# sobre el .wav de cada asset VO existente (mismo nombre -> reimporta, las referencias no cambian) y los nuevos a Obra/Audio.
# Uso: python importar_mezcla.py [--dry]
import os,glob,shutil,sys,json
DRY='--dry' in sys.argv
C=os.path.expanduser('~')+'/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Content'
SRC=os.path.expanduser('~')+'/Desktop/Soul Charger VO MEZCLA final'
ex={}
for p in glob.glob(C+'/**/VO_*.uasset',recursive=True):
    ex.setdefault(os.path.basename(p)[:-7],[]).append(os.path.dirname(p))
rep={'reimport':[],'nuevo':[]}
for w in sorted(glob.glob(SRC+'/*/*.wav')):
    vid=os.path.basename(w)[:-4].split('_',1)[1]
    dests=ex.get(vid) or [C+'/SoulCharger/Obra/Audio']
    for d in dests:
        t=os.path.join(d,vid+'.wav')
        if not DRY: shutil.copyfile(w,t)
        rep['reimport' if vid in ex else 'nuevo'].append(os.path.relpath(t,C).replace(os.sep,'/'))
print(json.dumps({k:len(v) for k,v in rep.items()}),'\nnuevos:',[os.path.basename(x) for x in rep['nuevo']])
