// StrokeUVS v1 - MF_TB_StrokeU, VERTEX SHADER (Custom -> VertexInterpolator). U del trazo TB calculada en el material.
// Pedido de Beltran (2026-09-30): "el inicio del trazo es cada vez mas lejos de mi mano... debiera ser siempre desde el
// punto donde dibujo". Con la U estirada a todo el trazo (UVStyle Stretch, fiel a Tilt Brush) la punta de la textura
// (u 0.8..1 en los 4 pinceles de la paleta, medido en las PNG de ob-tools) ocupa el 20 % del LARGO: crece con el trazo.
// Aca la punta mide TipCm fijos (y el arranque HeadCm, 0 = proporcional como TB). Trazos cortos (L*(1-UTip) < TipCm)
// quedan EXACTOS a Tilt Brush. TipCm = HeadCm = 0 -> u = arco/largo, identico al K_U que calculaba el Blueprint.
// Ademas saca del Blueprint la normalizacion global (O(N) por cuadro): el BP solo escribe el arco (UV1.x) y StrokeLen.
// UArc 0 (default) = devuelve UV0 tal cual -> neutro para cualquier otro uso del maestro.
// Entradas: UV0 (TexCoord0), UV1 (TexCoord1: x = arco en cm), Len (StrokeLen), UArc, HeadCm, TipCm, UHead, UTip.
float L = max(Len, 0.01);
float a = UV1.x;
float hh = HeadCm > 0 ? min(HeadCm, L * UHead) : L * UHead;
float tt = TipCm > 0 ? min(TipCm, L * (1.0 - UTip)) : L * (1.0 - UTip);
float u;
if (a < hh) u = a / max(hh, 1e-4) * UHead;
else if (a > L - tt) u = UTip + (a - (L - tt)) / max(tt, 1e-4) * (1.0 - UTip);
else u = UHead + (a - hh) / max(L - hh - tt, 1e-4) * (UTip - UHead);
return float2(lerp(UV0.x, saturate(u), UArc), UV0.y);
