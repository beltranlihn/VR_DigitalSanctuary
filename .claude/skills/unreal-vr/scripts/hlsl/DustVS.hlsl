// DustVS - M_ValleyDust_SC, VERTEX SHADER -> World Position Offset (via Transform vector Local->World). v2 2026-09-28
// EL POLVO SUSPENDIDO del valle de Entering (capa de vida). Cada quad de SM_ValleyDust_SC es una mota que VIVE EN EL
// MUNDO: la malla es la nube (cada quad en su lugar, espacio del actor = los ojos del usuario sentado). Este VS le suma
// el MEANDRO (tres senos lentos por mota, con un numero entero de vueltas en 1800 s: el reloj del BP se envuelve sin
// salto; la amplitud crece con la distancia hasta MeanderFar para que las lejanas no queden congeladas), el REMOLINO
// de la rafaga (un LAZO CERRADO por mota al paso del frente, polinomico: vale 0 EXACTO antes y despues del paso) y la
// DERIVA a favor del viento (Rd x P x Hold: el frente se lleva la mota; despues Hold vuelve a 0 EXACTO y la mota vuelve
// despacio a su lugar), y decide su alfa y su tamano sin estado. Brilla contra el sol bajo del valle (dispersion hacia
// adelante, Henyey-Greenstein).
// Rev. 2: todo lo que decide el ALFA (luz, caida con la distancia, confort cercano y lejano, despeje del metaball,
// velocidad) se calcula desde el punto CICLOPEO VidaC (lo empuja el BP desde la camara del rig; w = 0 -> la camara de
// cada ojo): los dos ojos ven la MISMA mota con el MISMO alfa (sin rivalidad binocular en el borde del metaball). El
// sprite y su tamano angular siguen con la camara de CADA ojo (CamL). Tamano angular con piso de 0,2 grados (no
// centellea). Los quads con alfa < 0,002 colapsan a tamano 0.
// SEMILLAS invariantes a la V invertida del importador FBX (gotcha 302) y a las UV en fp16: lo asimetrico va en U
// (esquina, enteros), en V solo fases uniformes. La posicion base sale de LocalPosition (fp32). Ver vida_model.encode.
// Modelo de referencia: scripts/vida_model.py (dust_vs). Verificador: scripts/hlsl/Vida_check.py.
// Plan: docs/PLAN-VIDA-VALLE-2026-09-28.md.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DustVS"  OutputType CMOT_Float3
//       additionalOutputs: DustV CMOT_Float4 (-> VertexInterpolator -> DustV de DustPS). La salida principal
//       se llama "return" (gotcha 453). Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = desplazamiento LOCAL (cm) del vertice -> Transform (vector, Local -> World) -> WPO.
//        DustV  = (esquina x, esquina y, alfa, luz) para el pixel shader.
// ENTRADAS (38, en este orden):
//   1  LP              float3  LocalPosition                                       posicion local del vertice (cm): mota + esquina
//   2  Crn             float2  TexCoord 0                                          (esquina k 0..3, 0.5)
//   3  Sa              float2  TexCoord 1                                          (n 0..1023 juego de frecuencias, fase 1)
//   4  Sb              float2  TexCoord 2                                          (bits: 1 solo-rafaga, 2 sentido del remolino; fase 2)
//   5  Sc              float2  TexCoord 3                                          (b brillo/tamano/radio, fase 3)
//   6  CamL            float3  CameraPositionWS -> TransformPosition (World -> Local)  la camara de ESTE ojo, en local
//   7  VidaT           float4  VectorParameter VidaT, pin RGBA                     (Tm, ritmo del meandro, Glob, Live): lo escribe el BP
//   8  VidaG           float4  VectorParameter VidaG, pin RGBA                     (Ox, Oy, dx, dy) trayectoria de la rafaga, local
//   9  VidaS           float4  VectorParameter VidaS, pin RGBA                     (s frente, W ancho, velocidad del frente, Amp)
//  10  VidaE           float4  VectorParameter VidaE, pin RGBA                     (e0, e1, rampa, Hold) envolvente a lo largo del camino; Hold = deriva
//  11  VidaF           float4  VectorParameter VidaF, pin RGBA                     (Lf0, Lf1, dHold/dt, -) largo del frente
//  12  VidaSoul        float4  VectorParameter VidaSoul, pin RGBA                  (centro del metaball local, radio); radio 0 = sin despeje
//  13  VidaC           float4  VectorParameter VidaC, pin RGBA                     (punto ciclopeo local, valido); w 0 = la camara de cada ojo
//  14  DustAlpha       float   ScalarParameter DustAlpha 1                         opacidad de las motas
//  15  DustSizeDeg     float   ScalarParameter DustSizeDeg 0.24                    tamano angular (grados; piso 0,2)
//  16  SizeVar         float   ScalarParameter SizeVar 0.3                         variacion del tamano (+-)
//  17  DistTilt        float   ScalarParameter DistTilt 0.3                        las lejanas mas tenues: (1 m / d)^DistTilt
//  18  MeanderCm       float   ScalarParameter MeanderCm 7                         amplitud del meandro (cm) hasta 3 m
//  19  MeanderFar      float   ScalarParameter MeanderFar 10                       mas lejos la amplitud crece con la distancia, hasta x MeanderFar
//  20  Twinkle         float   ScalarParameter Twinkle 0.35                        titileo lento (0 = ninguno)
//  21  SunAz           float   ScalarParameter SunAz 20                            azimut de la luz que las hace brillar (grados)
//  22  SunEl           float   ScalarParameter SunEl 10                            elevacion de esa luz (grados)
//  23  SunG            float   ScalarParameter SunG 0.55                           dispersion hacia adelante (0 = pareja, 0,9 = un halo angosto)
//  24  SunBase         float   ScalarParameter SunBase 0.5                         brillo de las que no estan contra la luz
//  25  EddyCm          float   ScalarParameter EddyCm 10                           radio del remolino de la rafaga (cm)
//  26  EddyNear        float   ScalarParameter EddyNear 250                        cm: mas cerca, el remolino y la deriva se achican (hasta 0,3)
//  27  Lift            float   ScalarParameter Lift 1.2                            cuanto se encienden al paso del frente
//  28  GustDustAlpha   float   ScalarParameter GustDustAlpha 0.6                   opacidad del polvo que SOLO levanta la rafaga
//  29  DriftCm         float   ScalarParameter DriftCm 40                          cuanto se lleva el viento cada mota (cm, a EddyNear)
//  30  DriftFar        float   ScalarParameter DriftFar 3                          lejos la deriva crece con la distancia, hasta x DriftFar
//  31  NearMin         float   ScalarParameter NearMin 120                         cm a los ojos: invisible debajo (fuera del volumen del aliento)
//  32  NearFull        float   ScalarParameter NearFull 180                        cm a los ojos: plena desde aca
//  33  FarFade0        float   ScalarParameter FarFade0 2600                       cm: se empiezan a apagar
//  34  FarFade1        float   ScalarParameter FarFade1 3600                       cm: apagadas
//  35  SpeedFade0      float   ScalarParameter SpeedFade0 6                        grados/s en la vista: desde aca lo rapido se apaga
//  36  SpeedFade1      float   ScalarParameter SpeedFade1 12                       grados/s: apagado del todo
//  37  SoulMargin0     float   ScalarParameter SoulMargin0 2                       grados alrededor del metaball sin polvo
//  38  SoulMargin1     float   ScalarParameter SoulMargin1 8                       grados: pleno desde aca
// USA ADEMAS: View.GameTime (solo en el editor, Live = 0: el meandro anima en el viewport sin Play). Sin bucles, sin
//       arreglos ni indices dinamicos (regla Adreno, gotcha 399), sin half. Una [branch] uniforme: la rafaga (VidaS.w).
// --------------------------------------------------------------------------------------------------------
float Tt = View.GameTime;
if (!(Tt > -1.0e9 && Tt < 1.0e9)) { Tt = 0.0; }
float kc = floor(Crn.x + 0.5);
float cx = step(0.5, kc) * step(kc, 2.5);
float cy = step(1.5, kc);
float3 P0 = LP - float3(0.0, (2.0 * cx - 1.0) * 0.2, (2.0 * cy - 1.0) * 0.2);
float n = floor(Sa.x + 0.5);
float f = floor(Sb.x + 0.5);
float ph1 = Sa.y;
float ph2 = Sb.y;
float ph3 = Sc.y;
float bi = Sc.x;
float isG = step(0.5, f - 2.0 * floor(f / 2.0));
float sgn = 2.0 * step(0.5, floor(f / 2.0) - 2.0 * floor(f / 4.0)) - 1.0;
float live = step(0.5, VidaT.w);
float Tm = VidaT.x * live + Tt * VidaT.y * (1.0 - live);
float cyc = step(0.5, VidaC.w);
float3 CamC = CamL + (VidaC.xyz - CamL) * cyc;
float r0 = length(P0);
// ---- meandro: tres senos, un numero ENTERO de vueltas por ventana de 1800 s; mas amplio lejos ----
float nq = floor(n / 32.0);
float nr = n - 32.0 * nq;
float k1 = 24.0 + nr;
float k2 = 24.0 + nq;
float m5 = n * 5.0 + nq;
float k3 = 24.0 + (m5 - 32.0 * floor(m5 / 32.0));
float a1 = 6.2831853 * frac(k1 * Tm / 1800.0 + ph1);
float a2 = 6.2831853 * frac(k2 * Tm / 1800.0 + ph2);
float a3 = 6.2831853 * frac(k3 * Tm / 1800.0 + ph3);
float mA = MeanderCm * (0.6 + 0.8 * frac(ph1 * 3.7 + ph2)) * clamp(r0 / 300.0, 1.0, max(MeanderFar, 1.0));
float3 M = mA * float3(sin(a1), sin(a2), 0.6 * sin(a3));
float mw = mA * 0.0034906585 * VidaT.y;
float3 Mv = mw * float3(k1 * cos(a1), k2 * cos(a2), 0.6 * k3 * cos(a3));
// ---- la rafaga: un lazo cerrado + la deriva a favor del viento (rama uniforme: sin rafaga no se calcula) ----
float3 G = float3(0.0, 0.0, 0.0);
float3 Gv = float3(0.0, 0.0, 0.0);
float act = 0.0;
[branch]
if (VidaS.w > 0.0)
{
    float2 dd = VidaG.zw;
    float2 rel = P0.xy - VidaG.xy;
    float xg = dot(rel, dd);
    float eta = abs(rel.x * (-dd.y) + rel.y * dd.x);
    float rp = max(VidaE.z, 1.0);
    float ta = saturate((xg - VidaE.x) / rp);
    float tb = saturate((xg - (VidaE.y - rp)) / rp);
    float Ax = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0) * (1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0));
    float th = saturate((eta - VidaF.x) / max(VidaF.y - VidaF.x, 1.0));
    float hx = 1.0 - th * th * th * (th * (6.0 * th - 15.0) + 10.0);
    float Wd = max(VidaS.y, 1.0);
    float tu = saturate(((VidaS.x - xg) / Wd + 2.0) * 0.25);
    float Pu = tu * tu * tu * (tu * (6.0 * tu - 15.0) + 10.0);
    float bl = 16.0 * tu * tu * (1.0 - tu) * (1.0 - tu);
    float dP = 7.5 * tu * tu * (1.0 - tu) * (1.0 - tu);
    float Ae = VidaS.w * Ax * hx;
    float be = 6.2831853 * (frac(ph3 * 5.3 + ph1) - 0.5) * 0.333;
    float3 e1 = float3(dd.x, dd.y, 0.0);
    float3 e2 = sgn * (cos(be) * float3(0.0, 0.0, 1.0) + sin(be) * float3(-dd.y, dd.x, 0.0));
    float Rr = EddyCm * (0.5 + bi) * clamp(r0 / max(EddyNear, 1.0), 0.3, 1.0);
    float Pc = 1.0 - Pu;
    float lx = 6.235383 * Pu * Pc * (1.0 - 2.0 * Pu);
    float ly = 32.0 * Pu * Pu * Pc * Pc;
    float dlx = 6.235383 * (1.0 - 6.0 * Pu + 6.0 * Pu * Pu);
    float dly = 64.0 * Pu * Pc * (1.0 - 2.0 * Pu);
    float Rd = DriftCm * (0.5 + bi) * clamp(r0 / max(EddyNear, 1.0), 0.3, max(DriftFar, 0.3));
    G = Rr * Ae * (lx * e1 + ly * e2) + Rd * Ae * Pu * VidaE.w * e1;
    Gv = Rr * Ae * dP * VidaS.z / Wd * (dlx * e1 + dly * e2) + Rd * Ae * (dP * VidaS.z / Wd * VidaE.w + Pu * VidaF.z) * e1;
    act = Ae * bl;
}
float3 P = P0 + M + G;
float3 V = Mv + Gv;
// ---- el sprite: la camara de ESTE ojo ----
float3 D = P - CamL;
float dist = max(length(D), 1.0e-3);
// ---- el alfa: el punto ciclopeo (igual en los dos ojos) ----
float3 DC = P - CamC;
float distC = max(length(DC), 1.0e-3);
float3 DnC = DC / distC;
float sza = sin(radians(SunAz));
float cza = cos(radians(SunAz));
float sze = sin(radians(SunEl));
float cze = cos(radians(SunEl));
float3 Ls = float3(cze * cza, cze * sza, sze);
float mu = dot(DnC, Ls);
float g = clamp(SunG, 0.0, 0.95);
float hgd = max(1.0 + g * g - 2.0 * g * mu, 1.0e-4);
float hgn = pow((1.0 - g) * (1.0 - g) / hgd, 1.5);
float lit = SunBase + (1.0 - SunBase) * hgn;
float br = 0.55 + 0.45 * frac(bi * 7.0 + ph2);
float m7 = n * 7.0;
float ktw = 180.0 + (m7 - 271.0 * floor(m7 / 271.0));
float tw = 1.0 - Twinkle * 0.5 * (1.0 + sin(6.2831853 * frac(ktw * Tm / 1800.0 + frac(ph1 + 0.618034 * ph3))));
float dfall = pow(100.0 / max(distC, 30.0), DistTilt);
float nearF = smoothstep(NearMin, NearFull, distC);
float farF = 1.0 - smoothstep(FarFade0, FarFade1, distC);
float3 SD = VidaSoul.xyz - CamC;
float sdl = max(length(SD), 1.0);
float ra = degrees(asin(saturate(VidaSoul.w / sdl)));
float ang = degrees(acos(clamp(dot(DnC, SD / sdl), -1.0, 1.0)));
float soul = 1.0 + (smoothstep(ra + SoulMargin0, ra + SoulMargin1, ang) - 1.0) * step(0.5, VidaSoul.w);
float om = degrees(length(cross(V, DnC)) / distC);
float spf = 1.0 - smoothstep(SpeedFade0, SpeedFade1, om);
float aBase = DustAlpha * br * lit * dfall * tw * (1.0 + Lift * act);
float aGust = GustDustAlpha * br * lit * dfall * act;
float al = (aBase + (aGust - aBase) * isG) * nearF * farF * soul * spf * VidaT.z;
al = min(al, 0.95);
float sdeg = max(DustSizeDeg * (1.0 + SizeVar * (2.0 * frac(bi * 3.1 + ph3) - 1.0)), 0.2);
float hsz = 0.5 * dist * tan(radians(sdeg)) * step(0.002, al);
// ---- sprite hacia la camara de este ojo ----
float3 fw = normalize(CamL - P + float3(1.0e-4, 0.0, 0.0));
float3 rt = normalize(cross(float3(0.0, 0.0, 1.0), fw) + float3(0.0, 1.0e-4, 0.0));
float3 up = cross(fw, rt);
float2 c = float2(cx, cy) * 2.0 - 1.0;
float3 dst = P + (rt * c.x + up * c.y) * hsz;
DustV = float4(c.x, c.y, al, saturate(hgn));
float3 offs = dst - LP;
if (!(dot(offs, offs) < 160000.0)) { offs = float3(0.0, 0.0, 0.0); }
return offs;
