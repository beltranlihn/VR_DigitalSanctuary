// InkArcPS v1 - M_DrawPalette_Ink_SC (Unlit, Translucent, TwoSided), PIXEL SHADER. Medidor de tinta de la paleta (2026-09-30).
// Pedido de Beltran: "un radial slider que marca cuanta tinta nos queda; al llegar al final activa save drawing";
// "verde pastel, medio translucido".
// Banda en arco (ProceduralMesh de BP_DrawPalette_SC.InkBuild): UV.x 0 = junto al slider de grosor -> 1 = junto a rehacer;
// UV.y 0..1 a lo ancho. Fill (0..1, lo empuja el director) = tinta que queda: lleno desde UV.x 0 hasta Fill.
// Salida float4: rgb -> Emissive, a -> Opacity.
float x = UV.x;
float across = 1.0 - abs(UV.y * 2.0 - 1.0);
float edge = saturate(across * 3.0);
float f = saturate(Fill);
float w = max(Soft, 0.001);
float m = saturate((f - x) / w + 0.5);
float head = exp(-abs(x - f) / (w * 2.0)) * step(0.0005, f);
float3 c = lerp(TrackColor, Color, m) * Glow + Color * head * HeadGlow;
float a = edge * saturate(lerp(TrackAlpha, FillAlpha, m) + head * HeadGlow * 0.5);
return float4(c, a);
