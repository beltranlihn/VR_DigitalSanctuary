// @uses FluidColor,WrapHead,FacingBasis,LiveClock,VeilTable
// @inputs LocalPos,Crn,Idx,CamL,Head,Drift,DriftVel,Phase,Caus,Absorb,FTop,FMid,FBot,Glow,Extras
// @outputs return:Float3,VC:Float4
// VELOS LEJANOS (F3): manchas enormes y tenues de densidad del medio, llevadas por la corriente
// (al 60 %), en un cubo de 60 m alrededor de la cabeza. Los 6 del prototipo en UNA malla
// (SM_FluidVeils_SC): Crn = UV0 (esquina) · Idx = UV1.x (qué velo). Su color es el del medio en
// esa dirección, un poco más claro u oscuro (K.x): se leen como volumen, no como objetos.
// Extras.x = VeilAmount (0 = sin área). Nunca a menos de 4-9 m. VC = (color, opacidad).
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float phF, phC;
float3 drift;
L.LiveClock(Phase, Caus, Drift, DriftVel, T, phF, phC, drift);
float4 C, K;
L.VeilTable(floor(Idx.x + 0.5), C, K);
float cube = 6000.0;
float3 Cc = L.WrapHead(C.xyz + drift * 0.6, Head.xyz, cube);
float3 rel = Cc - Head.xyz;
float3 toC = Cc - CamL.xyz;
float dist = max(length(toC), 1.0);
float edge = 1.0 - smoothstep(0.35, 0.5, max(max(abs(rel.x), abs(rel.y)), abs(rel.z)) / cube);
float a = max(Extras.x, 0.0) * edge * (0.6 + 0.4 * sin(T * 0.05 + K.y)) * smoothstep(400.0, 900.0, dist);
VC = float4(L.FluidColor(toC / dist, FTop, FMid, FBot, Glow, Absorb) * (1.0 + K.x), a);
float3 f, rgt, upv;
L.FacingBasis(Cc, CamL.xyz, f, rgt, upv);
float2 c2 = Crn.xy * 2.0 - 1.0;
float3 dst = (a > 1.0e-3) ? Cc + (rgt * (c2.x * K.z) + upv * c2.y) * C.w : Cc;
float3 off = dst - LocalPos.xyz;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 20000.0) / max(ol, 1.0e-4));
