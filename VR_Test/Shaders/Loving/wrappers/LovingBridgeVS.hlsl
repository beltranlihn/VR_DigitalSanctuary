// @uses SS,Hash,Shape,CoreWob,Calm,NeckBreath,BallsLayout,CentreGap,ArmSetup,BridgeSetup,SminS,SminH,Surr,StrandR,ArmField3,BridgeR,AmPod,AmBody,CentreR,Mound
// @inputs LocalPos,GA,GB,BPr,LV0,LV1,LV2,LV3,LV4,LV5
// @outputs return:Float3,Nrm:Float3,Misc:Float3,Misc2:Float2
// PUENTE entre dos grupos vecinos: tubo de FORMA CERRADA (sin biseccion) sobre el eje A->B,
// radio = reloj de arena con cintura con signo (munones -> contacto -> cuello).
// Normal de superficie de revolucion. Recorte EXACTO contra los brazos de A y de B: evalua
// sus campos 3D con la MISMA libreria, asi la pelicula del puente desaparece justo donde
// entra en la envoltura (y la del brazo, donde entra en el puente) -> una sola capa.
// Y contra la MEMBRANA DEL NUCLEO: a calma alta la cuerda entre dos grupos vecinos pasa por
// donde se suman los dos abultamientos (hasta 6 cm dentro de la membrana y 2 cm dentro del
// nucleo opaco a S = 1, revision 2026-09-27). Misc2.x = distancia con signo a esa membrana
// (misma ameba + los abultamientos de A y B + CentreGap): la pelicula del puente se apaga
// adentro y dibuja su linea de Plateau en el borde, igual que el brazo.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float4 BA, BB, BS;
L.BridgeSetup(GA, GB, BPr.x, LV0, LV1, LV2, LV3, BA, BB, BS);
float3 lp = LocalPos;
float  t  = saturate((lp.y + 100.0) * 0.005);
float2 rc = normalize(lp.xz + float2(1.0e-4, 0.0));
float3 A  = BA.xyz;
float3 d  = BB.xyz - A; float Lb = max(length(d), 0.1); d /= Lb;
float3 Nb = normalize(cross(d, LV4.xyz) + float3(0.0, 0.0, 1.0e-5));
float3 Bb = cross(d, Nb);
float  s  = t * Lb;
float  dpr;
float  pr = L.BridgeR(s, BA, BB, BS, dpr);
float3 rdir = Nb * rc.x + Bb * rc.y;
float3 dst  = A + d * s + rdir * pr;
Nrm = normalize(rdir - d * dpr);
float4 a0, a1, a2, b0, b1, b2, a3, a4, a5, a6;
float J;
L.ArmSetup(GA, LV0, LV1, LV2, LV3, LV4, LV5, T, a0, a1, a2, b0, b1, b2, a3, a4, a5, a6);
float fa = L.ArmField3(dst, a0, a1, a2, b0, b1, b2, a3, a4, a5, J);
L.ArmSetup(GB, LV0, LV1, LV2, LV3, LV4, LV5, T, a0, a1, a2, b0, b1, b2, a3, a4, a5, a6);
float fb = L.ArmField3(dst, a0, a1, a2, b0, b1, b2, a3, a4, a5, J);
float other = min(fa, fb);
Misc  = float3(saturate(1.0 - max(other, 0.0) / max(a3.w, 0.1)), pr, other);
float Rcq, rbq, gpq, Renq, rMq, rEq, lamq, kCq, kNq, kEq, Raq, MHq, kBq, WAq;
L.Shape(LV0, LV1, LV2, LV3, Rcq, rbq, gpq, Renq, rMq, rEq, lamq, kCq, kNq, kEq, Raq, MHq, kBq, WAq);
float  gCq = L.CentreGap(LV1, LV3, Rcq);
float3 Cq  = LV0.xyz;
float3 wq  = dst - Cq; float lq = max(length(wq), 1.0e-3); float3 uq = wq / lq;
float3 gTq, gmq = float3(0.0, 0.0, 0.0);
float  rCq = L.CentreR(uq, Rcq, LV1, LV3, T, gTq);
rCq += L.Mound(uq, float4(normalize(GA.xyz - Cq + float3(1.0e-4, 0.0, 0.0)), MHq), 0.55, gmq);
rCq += L.Mound(uq, float4(normalize(GB.xyz - Cq + float3(1.0e-4, 0.0, 0.0)), MHq), 0.55, gmq);
Misc2 = float2(lq - (rCq + gCq), t);
float3 off = dst - lp;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
