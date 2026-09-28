// DrawSeaGradVS - M_DrawSea_SC, VERTEX SHADER -> VertexInterpolator_0 -> G del PS. Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// Corte por oleaje: si el vertice esta mas alla de E.w, ese oleaje ya vale 0 y el bloque se salta
// (leccion del latido: asi llego a 72 fps).
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawSeaGradVS"  OutputType CMOT_Float4
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float4 = (h, dh/dx, dh/dy, 0), local. Gradiente EXACTO (regla de la cadena del warp). Part 1 o PerfMode 1/3 -> 0.
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
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float4(0.0, 0.0, 0.0, 0.0); }
float2 P = LP.xy;
const float TAU = 6.2831853;
float kw = TAU / WarpScale;
float ax = P.y * kw + T * 0.071;
float ay = P.x * kw * 1.31 + T * 0.053 + 1.7;
float dwx_dy = Warp * kw * cos(ax);
float dwy_dx = Warp * kw * 1.31 * cos(ay);
float2 qa = P + Warp * float2(sin(ax), sin(ay)) + float2(Advance * T, 0.0);
float r = max(length(P), 1.0);
float kg = TAU / GroupLen;
float S = 0.0;
float2 gq = float2(0.0, 0.0);
float gl = 0.0;
[branch] if (r < E0.w)
{
  float se0, ce0;
  sincos(kg * (dot(qa, E0.xy) - V0.z * T) + V0.w, se0, ce0);
  float m0 = 1.0 + GroupAmt * se0;
  float2 gm0 = GroupAmt * ce0 * kg * E0.xy;
  float x0 = saturate((r - E0.z) / (E0.w - E0.z));
  float lod0 = 1.0 - x0 * x0 * (3.0 - 2.0 * x0);
  float dlod0 = -6.0 * x0 * (1.0 - x0) / (E0.w - E0.z);
  float s0, c0;
  sincos(W0.z * dot(W0.xy, qa) - W0.w * T + V0.y, s0, c0);
  S += V0.x * lod0 * m0 * s0;
  gq += V0.x * lod0 * (m0 * W0.z * c0 * W0.xy + s0 * gm0);
  gl += V0.x * dlod0 * m0 * s0;
}
[branch] if (r < E1.w)
{
  float se1, ce1;
  sincos(kg * (dot(qa, E1.xy) - V1.z * T) + V1.w, se1, ce1);
  float m1 = 1.0 + GroupAmt * se1;
  float2 gm1 = GroupAmt * ce1 * kg * E1.xy;
  float x1 = saturate((r - E1.z) / (E1.w - E1.z));
  float lod1 = 1.0 - x1 * x1 * (3.0 - 2.0 * x1);
  float dlod1 = -6.0 * x1 * (1.0 - x1) / (E1.w - E1.z);
  float s1, c1;
  sincos(W1.z * dot(W1.xy, qa) - W1.w * T + V1.y, s1, c1);
  S += V1.x * lod1 * m1 * s1;
  gq += V1.x * lod1 * (m1 * W1.z * c1 * W1.xy + s1 * gm1);
  gl += V1.x * dlod1 * m1 * s1;
}
[branch] if (r < E2.w)
{
  float se2, ce2;
  sincos(kg * (dot(qa, E2.xy) - V2.z * T) + V2.w, se2, ce2);
  float m2 = 1.0 + GroupAmt * se2;
  float2 gm2 = GroupAmt * ce2 * kg * E2.xy;
  float x2 = saturate((r - E2.z) / (E2.w - E2.z));
  float lod2 = 1.0 - x2 * x2 * (3.0 - 2.0 * x2);
  float dlod2 = -6.0 * x2 * (1.0 - x2) / (E2.w - E2.z);
  float s2, c2;
  sincos(W2.z * dot(W2.xy, qa) - W2.w * T + V2.y, s2, c2);
  S += V2.x * lod2 * m2 * s2;
  gq += V2.x * lod2 * (m2 * W2.z * c2 * W2.xy + s2 * gm2);
  gl += V2.x * dlod2 * m2 * s2;
}
[branch] if (r < E3.w)
{
  float se3, ce3;
  sincos(kg * (dot(qa, E3.xy) - V3.z * T) + V3.w, se3, ce3);
  float m3 = 1.0 + GroupAmt * se3;
  float2 gm3 = GroupAmt * ce3 * kg * E3.xy;
  float x3 = saturate((r - E3.z) / (E3.w - E3.z));
  float lod3 = 1.0 - x3 * x3 * (3.0 - 2.0 * x3);
  float dlod3 = -6.0 * x3 * (1.0 - x3) / (E3.w - E3.z);
  float s3, c3;
  sincos(W3.z * dot(W3.xy, qa) - W3.w * T + V3.y, s3, c3);
  S += V3.x * lod3 * m3 * s3;
  gq += V3.x * lod3 * (m3 * W3.z * c3 * W3.xy + s3 * gm3);
  gl += V3.x * dlod3 * m3 * s3;
}
[branch] if (r < E4.w)
{
  float se4, ce4;
  sincos(kg * (dot(qa, E4.xy) - V4.z * T) + V4.w, se4, ce4);
  float m4 = 1.0 + GroupAmt * se4;
  float2 gm4 = GroupAmt * ce4 * kg * E4.xy;
  float x4 = saturate((r - E4.z) / (E4.w - E4.z));
  float lod4 = 1.0 - x4 * x4 * (3.0 - 2.0 * x4);
  float dlod4 = -6.0 * x4 * (1.0 - x4) / (E4.w - E4.z);
  float s4, c4;
  sincos(W4.z * dot(W4.xy, qa) - W4.w * T + V4.y, s4, c4);
  S += V4.x * lod4 * m4 * s4;
  gq += V4.x * lod4 * (m4 * W4.z * c4 * W4.xy + s4 * gm4);
  gl += V4.x * dlod4 * m4 * s4;
}
[branch] if (r < E5.w)
{
  float se5, ce5;
  sincos(kg * (dot(qa, E5.xy) - V5.z * T) + V5.w, se5, ce5);
  float m5 = 1.0 + GroupAmt * se5;
  float2 gm5 = GroupAmt * ce5 * kg * E5.xy;
  float x5 = saturate((r - E5.z) / (E5.w - E5.z));
  float lod5 = 1.0 - x5 * x5 * (3.0 - 2.0 * x5);
  float dlod5 = -6.0 * x5 * (1.0 - x5) / (E5.w - E5.z);
  float s5, c5;
  sincos(W5.z * dot(W5.xy, qa) - W5.w * T + V5.y, s5, c5);
  S += V5.x * lod5 * m5 * s5;
  gq += V5.x * lod5 * (m5 * W5.z * c5 * W5.xy + s5 * gm5);
  gl += V5.x * dlod5 * m5 * s5;
}
// regla de la cadena del warp: grad_p = J^T grad_q
float2 gS = float2(gq.x + dwy_dx * gq.y, dwx_dy * gq.x + gq.y) + gl * P / r;
float xc = saturate(r / CalmR);
float fade = lerp(CalmMin, 1.0, xc * xc * (3.0 - 2.0 * xc));
float dfade = (1.0 - CalmMin) * 6.0 * xc * (1.0 - xc) / CalmR;
float2 g = fade * gS + S * dfade * P / r;
return float4(fade * S, g.x, g.y, 0.0);
