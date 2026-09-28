// DrawDustPS - M_DrawDust_SC, PIXEL SHADER -> Emissive (translucido ADITIVO). Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawDustPS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = color lineal de la mota.
// ENTRADAS (5, en este orden):
//   1  A          float   VertexInterpolator_0 (pin PS) <- DrawDustAlphaVS  |  alpha de la mota
//   2  UV0        float2  TexCoord 0  |  esquina del quad (0..1)
//   3  DustColor  float3  VectorParameter DustColor  |  lineal
//   4  DustAmt    float   ScalarParameter DustAmt  |  0.45
//   5  DustBG     float3  VectorParameter DustBG  |  fondo tipico detras de las motas (lineal); gotcha 485
// TIEMPO: View.GameTime adentro (fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
// --------------------------------------------------------------------------------------------------------
float d = length(UV0 * 2.0 - 1.0);
float3 c = DustColor * (DustAmt * A * (1.0 - smoothstep(0.35, 1.0, d)));
float3 bg = max(DustBG, 0.0);
float3 eb = lerp(1.055 * pow(max(bg, 1e-7), 1.0 / 2.4) - 0.055, bg * 12.92, step(bg, 0.0031308));
float3 ec = lerp(1.055 * pow(max(c, 1e-7), 1.0 / 2.4) - 0.055, c * 12.92, step(c, 0.0031308));
float3 s = saturate(eb + ec);
float3 lin = lerp(pow(max((s + 0.055) / 1.055, 1e-7), 2.4), s / 12.92, step(s, 0.04045));
return max(lin - bg, 0.0);
