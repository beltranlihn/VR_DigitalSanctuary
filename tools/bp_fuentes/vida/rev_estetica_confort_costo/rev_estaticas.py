import sys, numpy as np
sys.path.insert(0, r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/.claude/skills/unreal-vr/scripts")
import sim_vida as sv, vida_model as vm
bp=vm.VidaBP(); bp.Glob=1.0
eye=np.array([0,-vm.IPD/2,0.]); F=np.array([1.,0,0])
rows=[]
for t in np.linspace(0,60,13):
    bp.Tm=t; r=sv.dust_centros(bp.push_dust(),eye)
    Dn=r["Dn"]; z=Dn@F; ax=np.degrees(np.arctan2(Dn[:,1],z)); ay=np.degrees(np.arctan2(Dn[:,2],z))
    vis=(z>0)&(np.abs(ax)<52)&(np.abs(ay)<48)&(r["al"]>0.05)
    d=r["dist"][vis]; om=r["om"][vis]; al=r["al"][vis]
    rows.append((d,om,al))
d=np.concatenate([x[0] for x in rows]); om=np.concatenate([x[1] for x in rows]); al=np.concatenate([x[2] for x in rows])
n=len(rows)
for a,b in [(0,100),(100,300),(300,1000),(1000,2000),(2000,4000)]:
    m=(d>=a)&(d<b)
    if m.any(): print("dist %4d-%4d cm: %5.1f motas visibles/cuadro | vel. angular propia p50 %.3f p90 %.3f grados/s | alfa p50 %.2f max %.2f"%(a,b,m.sum()/n,np.percentile(om[m],50),np.percentile(om[m],90),np.percentile(al[m],50),al[m].max()))
# parallax from seated head sway ~1 cm/s lateral
for dd in (100,500,1000,2000):
    print("paralaje por balanceo de cabeza 1 cm/s a %d cm: %.3f grados/s"%(dd,np.degrees(1.0/dd)))
