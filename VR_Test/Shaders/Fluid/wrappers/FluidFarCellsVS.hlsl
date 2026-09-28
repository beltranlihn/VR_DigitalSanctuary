// @uses FluidColor,AbsorbAt,SinCurl,RotR,RotRT,FlowAt,WrapHead,FacingBasis,LiveClock
// @inputs LocalPos,Crn,SdA,SdB,CamL,Head,Drift,DriftVel,Phase,Flow,Absorb,FTop,FMid,FBot,Glow,Caus,FarA,Light
// @outputs return:Float3,FA:Float4,FB:Float4,LQ:Float4
// CÉLULAS LEJANAS (F2): siluetas en un quad cada una (SM_FluidFarCells_SC: 64 quads con semillas
// en las UV, la técnica de las partículas), todas en UNA llamada. Port de FAR_VS del prototipo.
//   FarA = (lado del cubo cm, tamaño cm, cuánto las mueven los remolinos, cuántas de las 64)
// Aparecen por cercanía entre 7 y 11 m (antes serían células medias) y se funden en el fondo por
// absorción. Salidas: FA = (color del medio, absorción) · FB = (fundido, semilla, giro, -) · LQ = la luz
// del MUNDO (Light, la de Loving y las medias) en la base del quad: antes era una constante de pantalla y
// las siluetas quedaban iluminadas del lado contrario a las medias (revisión MAT-3).
// El fundido por cercanía/borde va al COLOR en el PS y la silueta se ACHICA en el último tramo: el
// alpha-to-coverage del móvil cuantiza a 4 niveles (25 %) y el fundido por alfa aparecía a saltos
// (revisión MAT-2 / MOV-1 / INT-2).
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float phF, phC;
float3 drift;
L.LiveClock(Phase, Caus, Drift, DriftVel, T, phF, phC, drift);
float4 seed = float4(SdA.x, SdA.y, SdB.x, SdB.y);
float cube = max(FarA.x, 1.0);
float3 anchor = L.WrapHead(seed.xyz * cube + drift, Head.xyz, cube);
float3 P = anchor + L.FlowAt(anchor, phF, Flow) * FarA.z;
float3 toP = P - CamL.xyz;
float dist = max(length(toP), 1.0);
float3 rel = anchor - Head.xyz;
float edge = 1.0 - smoothstep(0.38, 0.5, max(max(abs(rel.x), abs(rel.y)), abs(rel.z)) / cube);
float on = step(frac(seed.w * 13.7), FarA.w / 64.0);                 // FarCellCount de 64
float fade = edge * smoothstep(700.0, 1100.0, dist) * on;
FA = float4(L.FluidColor(toP / dist, FTop, FMid, FBot, Glow, Absorb), L.AbsorbAt(dist, Absorb));
// giro ENVUELTO en 2 pi (todos sus usos son 2 pi-periódicos): llega en half al PS y sin envolver se
// cuantizaba cada vez más con el tiempo de juego (revisión MAT-7 / MOV-5).
FB = float4(fade, seed.w, 6.2831853 * frac(seed.w + T * 0.03 * (frac(seed.w * 5.3) - 0.5) / 6.2831853), 0.0);
float size = FarA.y * (0.7 + 0.6 * frac(seed.w * 3.1)) * smoothstep(0.0, 0.3, fade);
float3 f, rgt, upv;
L.FacingBasis(P, CamL.xyz, f, rgt, upv);
float3 Lw = normalize(Light.xyz + float3(0.0, 0.0, 1.0e-3));
LQ = float4(dot(Lw, rgt), dot(Lw, upv), dot(Lw, f), 0.0);
float2 c2 = Crn.xy * 2.0 - 1.0;
float3 dst = (fade > 0.002) ? P + (rgt * c2.x + upv * c2.y) * size : P;   // apagada: sin área
float3 off = dst - LocalPos.xyz;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 20000.0) / max(ol, 1.0e-4));
