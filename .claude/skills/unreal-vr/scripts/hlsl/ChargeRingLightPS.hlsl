// ChargeRingLightPS v1 - M_ChargeRing_Light_SC, PIXEL SHADER (unlit). Los pisos de luz de SM_ChargeRing_SC.
// Entradas: UV (TexCoord0), Px (ScreenPosition.PixelPosition), C0..C4 (Charge_<Etapa>), K0..K4 (Color_<Etapa>),
//           Pastel, EmptyLevel, FullLevel, EdgeSoftness, FrontGlow.
// UV.x = etapa + t (0..5): 0 Entering, 1 Recognizing, 2 Loving, 3 Attracting, 4 Surrounding (antihorario desde
//        arriba-izquierda); t = avance a lo largo de la cavidad, 0 y 1 caen justo en el borde de las barras.
// UV.y = 1 - radial (Unreal invierte la V al importar; gotcha 302).
float j = clamp(floor(UV.x), 0.0, 4.0);
float t = saturate(UV.x - j);
float c = (j < 0.5) ? C0 : ((j < 1.5) ? C1 : ((j < 2.5) ? C2 : ((j < 3.5) ? C3 : C4)));
float3 k = (j < 0.5) ? K0 : ((j < 1.5) ? K1 : ((j < 2.5) ? K2 : ((j < 3.5) ? K3 : K4)));
k = lerp(k, float3(1.0, 1.0, 1.0), saturate(Pastel));
// carga: c = 0 apaga toda la cavidad, c = 1 la enciende entera; el frente tiene EdgeSoftness de ancho
float e = max(EdgeSoftness, 0.002);
float cc = saturate(c) * (1.0 + e);
float lit = saturate((cc - t) / e);
// brillo del frente mientras carga (0 < c < 1)
float charging = step(0.001, c) * step(c, 0.999);
float front = charging * exp(-abs(cc - 0.5 * e - t) / max(3.0 * e, 0.004));
// la franja es un poco mas viva al centro (se lee como volumen de luz, no como calcomania)
float rv = 2.0 * (1.0 - UV.y) - 1.0;
float body = 1.0 - 0.18 * rv * rv;
float lvl = lerp(EmptyLevel, FullLevel, lit) * body + FrontGlow * front;
// dither R2 de 1 LSB contra las bandas de 8 bits (materials-vr.md)
float dither = (frac(dot(Px, float2(0.7548776662, 0.5698402910))) - 0.5) / 255.0;
return k * lvl + dither;
