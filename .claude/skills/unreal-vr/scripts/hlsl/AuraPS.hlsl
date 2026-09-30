// AuraPS - M_AlmaAura_SC, PIXEL SHADER -> Emissive Color + Opacity (AlphaComposite = premultiplicado). v1 2026-09-30
// Un punto suave: perfil (1 - r^2)^2 dentro del quad (soporte compacto, sin borde duro), color entre ColA y ColB segun
// la mota. Es DustPS con la paleta del aura (blanco tibio a durazno palido) y un brillo general.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "AuraPS"  OutputType CMOT_Float3
//       additionalOutputs: Alpha CMOT_Float1 (-> Opacity). La salida principal se llama "return" (gotcha 453).
// SALIDA float3 = color LINEAL premultiplicado -> Emissive Color. Alpha -> Opacity.
// ENTRADAS (4, en este orden):
//   1  AuraV           float4  VertexInterpolator, pin PS (su VS = AuraV de AuraVS)  (esquina x, y, alfa, mezcla)
//   2  ColA            float3  VectorParameter ColA, pin RGB                       lineal (1, 0.94, 0.86)
//   3  ColB            float3  VectorParameter ColB, pin RGB                       lineal (1, 0.8, 0.62)
//   4  AuraGlow        float   ScalarParameter AuraGlow 1                          brillo del color (<= 1: en movil no hay "mas blanco que blanco")
// USA ADEMAS: nada. Sin texturas. El material: Unlit, Translucent AlphaComposite, Two Sided, sin niebla de translucidos.
// --------------------------------------------------------------------------------------------------------
float2 c = AuraV.xy;
float m = saturate(1.0 - dot(c, c));
m = m * m;
float a = saturate(m * AuraV.z);
float3 col = lerp(ColA, ColB, saturate(AuraV.w)) * AuraGlow;
Alpha = a;
return col * a;
