// @uses CellShade,Caustic
// @inputs NrmC,FluidAb,Pw,CellHigh,CellLow,CellFill,Light,Caus,Phase
// @outputs return:Float3
// CÉLULA MEDIA (opaca, unlit, aspecto de GELATINA): bicolor mitad-lambert (CellHigh.rgb luz, CellHigh.a =
// CellBody = cuánto se ve el cuerpo, CellLow sombra, CellLow.a contraste) + relleno de sombra, CÁUSTICAS POR PÍXEL (solo en lo que mira hacia
// arriba; como OBJ_FS del prototipo) y ABSORCIÓN hacia el color del medio en esa dirección: a lo lejos
// la célula se funde EXACTA en el fondo. Light = dirección de la luz (la misma de la célula de Loving).
// 🔴 Este material va en precisión COMPLETA (MFPM_Full_MaterialExpressionOnly): Pw.xy / 18 cm llega
// a +-100 y la fase de la cáustica a 20 pi; en half se cuantizan (revisión MAT-4).
// Fase: la misma que las motas y el BP (Phase.y en juego, T x Caus.z en el editor).
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float phC = lerp(T * Caus.z, Phase.y, step(0.5, Phase.w));
float3 N  = NrmC.xyz * rsqrt(max(dot(NrmC.xyz, NrmC.xyz), 1.0e-4));
float3 Lv = normalize(Light.xyz + float3(0.0, 0.0, 1.0e-3));
float3 c  = L.CellShade(N, Lv, float4(CellHigh.rgb, 1.0), CellLow, CellFill);
float cs  = Caus.x * L.Caustic(Pw.xy / max(Caus.y, 1.0), phC) * max(N.z, 0.0);
c *= 1.0 + max(cs, 0.0);
// GELATINA, como la célula de Loving (Beltrán: "se notan demasiado blancas, no son de la estética de la
// principal; el fog no se las come"): el CUERPO se ve solo en CellHigh.a (CellBody) y el BORDE (Fresnel sobre
// N.V del VS) conserva el brillo perla. Con CellBody 1 = la célula opaca de antes.
float fres = pow(1.0 - saturate(abs(NrmC.w)), 2.5);
float vis  = lerp(saturate(CellHigh.a), 1.0, fres);
return lerp(FluidAb.rgb, c, (1.0 - saturate(FluidAb.a)) * vis);
