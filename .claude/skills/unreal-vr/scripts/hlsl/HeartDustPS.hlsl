// HeartDustPS - M_HeartDust_SC, PIXEL SHADER -> Emissive Color + Opacity (AlphaComposite = premultiplicado). v1 2026-10-01
// Un punto suave: perfil (1 - r^2)^2 dentro del quad (soporte compacto, sin borde duro). Color por tipo: polvo o
// particula (paleta blanca-rojiza del latido). Es AuraPS con otra paleta.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "HeartDustPS"  OutputType CMOT_Float3
//       additionalOutputs: Alpha CMOT_Float1 (-> Opacity). La salida principal se llama "return" (gotcha 453).
// SALIDA float3 = color LINEAL premultiplicado -> Emissive Color. Alpha -> Opacity.
// ENTRADAS (4, en este orden):
//   1  DustV           float4  VertexInterpolator, pin PS (su VS = DustV de HeartDustVS)  (esquina x, y, alfa, tipo)
//   2  DustColor       float3  VectorParameter DustColor, pin RGB                  lineal (1, 0.88, 0.84)
//   3  SparkColor      float3  VectorParameter SparkColor, pin RGB                 lineal (1, 0.72, 0.66)
//   4  Glow            float   ScalarParameter Glow 1                              brillo del color (<= 1: en movil no hay "mas blanco que blanco")
// USA ADEMAS: nada. Sin texturas. El material: Unlit, Translucent AlphaComposite, Two Sided, sin niebla de translucidos.
// --------------------------------------------------------------------------------------------------------
float2 c = DustV.xy;
float m = saturate(1.0 - dot(c, c));
m = m * m;
float a = saturate(m * DustV.z);
float3 col = lerp(DustColor, SparkColor, saturate(DustV.w)) * Glow;
Alpha = a;
return col * a;
