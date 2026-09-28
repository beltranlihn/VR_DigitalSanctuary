// BreathAirPS - M_BreathAir_SC, PIXEL SHADER -> Emissive Color + Opacity (AlphaComposite = premultiplicado). v1 2026-09-28
// Un punto suave: perfil (1 - r^2)^2 dentro del quad (soporte compacto, sin borde duro). El color es frio al inhalar
// (InColor, casi el tono del aire del valle) y tibio al exhalar (OutColor, el mismo tinte que toma la bruma).
// Modelo de referencia: scripts/breath_air_model.py (ps). Verificador: scripts/hlsl/BreathAir_check.py.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "BreathAirPS"  OutputType CMOT_Float3
//       additionalOutputs: Alpha CMOT_Float1 (-> Opacity). La salida principal se llama "return" (gotcha 453).
// SALIDA float3 = color LINEAL premultiplicado -> Emissive Color. Alpha -> Opacity.
// ENTRADAS (3, en este orden):
//   1  AirV            float4  VertexInterpolator, pin PS (su VS = AirV de BreathAirVS)  (esquina x, y, alfa, corriente)
//   2  InColor         float3  VectorParameter InColor, pin RGB                    lineal (0.8, 0.85, 1)
//   3  OutColor        float3  VectorParameter OutColor, pin RGB                   lineal (1, 0.84, 0.8)
// USA ADEMAS: nada. Sin texturas. El material: Unlit, Translucent AlphaComposite, Two Sided, sin niebla de
//       translucidos, TranslucencySortPriority 20 en el componente (despues del pacer 0 y del metaball 10).
// --------------------------------------------------------------------------------------------------------
float2 c = AirV.xy;
float m = saturate(1.0 - dot(c, c));
m = m * m;
float a = saturate(m * AirV.z);
float3 col = lerp(InColor, OutColor, saturate(AirV.w));
Alpha = a;
return col * a;
