# ue_xf.py - transforms de Unreal (convencion FRotationMatrix, vectores fila: v' = v*M; hijo_mundo = hijo_rel * padre).
import numpy as np
d2r=np.pi/180
def rotm(p,y,r):
    SP,CP=np.sin(p*d2r),np.cos(p*d2r); SY,CY=np.sin(y*d2r),np.cos(y*d2r); SR,CR=np.sin(r*d2r),np.cos(r*d2r)
    X=[CP*CY, CP*SY, SP]
    Y=[SR*SP*CY-CR*SY, SR*SP*SY+CR*CY, -SR*CP]
    Z=[-(CR*SP*CY+SR*SY), CY*SR-CR*SP*SY, CR*CP]
    return np.array([X,Y,Z])            # filas = ejes X, Y, Z del marco rotado, expresados en el padre
def mat(loc=(0,0,0),rot=(0,0,0),scale=(1,1,1)):
    M=np.eye(4); M[:3,:3]=np.diag(scale)@rotm(*rot); M[3,:3]=loc; return M
def rotator(R):
    X,Y,Z=R[0]/np.linalg.norm(R[0]),R[1]/np.linalg.norm(R[1]),R[2]/np.linalg.norm(R[2])
    p=np.degrees(np.arctan2(X[2],np.hypot(X[0],X[1]))); y=np.degrees(np.arctan2(X[1],X[0]))
    SY=rotm(p,y,0)[1]; SZ=rotm(p,y,0)[2]
    r=np.degrees(np.arctan2(Z@SY, Y@SY))
    return p,y,r
def dec(M):
    R=M[:3,:3]; s=np.linalg.norm(R,axis=1); Rn=R/s[:,None]
    return tuple(M[3,:3]), rotator(Rn), tuple(s)
def fmt(M):
    l,r,s=dec(M)
    return "loc (X=%.4f,Y=%.4f,Z=%.4f) rot (Pitch=%.4f,Yaw=%.4f,Roll=%.4f) scale (%.4f,%.4f,%.4f)"%(l+r+s)
if __name__=='__main__':
    # autoprueba: ida y vuelta de rotadores
    for rr in [(10,20,30),(-90,-10,0),(-13.566261,-83.539335,64.230738),(0,-95,65),(0,0,90)]:
        l,r,s=dec(mat((1,2,3),rr,(1,1,1)))
        assert np.allclose(rotm(*r),rotm(*rr),atol=1e-9),(rr,r)
    # Roll 90: el Z local va al +Y del padre
    print('Z de Roll90 ->', np.round(rotm(0,0,90)[2],6), ' Z de Roll-90 ->', np.round(rotm(0,0,-90)[2],6))
    print('OK')

def quat(p,y,r):
    h=d2r/2
    SP,CP=np.sin(p*h),np.cos(p*h); SY,CY=np.sin(y*h),np.cos(y*h); SR,CR=np.sin(r*h),np.cos(r*h)
    return (CR*SP*SY-SR*CP*CY, -CR*SP*CY-SR*CP*SY, CR*CP*SY-SR*SP*CY, CR*CP*CY+SR*SP*SY)
def xf_text(M):
    l,r,s=dec(M); q=quat(*r)
    return "(Rotation=(X=%.6f,Y=%.6f,Z=%.6f,W=%.6f),Translation=(X=%.6f,Y=%.6f,Z=%.6f),Scale3D=(X=%.6f,Y=%.6f,Z=%.6f))"%(q+l+s)
def qmat(q):
    x,y,z,w=q
    # FQuat -> matriz de rotacion de Unreal (filas = ejes)
    return np.array([[1-2*(y*y+z*z), 2*(x*y+w*z), 2*(x*z-w*y)],
                     [2*(x*y-w*z), 1-2*(x*x+z*z), 2*(y*z+w*x)],
                     [2*(x*z+w*y), 2*(y*z-w*x), 1-2*(x*x+y*y)]])
if __name__=='__main__':
    for rr in [(10,20,30),(-90,-10,0),(-13.566261,-83.539335,64.230738),(0,-95,65),(0,0,90)]:
        assert np.allclose(qmat(quat(*rr)),rotm(*rr),atol=1e-9),rr
    print('quat OK')
