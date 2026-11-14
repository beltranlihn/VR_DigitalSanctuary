# poses.py - calcula las transformadas de BP_UserTool_SC a partir de recon.json (lectura del editor).
# Todo en el marco del GRIP (el MotionController al que se cuelga el actor).
#   SensorXf{R,L}: donde va el sensor nuevo = centro del cilindro viejo (validado en visor), cara (-Z local) = la cara del
#                  sensor viejo segun FacingOK del rig: -Right(GripR) / +Right(GripL)  -> Roll +90 / -90.
#   MandoXf{R,L}:  el mando nuevo = las transformadas de SM_RHand/SM_LHand del dibujo (mismo marco que el Touch Plus).
#   HandRelR:      la mano del pawn (fantasma de autoria).
import json, sys, numpy as np
sys.path.insert(0, '.')
from ue_xf import mat, dec, fmt, xf_text, rotm

R=json.load(open('recon.json'))
def P(k):
    v=R[k]
    return json.loads(v) if isinstance(v,str) else v
def xf(d):
    l=d['relativeLocation']; r=d['relativeRotation']; s=d.get('relativeScale3D') or {'x':1,'y':1,'z':1}
    return mat((l['x'],l['y'],l['z']),(r['pitch'],r['yaw'],r['roll']),(s['x'],s['y'],s['z']))
OLD_CENTER=np.array([1.685,0.0,0.93,1.0])     # centro de la caja de /Game/BreathR en su marco local (medido por Mesh 3D)
out={}
for side,hand,sens,nc,roll in (('R','pawn.HandRight','rig.SensR','tb.SM_RHand',90.0),('L','pawn.HandLeft','rig.SensL','tb.SM_LHand',-90.0)):
    H=xf(P(hand)); S=xf(P(sens)); N=xf(P(nc))
    SG=S@H                                  # sensor viejo en el grip
    c=OLD_CENTER@SG
    Xold=SG[0,:3]/np.linalg.norm(SG[0,:3])
    new=mat(tuple(c[:3]),(0.0,0.0,roll),(1,1,1))
    face=-rotm(0,0,roll)[2]
    out[side]={'hand_in_grip':fmt(H),'old_sensor_in_grip':fmt(SG),'old_axisX_in_grip':np.round(Xold,3).tolist(),
               'new_face_in_grip':np.round(face,3).tolist(),'SensorXf':xf_text(new),'SensorXf_h':fmt(new),
               'MandoXf':xf_text(N),'MandoXf_h':fmt(N),'HandRel':xf_text(H)}
json.dump(out,open('poses.json','w'),indent=1)
for s in out:
    print(s); [print('  ',k,':',v) for k,v in out[s].items()]
