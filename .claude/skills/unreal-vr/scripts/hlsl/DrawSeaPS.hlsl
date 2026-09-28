// DrawSeaPS - M_DrawSea_SC, PIXEL SHADER -> Emissive. Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawSeaPS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = color lineal (mate), con dither.
// ENTRADAS (21, en este orden):
//   1  G             float4  VertexInterpolator_0 (pin PS) <- DrawSeaGradVS  |  (h, dh/dx, dh/dy, 0)
//   2  Vv            float3  WorldPosition - CameraPositionWS (nodos, LWC)  |  de la camara al punto (cm); distancia REAL para la niebla
//   3  Part          float   ScalarParameter Part  |  0 mar, 1 cielo
//   4  PerfMode      float   ScalarParameter PerfMode  |  banco: 2 y 3 = pixeles baratos (color plano)
//   5  DeepColor     float3  VectorParameter DeepColor  |  cara en sombra (lineal)
//   6  SurfColor     float3  VectorParameter SurfColor  |  cara iluminada (lineal)
//   7  CrestColor    float3  VectorParameter CrestColor  |  tinte de las crestas (lineal)
//   8  CrestAmt      float   ScalarParameter CrestAmt  |  1
//   9  SwellAmp      float   ScalarParameter SwellAmp  |  22 cm (normaliza el tinte de cresta)
//  10  LightAz       float   ScalarParameter LightAz  |  40 grados (0 = +X local)
//  11  LightEl       float   ScalarParameter LightEl  |  22 grados
//  12  WrapPow       float   ScalarParameter WrapPow  |  1.6 (dureza de la luz mate)
//  13  ZenithColor   float3  VectorParameter ZenithColor  |  cielo arriba (lineal)
//  14  HorizonColor  float3  VectorParameter HorizonColor  |  cielo en el horizonte = color de la niebla (lineal)
//  15  SkyPow        float   ScalarParameter SkyPow  |  0.45
//  16  GlowColor     float3  VectorParameter GlowColor  |  resplandor del cielo (lineal)
//  17  GlowAmt       float   ScalarParameter GlowAmt  |  0.012
//  18  GlowPow       float   ScalarParameter GlowPow  |  30
//  19  FogStart      float   ScalarParameter FogStart  |  500 cm
//  20  FogDensity    float   ScalarParameter FogDensity  |  0.00017 /cm
//  21  Dither        float   ScalarParameter Dither  |  1 (dither estatico contra el banding, el del latido)
// TIEMPO: View.GameTime adentro (fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
// --------------------------------------------------------------------------------------------------------
float pm = floor(PerfMode + 0.5);
// dither estatico contra el banding: el MISMO de HeartScapePS (aprobado en visor)
float3 p3 = frac(float3(Parameters.SvPosition.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
float dith = (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0 * Dither;
if (pm >= 2.0) { return SurfColor + dith; }
float az = LightAz * 0.017453292519943295;
float el = LightEl * 0.017453292519943295;
float3 L = float3(cos(el) * cos(az), cos(el) * sin(az), sin(el));
float dist = max(length(Vv), 1.0);
float3 V = Vv / dist;
float3 sdir = V;
if (Part < 0.5) { sdir = normalize(float3(V.xy, 0.015)); }
float3 sky = lerp(HorizonColor, ZenithColor, pow(saturate(sdir.z), SkyPow)) + GlowColor * GlowAmt * pow(saturate(dot(sdir, L)), GlowPow);
if (Part > 0.5) { return sky + dith; }
// MATE: solo difusa envolvente sobre la forma de la ola. Sin reflejo, sin especular.
float3 N = normalize(float3(-G.y, -G.z, 1.0));
float diff = pow(saturate(dot(N, L) * 0.5 + 0.5), WrapPow);
float3 col = lerp(DeepColor, SurfColor, diff);
float crest = saturate(G.x / (SwellAmp * 2.0) + 0.5);
col += CrestColor * CrestAmt * crest * crest;
float fog = 1.0 - exp(-max(dist - FogStart, 0.0) * FogDensity);
return lerp(col, sky, fog) + dith;
