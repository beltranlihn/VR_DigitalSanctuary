// DustPS - M_ValleyDust_SC, PIXEL SHADER -> Emissive Color + Opacity (AlphaComposite = premultiplicado). v2 2026-09-28
// Un punto suave: perfil (1 - r^2)^2 dentro del quad (soporte compacto, sin borde duro). El color va de blanco lavanda
// (ColDim, la mota en sombra, apenas mas clara que el aire) a dorado (ColLit, la mota contra la luz baja del valle) segun cuanto
// dispersa hacia el ojo (la "luz" que calcula el VS). Rev. 2: paleta PROPIA, distinta de la del aliento (azul frio /
// rosa tibio), para que el polvo no se lea como aliento que quedo.
// Modelo de referencia: scripts/vida_model.py (dust_ps). Verificador: scripts/hlsl/Vida_check.py.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DustPS"  OutputType CMOT_Float3
//       additionalOutputs: Alpha CMOT_Float1 (-> Opacity). La salida principal se llama "return" (gotcha 453).
// SALIDA float3 = color LINEAL premultiplicado -> Emissive Color. Alpha -> Opacity.
// ENTRADAS (3, en este orden):
//   1  DustV           float4  VertexInterpolator, pin PS (su VS = DustV de DustVS)  (esquina x, y, alfa, luz)
//   2  ColLit          float3  VectorParameter ColLit, pin RGB                     lineal (1, 0.93, 0.74)
//   3  ColDim          float3  VectorParameter ColDim, pin RGB                     lineal (0.92, 0.9, 0.96)
// USA ADEMAS: nada. Sin texturas. El material: Unlit, Translucent AlphaComposite, Two Sided, sin niebla de
//       translucidos, TranslucencySortPriority 5 en el componente (despues del pacer 0, antes del metaball 10 y del
//       aliento 20: el polvo esta detras del aliento y el disco del metaball queda despejado por el VS).
// --------------------------------------------------------------------------------------------------------
float2 c = DustV.xy;
float m = saturate(1.0 - dot(c, c));
m = m * m;
float a = saturate(m * DustV.z);
float3 col = lerp(ColDim, ColLit, saturate(DustV.w));
Alpha = a;
return col * a;
