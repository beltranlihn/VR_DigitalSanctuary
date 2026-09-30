// DrawPaletteSwatchPS v2 - M_DrawPaletteSwatch_SC, PIXEL SHADER (unlit). El casquete central de la paleta 3D de dibujo.
// Pedido de Beltran (2026-09-29, 2a vuelta): el casquete se pinta COMPLETO del color elegido y la textura del pincel
// solo le da el CARACTER (no la silueta del trazo). Mismo sombreado falso y mate que DrawPaletteShadePS.
// A = alfa del INTERIOR del trazo (DrawPaletteSwatchUV: sin bordes ni punta) -> veladura de Light; en Marker/Oil/Wet
//     el interior es casi 1 (liso).
// Bump = R del mapa normal del pincel (-1..1), BumpAmt 0.4 en OilPaint/WetPaint (sus cerdas), 0 en los demas: es el
//     mismo relieve falso que usa M_TB_Paint en el trazo (Bump.R * ReliefAmt).
// Entradas: N (VertexNormalWS), V (CameraVector), P (LocalPosition, cm), Base (color), A, Bump, BumpAmt, LightDir,
//           Ambient, Diffuse, Wrap, Fill, SelfGlow, Grain, GrainScale (cm), Mottle, MottleScale (cm).
struct PalLib
{
    float H(float3 p)
    {
        p = frac(p * 0.3183099 + 0.1);
        p *= 17.0;
        return frac(p.x * p.y * p.z * (p.x + p.y + p.z));
    }
    float VN(float3 x)
    {
        float3 i = floor(x);
        float3 f = frac(x);
        f = f * f * (3.0 - 2.0 * f);
        float a = lerp(lerp(H(i), H(i + float3(1, 0, 0)), f.x), lerp(H(i + float3(0, 1, 0)), H(i + float3(1, 1, 0)), f.x), f.y);
        float b = lerp(lerp(H(i + float3(0, 0, 1)), H(i + float3(1, 0, 1)), f.x), lerp(H(i + float3(0, 1, 1)), H(i + float3(1, 1, 1)), f.x), f.y);
        return lerp(a, b, f.z);
    }
};
PalLib L;
float3 n = normalize(N);
float3 l = normalize(LightDir);
float key = saturate((dot(n, l) + Wrap) / (1.0 + Wrap));
float fill = saturate(dot(n, normalize(V)));
float hemi = 0.5 + 0.5 * n.z;
float shade = Ambient * hemi + Diffuse * key + Fill * fill;
float m = L.VN(P / max(MottleScale, 0.1));
float3 gp = P / max(GrainScale, 0.01);
float g = (L.VN(gp) + 0.5 * L.VN(gp * 2.7)) / 1.5 - 0.5;
float foot = length(fwidth(gp));
float grainf = (1.0 + Mottle * (m - 0.5) * 2.0) * (1.0 + 2.0 * Grain * g * saturate(1.5 - foot));
float tex = lerp(0.45, 1.05, saturate(A)) + BumpAmt * Bump;
return Base * grainf * (shade + SelfGlow) * max(tex, 0.0);
