// ValleyPS - M_BreathValley_SC, PIXEL SHADER -> Emissive. Unlit mate en espacio LOCAL. Part 0 suelo, 1 cielo.  v2 (revision 2026-09-28)
// VI1 = ValleyGradVS (dh/dx, dh/dy, h, hf). LPi = posicion local interpolada. CamL = CameraVector en local.
// Dist = distancia REAL a la camara. LightDir/GlowDir/MoonDir/MoonCosR llegan ya calculados (preshader).
// Sin tonemapper en el APK: lo que se escribe es lo que se ve (el hardware solo codifica sRGB).
// v2: brillo rasante con LOBULO DE TOPE PLANO exp(-(N.V/SheenW)^4) (sin ganancia en el rasante: era la linea del
//     piso) que se apaga con la niebla; niebla por distancia + niebla de ALTURA integrada a lo largo del rayo.
// Revision: el gradiente de VI1 trae ademas el SOMBREADO del oleaje (el llano ondula en la luz); ramas con [branch]
//     (no aplanar: el piso cercano no paga niebla ni cielo); la sombra falsa solo a menos de 12 anchos de penumbra.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "ValleyPS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = color LINEAL final (con dither) -> Emissive Color. Unlit: no hay otra salida.
//       Part 0: suelo (luz wrap, pendiente, cimas, sheen, sombra del metaball, niebla, dither).
//       Part 1: cielo (degradado, resplandor, luna; sale temprano). PerfMode 2/3: color plano + dither, y sale
//       ANTES de toda cuenta (el banco mide el pixel entero). El suelo a menos de FogStart no calcula ni la niebla
//       ni el cielo, y la sombra del metaball se calcula solo cerca de el (afuera O < 9e-4).
// ENTRADAS (44, en este orden):
//   1  VI1             float4  VertexInterpolator_0, pin PS (su VS = ValleyGradVS)       (dh/dx, dh/dy, h, hf) del suelo; el gradiente incluye el sombreado del oleaje
//   2  LPi             float3  VertexInterpolator_1, pin PS (su VS = LocalPosition XYZ)  posicion local interpolada (cm, sin WPO)
//   3  CamL            float3  CameraVector -> Transform (vector, World -> Local)        del pixel hacia la camara, en local
//   4  Dist            float   Distance(AbsoluteWorldPosition, CameraPositionWS)         distancia REAL pixel-camara (cm)
//   5  Part            float   ScalarParameter Part                                      0 suelo, 1 cielo
//   6  PerfMode        float   ScalarParameter PerfMode                                  banco: 2 y 3 = pixeles baratos
//   7  LightDir        float3  preshader D(LightAz, LightEl)                             unitario; (0.851651, 0.309976, 0.422618)
//   8  Wrap            float   ScalarParameter Wrap                                      0.3
//   9  ShadeFloor      float   ScalarParameter ShadeFloor                                0
//  10  SlopeDark       float   ScalarParameter SlopeDark                                 1.2
//  11  ColLit          float3  VectorParameter ColLit, pin RGB                           lineal (0.434, 0.527, 0.855)
//  12  ColShadow       float3  VectorParameter ColShadow, pin RGB                        lineal (0.061, 0.117, 0.352)
//  13  ColSheen        float3  VectorParameter ColSheen, pin RGB                         lineal (0.855, 0.761, 0.913)
//  14  Sheen           float   ScalarParameter Sheen                                     0.28
//  15  SheenW          float   ScalarParameter SheenW                                    0.3 (ancho del lobulo en N.V; reemplaza a SheenPow)
//  16  SheenBack       float   ScalarParameter SheenBack                                 0.35
//  17  CrestLight      float   ScalarParameter CrestLight                                0.2
//  18  ShadowCenter    float3  VectorParameter ShadowCenter, pin RGB                     centro del metaball en local (cm); (380, 0, 125); lo escribe el BP
//  19  ShadowRadius    float   ScalarParameter ShadowRadius                              85 cm; lo escribe el BP
//  20  ShadowStrength  float   preshader Mul(ShadowStrength, LiveShadowStrength)           1.5; lo escribe el BP (0 = sin sombra) x capa viva (densa al inhalar)
//  21  ShadowSoft      float   preshader Mul(ShadowSoft, LiveShadowSoft)                   0.8 x capa viva (se abre al exhalar)
//  22  ShadowTint      float3  preshader Mix(ShadowTint, ShadowWarm, LiveShadowWarm)       lineal (0.305, 0.352, 0.68); tibio al exhalar
//  23  ShadowMax       float   ScalarParameter ShadowMax                                 0.8
//  24  SkyZenith       float3  VectorParameter SkyZenith, pin RGB                        lineal (0.216, 0.328, 0.597)
//  25  SkyHorizon      float3  preshader Tint(SkyHorizon, BreathTint, LiveWarm)            lineal (0.597, 0.624, 0.839); tambien color de la niebla; tibio al exhalar
//  26  SkyGlow         float3  VectorParameter SkyGlow, pin RGB                          lineal (0.831, 0.68, 0.855)
//  27  SkyGradTop      float   ScalarParameter SkyGradTop                                0.7
//  28  GlowDir         float3  preshader D(GlowAz, GlowEl)                               unitario; (0.939120, 0.341812, 0.034899)
//  29  GlowPow         float   preshader Mul(GlowPow, LiveGlowPow)                         2 x capa viva
//  30  GlowHeight      float   ScalarParameter GlowHeight                                0.45
//  31  GlowAmt         float   preshader Mul(GlowAmt, LiveGlowAmt)                         0.8 x capa viva
//  32  MoonDir         float3  preshader D(MoonAz, MoonEl)                               unitario; (0.760334, -0.637996, 0.121869)
//  33  MoonCosR        float   preshader Cosine(MoonRadius), Period 360                  0.987688
//  34  MoonEdge        float   ScalarParameter MoonEdge                                  0.03
//  35  MoonColor       float3  VectorParameter MoonColor, pin RGB                        lineal (0.73, 0.644, 0.839)
//  36  MoonOpacity     float   ScalarParameter MoonOpacity                               0.55
//  37  MoonFill        float   ScalarParameter MoonFill                                  0.2
//  38  MoonRim         float   ScalarParameter MoonRim                                   1
//  39  FogStart        float   ScalarParameter FogStart                                  1500 cm
//  40  FogDist         float   preshader Mul(FogDist, LiveFogDist)                         45000 cm (niebla por distancia) x capa viva
//  41  FogMax          float   ScalarParameter FogMax                                    0.9
//  42  HFogDist        float   preshader Mul(HFogDist, LiveHFogDist)                       60000 cm (niebla de altura, a z = 0) x capa viva
//  43  HFogFall        float   preshader Mul(HFogFall, LiveHFogFall)                       1500 cm (la niebla de altura cae a 1/e cada esto) x capa viva
//  44  DitherAmt       float   ScalarParameter DitherAmt                                 1.5 (LSB; 1 = +-0,5/255 en lineal)
// USA ADEMAS: Parameters.SvPosition (hash del dither, igual que HeartScapePS). Sin texturas ni bucles.
// REGLAS: material en MFPM_Full_MaterialExpressionOnly (en fp16 se rompen el borde de la luna y el hash del dither).
//         Los colores y ShadowCenter entran por el pin RGB (float3) del VectorParameter (gotcha 453).
// CONTROL: docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 12. Cableado completo: Valley_CABLEADO.md.
// CAPA VIVA (2026-09-28, docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md): las 9 entradas "preshader Mul/Mix/Tint" llegan
//       multiplicadas (Mul: A*B), mezcladas (Mix: A + (B - A)*T) o tenidas (Tint: A * (1 + (B - 1)*T), un tinte
//       RELATIVO: sigue a SkyHorizon aunque se cambie en las perillas del BP) por los Live* que empuja
//       BP_BreathValley_SC.PushLive desde la respiracion. Son cuentas de UNIFORMES (preshader, en la CPU): el codigo no
//       cambia y con los Live* en su neutro (Mul 1, Mix 0, Tint 0) cada entrada vale EXACTO lo de la v2.
//       ShadowRadius y GlowHeight NO respiran (rev. 2: el radio iba a contrafase de StepShadow y la altura del
//       resplandor movia la banda del cielo).
// --------------------------------------------------------------------------------------------------------
float pm = floor(PerfMode + 0.5);
// dither estatico contra el banding (mismo hash que HeartScapePS)
float3 p3 = frac(float3(Parameters.SvPosition.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
float dith = DitherAmt * (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0;
// banco: PerfMode 2/3 = pixeles baratos DE VERDAD, antes de cualquier cuenta (asi m0 - m2 mide el pixel entero)
if (pm >= 2.0 && Part > 0.5) { return SkyHorizon + dith; }
if (pm >= 2.0) { return ColLit + dith; }
float3 V = normalize(CamL);
float3 dv = -V;
// niebla del suelo: por distancia + de altura exponencial integrada a lo largo del rayo (densidad
// 1/FogDist + exp(-z/HFogFall)/HFogDist). z0 = camara y z1 = pixel, en local. Rama dinamica: el piso a menos
// de FogStart (la zona quieta, casi medio campo visual) no la paga.
float fog = 0.0;
[branch]
if (Part < 0.5 && Dist > FogStart)
{
  float Hf = max(HFogFall, 1.0);
  float z1 = max(VI1.z, 0.0);
  float z0 = max(VI1.z + V.z * Dist, 0.0);
  float e0 = exp(-z0 / Hf);
  float dz = z1 - z0;
  float Fh = e0;
  if (abs(dz) > 1.0)
  {
    Fh = Hf * (e0 - exp(-z1 / Hf)) / dz;
  }
  fog = FogMax * (1.0 - exp(-(Dist - FogStart) * (1.0 / max(FogDist, 1.0) + Fh / max(HFogDist, 1.0))));
}
// cielo en la direccion de la mirada: el color del cielo y el color al que tiende la niebla del suelo.
// Rama dinamica: el suelo SIN niebla no lo paga; lerp(col, sky, 0) = col exacto.
float3 sky = SkyHorizon;
[branch]
if (Part > 0.5 || fog > 0.0)
{
  sky = lerp(SkyHorizon, SkyZenith, smoothstep(0.0, max(SkyGradTop, 0.01), dv.z));
  float2 hz = dv.xy * rsqrt(max(dot(dv.xy, dv.xy), 1e-8));
  float2 gh = GlowDir.xy * rsqrt(max(dot(GlowDir.xy, GlowDir.xy), 1e-8));
  float gaz = pow(max(dot(hz, gh), 1e-6), max(GlowPow, 0.1));
  float gel = 1.0 - smoothstep(0.0, max(GlowHeight, 0.001), abs(dv.z - GlowDir.z));
  sky = lerp(sky, SkyGlow, saturate(GlowAmt * gaz * gel));
}
if (Part > 0.5)
{
  // luna: disco suave con el borde encendido del lado del resplandor
  float cosA = dot(dv, MoonDir);
  float rho = sqrt(max(1.0 - cosA, 0.0) / max(1.0 - MoonCosR, 1e-6));
  float me = max(MoonEdge, 0.001);
  if (rho < 1.0 + me)
  {
    float disc = 1.0 - smoothstep(1.0 - me, 1.0 + me, rho);
    float3 o = dv - MoonDir * cosA;
    float3 gm = GlowDir - MoonDir * dot(GlowDir, MoonDir);
    float side = 0.5 + 0.5 * dot(o, gm) * rsqrt(max(dot(o, o), 1e-10)) * rsqrt(max(dot(gm, gm), 1e-10));
    float rim = smoothstep(0.6, 1.0, rho) * side * side;
    sky = lerp(sky, MoonColor, saturate(MoonOpacity * disc * (MoonFill + MoonRim * rim)));
  }
  return sky + dith;
}
// ---- suelo ----
float3 N = normalize(float3(-VI1.x, -VI1.y, 1.0));
float wrap = saturate((dot(N, LightDir) + Wrap) / (1.0 + Wrap));
float k = lerp(ShadeFloor, 1.0, wrap) * saturate(1.0 - SlopeDark * (1.0 - N.z));
float3 col = lerp(ColShadow, ColLit, k);
col = lerp(col, ColLit, CrestLight * VI1.w * VI1.w);
// brillo rasante: lobulo de tope plano (pendiente 0 en N.V = 0); se apaga con la niebla (sin franja en el horizonte)
float xs = saturate(dot(N, V)) / max(SheenW, 0.05);
float x2 = xs * xs;
float fres = exp(-x2 * x2);
float fwd = saturate(0.5 + 0.5 * dot(dv, LightDir));
col = lerp(col, ColSheen, saturate(Sheen * fres * lerp(SheenBack, 1.0, fwd) * (1.0 - fog)));
// sombra falsa del metaball: factor de forma de una esfera de radio Rs a altura Hs sobre el suelo. Rama: solo a
// menos de 12 anchos de penumbra (q^-3/2 < 6e-4 afuera: O < 9e-4, menos de 0,1 nivel); el resto del suelo no la paga
float Hs = max(ShadowCenter.z - VI1.z, 1.0);
float ws = max(ShadowSoft * Hs, 1.0);
float2 ds = LPi.xy - ShadowCenter.xy;
float d2 = dot(ds, ds);
[branch]
if (d2 < 144.0 * ws * ws)
{
  float Rs = max(ShadowRadius, 1.0);
  float peak = ShadowStrength * Rs * Rs / (Rs * Rs + Hs * Hs);
  float qs = 1.0 + d2 / (ws * ws);
  float rq = rsqrt(qs);
  float O = min(saturate(peak * rq * rq * rq), ShadowMax);
  col *= 1.0 - O * (1.0 - ShadowTint);
}
// niebla hacia el color del cielo en esa direccion
return lerp(col, sky, fog) + dith;
