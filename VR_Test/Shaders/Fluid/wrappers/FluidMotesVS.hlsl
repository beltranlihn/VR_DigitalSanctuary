// @uses FluidColor,AbsorbAt,Caustic,SinCurl,RotR,RotRT,FlowAt,WrapHead,Stir,FacingBasis
// @inputs LocalPos,Crn,SdA,SdB,CamL,LayerA,LayerB,Head,Drift,DriftVel,Phase,Flow,Absorb,FTop,FMid,FBot,Glow,Caus,Mote,StirK,Hand0,HandV0,Hand1,HandV1
// @outputs return:Float3,ColA:Float4,Bok:Float1
// PARTÍCULAS EN SUSPENSIÓN (una capa por componente; misma malla de quads con semillas en las UV,
// la técnica de SM_LovingDust_SC). Port de MOTE_VS del prototipo:
//   ancla = semilla en el cubo + arrastre de la corriente, reciclada alrededor de la CABEZA
//   P = ancla + remolinos (FlowAt) + manos; velocidad real (la misma cuenta 0,2 s antes) para la estela
//   sprite ORIENTADO HACIA EL OJO (CamL, por ojo); con StirK.y > 0 se estira a lo largo de la velocidad.
// LayerA = (lado del cubo cm, tamaño mín cm, tamaño máx cm, opacidad)
// LayerB = (aparición por cercanía desde/hasta cm, distancia del desenfoque, crecimiento del desenfoque)
// StirK = (remolino de la mano, estela en s). Mote = (color lineal, brillo). Crn = UV0 (esquina),
// SdA = UV1, SdB = UV2 (semillas: la V invertida al importar no les cambia nada).
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
// Phase.w = Live: 1 en juego (el BP integra fases y arrastre); 0 en el editor = reloj propio del
// material con las velocidades de las perillas -> el fluido se mueve en el viewport sin Play.
float live = step(0.5, Phase.w);
float phF = lerp(T * Phase.z, Phase.x, live);
float phC = lerp(T * Caus.z, Phase.y, live);
float3 drift = lerp(DriftVel.xyz * T, Drift.xyz, live);
float4 seed = float4(SdA.x, SdA.y, SdB.x, SdB.y);
float3 cam = CamL.xyz;
float cell = max(LayerA.x, 1.0);
float3 anchor = L.WrapHead(seed.xyz * cell + drift, Head.xyz, cell);
float3 P = anchor + L.FlowAt(anchor, phF, Flow);
// Velocidad (para la estela) y manos SOLO si están en uso: ramas UNIFORMES (valores de la MPC, iguales
// en todo el draw y en las dos evaluaciones del Custom). Con StreakTime 0 la velocidad solo giraba el quad
// dentro de su plano y el PS es radial: la imagen no cambia (revisión COS-3: -33 % del VS de las motas).
float3 vel = float3(0.0, 0.0, 0.0);
[branch] if (StirK.y > 1.0e-4)
{
    float3 aPrev = anchor - DriftVel.xyz * 0.2;
    vel = (P - (aPrev + L.FlowAt(aPrev, phF - Phase.z * 0.2, Flow))) * 5.0;
}
[branch] if (abs(HandV0.w) + abs(HandV1.w) > 0.0)
{
    P += L.Stir(P, Hand0, HandV0, StirK.x) + L.Stir(P, Hand1, HandV1, StirK.x);
}
float3 toP = P - cam;
float dist = max(length(toP), 1.0);
float3 dir = toP / dist;
float3 rel = anchor - Head.xyz;
float edge = 1.0 - smoothstep(0.36, 0.5, max(max(abs(rel.x), abs(rel.y)), abs(rel.z)) / cell);
float nearF = smoothstep(LayerB.x, max(LayerB.y, LayerB.x + 1.0), dist);
float bz = max(LayerB.z, 1.0);
float bok = (1.0 - smoothstep(bz * 0.35, bz, dist)) * step(0.001, LayerB.w);
float e = seed.w;
float size = lerp(LayerA.y, LayerA.z, frac(e * 7.31)) * (1.0 + LayerB.w * bok);
float ab = L.AbsorbAt(dist, Absorb);
float tw = 0.75 + 0.25 * sin(T * (0.6 + 1.3 * frac(e * 3.7)) + 6.2831853 * e);
float spark = Caus.w * L.Caustic(P.xy / max(Caus.y, 1.0), phC);
float3 col = lerp(Mote.rgb * Mote.a * (1.0 + spark), L.FluidColor(dir, FTop, FMid, FBot, Glow, Absorb), ab);
ColA = float4(col, LayerA.w * edge * nearF * tw * (1.0 - ab * Absorb.z) * (1.0 - 0.6 * bok));
Bok = bok;
float3 f, rgt, upv;
L.FacingBasis(P, cam, f, rgt, upv);
float3 vt = vel - f * dot(vel, f);
float sp = length(vt);
float3 ax = (sp > 1.0e-3) ? vt / sp : rgt;
float3 pe = cross(f, ax);
float len = size + sp * StirK.y * (1.0 - bok);
float2 c2 = Crn.xy * 2.0 - 1.0;
// invisible (alfa ~0 por cercanía o borde) -> sin área, como las lejanas y los velos (revisión COS-7)
float3 dst = (ColA.a > 1.0 / 255.0) ? P + ax * (c2.x * len) + pe * (c2.y * size) : P;
float3 off = dst - LocalPos.xyz;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 20000.0) / max(ol, 1.0e-4));
