import sys, numpy as np
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import sim_vida as sv, vida_model as vm
L=np.array([0,-vm.IPD/2,0.]); R=np.array([0,vm.IPD/2,0.])
def estados():
    bp=vm.VidaBP(); bp.Glob=1.0
    out=[]
    for t in np.linspace(0,60,13):
        bp.Tm=t; out.append(("calma",bp.push_dust()))
    bp=vm.VidaBP(); bp.Glob=1.0; bp.start_lateral()
    for fr in np.linspace(0,1,25):
        bp.S=bp.S0+(bp.S1-bp.S0)*fr; bp.Tm=fr*bp.Life
        bp.Rate=1.0+vm.BP["GustStir"]*vm.gust_act((bp.actor.loc+bp.actor.axes()[0]*vm.PROBE_FWD)[:2],bp.gust())
        out.append(("lateral",bp.push_dust()))
    return out
F=np.array([1.,0,0])
def fov(r):
    Dn=r["Dn"]; z=Dn@F
    ax=np.degrees(np.arctan2(Dn[:,1],z)); ay=np.degrees(np.arctan2(Dn[:,2],z))
    return (z>0)&(np.abs(ax)<52)&(np.abs(ay)<48)
worst=[];near_rows=[]
for tag,pv in estados():
    a=sv.dust_centros(pv,L); b=sv.dust_centros(pv,R)
    vis=(fov(a)|fov(b))&((a["al"]>0.05)|(b["al"]>0.05))
    d=np.abs(a["al"]-b["al"]); rel=d/np.maximum(np.maximum(a["al"],b["al"]),1e-6)
    one=vis&(np.minimum(a["al"],b["al"])<0.02)&(np.maximum(a["al"],b["al"])>0.1)  # visible in one eye only
    worst.append((tag,int(vis.sum()),int(one.sum()),float(np.percentile(rel[vis],99)),float(rel[vis].max()), float(a["dist"][one].min()) if one.any() else -1))
    # near band overlapping aliento (40-110 cm)
    nb=vis&(a["dist"]<110); nb95=vis&(a["dist"]<95)
    near_rows.append((tag,int(nb.sum()),int(nb95.sum()), float(a["al"][nb].max()) if nb.any() else 0))
import collections
for tag in ("calma","lateral"):
    w=[x for x in worst if x[0]==tag]
    print(tag,"visibles medio %.0f | motas vistas por UN solo ojo (alfa<0,02 en uno y >0,1 en el otro): medio %.1f max %d | dif. relativa de alfa entre ojos p99 %.2f max %.2f | dist min de esas %.0f cm"%(
        np.mean([x[1] for x in w]),np.mean([x[2] for x in w]),max(x[2] for x in w),np.mean([x[3] for x in w]),max(x[4] for x in w),min([x[5] for x in w if x[5]>0] or [-1])))
    n=[x for x in near_rows if x[0]==tag]
    print("   motas visibles a <110 cm (zona de la pluma del aliento): medio %.1f max %d | a <95 cm (zona de inhalar): medio %.1f | alfa max %.2f"%(np.mean([x[1] for x in n]),max(x[1] for x in n),np.mean([x[2] for x in n]),max(x[3] for x in n)))
# soul clearance parallax: analytic
for dcm in (50,80,100,150,200,300):
    par=np.degrees(vm.IPD*(1/dcm-1/380.))
    print("mota a %4d cm: diferencia entre ojos del angulo mota-metaball = %.2f grados (rampa SoulMargin 2->8 = 6 grados)"%(dcm,par))
