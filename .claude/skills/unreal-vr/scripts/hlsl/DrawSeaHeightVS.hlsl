// DrawSeaHeightVS - M_DrawSea_SC, VERTEX SHADER -> Transform Local->World -> WPO. Solo la ALTURA. Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// Unreal compila el WPO y cada VertexInterpolator en funciones separadas: cada salida vuelve a
// llamar a su Custom (leccion del latido). Por eso este nodo calcula SOLO h.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawSeaHeightVS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = (0, 0, h) en local (cm). Part 1 o PerfMode 1/3 -> 0.
// ENTRADAS (28, en este orden):
//   1  LP         float3  LocalPosition, pin XYZ  |  posicion del vertice en el espacio del actor (cm); el disco es plano
//   2  Part       float   ScalarParameter Part  |  0 mar, 1 cielo (lo pone el Construction Script)
//   3  PerfMode   float   ScalarParameter PerfMode  |  banco: 1 y 3 = vertices baratos (sin oleaje)
//   4  W0         float4  VectorParameter W0  |  oleaje 0: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//   5  W1         float4  VectorParameter W1  |  oleaje 1: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//   6  W2         float4  VectorParameter W2  |  oleaje 2: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//   7  W3         float4  VectorParameter W3  |  oleaje 3: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//   8  W4         float4  VectorParameter W4  |  oleaje 4: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//   9  W5         float4  VectorParameter W5  |  oleaje 5: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP
//  10  V0         float4  VectorParameter V0  |  oleaje 0: (A, fase, velocidad del grupo, fase del grupo)
//  11  V1         float4  VectorParameter V1  |  oleaje 1: (A, fase, velocidad del grupo, fase del grupo)
//  12  V2         float4  VectorParameter V2  |  oleaje 2: (A, fase, velocidad del grupo, fase del grupo)
//  13  V3         float4  VectorParameter V3  |  oleaje 3: (A, fase, velocidad del grupo, fase del grupo)
//  14  V4         float4  VectorParameter V4  |  oleaje 4: (A, fase, velocidad del grupo, fase del grupo)
//  15  V5         float4  VectorParameter V5  |  oleaje 5: (A, fase, velocidad del grupo, fase del grupo)
//  16  E0         float4  VectorParameter E0  |  oleaje 0: (dir del grupo x, y, LOD desde, LOD hasta)
//  17  E1         float4  VectorParameter E1  |  oleaje 1: (dir del grupo x, y, LOD desde, LOD hasta)
//  18  E2         float4  VectorParameter E2  |  oleaje 2: (dir del grupo x, y, LOD desde, LOD hasta)
//  19  E3         float4  VectorParameter E3  |  oleaje 3: (dir del grupo x, y, LOD desde, LOD hasta)
//  20  E4         float4  VectorParameter E4  |  oleaje 4: (dir del grupo x, y, LOD desde, LOD hasta)
//  21  E5         float4  VectorParameter E5  |  oleaje 5: (dir del grupo x, y, LOD desde, LOD hasta)
//  22  GroupAmt   float   ScalarParameter GroupAmt  |  0.75 (fuerza de los grupos de olas)
//  23  GroupLen   float   ScalarParameter GroupLen  |  9000 cm (largo de un grupo)
//  24  Warp       float   ScalarParameter Warp  |  120 cm (serpenteo de las crestas)
//  25  WarpScale  float   ScalarParameter WarpScale  |  4500 cm
//  26  Advance    float   ScalarParameter Advance  |  5 cm/s (el campo se desliza hacia el usuario, -X local)
//  27  CalmR      float   ScalarParameter CalmR  |  600 cm (radio de calma bajo el usuario)
//  28  CalmMin    float   ScalarParameter CalmMin  |  0.7 (amplitud en el centro)
// TIEMPO: View.GameTime adentro (fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
// --------------------------------------------------------------------------------------------------------
float T = View.GameTime;
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float3(0.0, 0.0, 0.0); }
float2 P = LP.xy;
const float TAU = 6.2831853;
float kw = TAU / WarpScale;
float ax = P.y * kw + T * 0.071;
float ay = P.x * kw * 1.31 + T * 0.053 + 1.7;
float2 qa = P + Warp * float2(sin(ax), sin(ay)) + float2(Advance * T, 0.0);
float r = max(length(P), 1.0);
float kg = TAU / GroupLen;
float S = 0.0;
[branch] if (r < E0.w)
{
  float x0 = saturate((r - E0.z) / (E0.w - E0.z));
  float lod0 = 1.0 - x0 * x0 * (3.0 - 2.0 * x0);
  float m0 = 1.0 + GroupAmt * sin(kg * (dot(qa, E0.xy) - V0.z * T) + V0.w);
  S += V0.x * lod0 * m0 * sin(W0.z * dot(W0.xy, qa) - W0.w * T + V0.y);
}
[branch] if (r < E1.w)
{
  float x1 = saturate((r - E1.z) / (E1.w - E1.z));
  float lod1 = 1.0 - x1 * x1 * (3.0 - 2.0 * x1);
  float m1 = 1.0 + GroupAmt * sin(kg * (dot(qa, E1.xy) - V1.z * T) + V1.w);
  S += V1.x * lod1 * m1 * sin(W1.z * dot(W1.xy, qa) - W1.w * T + V1.y);
}
[branch] if (r < E2.w)
{
  float x2 = saturate((r - E2.z) / (E2.w - E2.z));
  float lod2 = 1.0 - x2 * x2 * (3.0 - 2.0 * x2);
  float m2 = 1.0 + GroupAmt * sin(kg * (dot(qa, E2.xy) - V2.z * T) + V2.w);
  S += V2.x * lod2 * m2 * sin(W2.z * dot(W2.xy, qa) - W2.w * T + V2.y);
}
[branch] if (r < E3.w)
{
  float x3 = saturate((r - E3.z) / (E3.w - E3.z));
  float lod3 = 1.0 - x3 * x3 * (3.0 - 2.0 * x3);
  float m3 = 1.0 + GroupAmt * sin(kg * (dot(qa, E3.xy) - V3.z * T) + V3.w);
  S += V3.x * lod3 * m3 * sin(W3.z * dot(W3.xy, qa) - W3.w * T + V3.y);
}
[branch] if (r < E4.w)
{
  float x4 = saturate((r - E4.z) / (E4.w - E4.z));
  float lod4 = 1.0 - x4 * x4 * (3.0 - 2.0 * x4);
  float m4 = 1.0 + GroupAmt * sin(kg * (dot(qa, E4.xy) - V4.z * T) + V4.w);
  S += V4.x * lod4 * m4 * sin(W4.z * dot(W4.xy, qa) - W4.w * T + V4.y);
}
[branch] if (r < E5.w)
{
  float x5 = saturate((r - E5.z) / (E5.w - E5.z));
  float lod5 = 1.0 - x5 * x5 * (3.0 - 2.0 * x5);
  float m5 = 1.0 + GroupAmt * sin(kg * (dot(qa, E5.xy) - V5.z * T) + V5.w);
  S += V5.x * lod5 * m5 * sin(W5.z * dot(W5.xy, qa) - W5.w * T + V5.y);
}
float xc = saturate(r / CalmR);
return float3(0.0, 0.0, lerp(CalmMin, 1.0, xc * xc * (3.0 - 2.0 * xc)) * S);
