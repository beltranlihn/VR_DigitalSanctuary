// HallTilePS v1 - M_Hall_Tile_SC, PIXEL SHADER (unlit). Las 5 baldosas de las etapas en el centro del hall.
// Pedido de Beltran (2026-09-29): baldosas (no alfombra), cada una con el color de su etapa, suave, que encaje en el
// interior calido, y del MISMO hormigon pulido que los muros -> mismo manchado + grano que HallInteriorPS, teñido.
// Luz: la del piso horneado copiada debajo de cada vertice (gen_bake_hall_tiles.py) en UV2 = (R, G), UV3 = (B, 0).
// Entradas: L2, L3, P (LocalPosition, cm), Px (PixelPosition), D (PixelDepth, cm), TileColor, Albedo, AlbedoDark, Tint,
//           LightScale, LightGamma, Glow, GrainScale, GrainAmount, MottleScale, MottleAmount, HazeColor, HazeDensity,
//           HazeAmount, Knee.
// 🔴 MFPM_Full_MaterialExpressionOnly (P llega a 250 cm y el ruido en fp16 se rompe).
struct TileLib
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
TileLib L;
// hormigon: el mismo manchado que el muro, en el tono de la etapa
float m = 0.65 * L.VN(P / max(MottleScale, 1.0)) + 0.35 * L.VN(P / max(MottleScale * 0.33, 1.0));
float3 base = lerp(Albedo, AlbedoDark, saturate((m - 0.5) * 2.0 * MottleAmount + 0.5 * MottleAmount));
float lum = dot(base, float3(0.3, 0.59, 0.11));
float3 alb = lerp(base, TileColor * lum * 1.6, saturate(Tint));
float3 gp = P / max(GrainScale, 0.05);
float foot = length(fwidth(gp));
float g = (L.VN(gp) + 0.5 * L.VN(gp * 2.7)) / 1.5 - 0.5;
alb *= 1.0 + 2.0 * GrainAmount * g * saturate(1.5 - foot);
float3 light = pow(max(float3(L2.x, 1.0 - L2.y, L3.x), 0.0), LightGamma) * LightScale;
float3 c = alb * light + TileColor * Glow;
float fog = saturate((1.0 - exp(-D * HazeDensity)) * HazeAmount);
c = lerp(c, HazeColor, fog);
float mx = max(max(c.r, c.g), c.b);
float kn = min(Knee, 0.99);
float mo = (mx < kn) ? mx : kn + (1.0 - kn) * (1.0 - exp(-(mx - kn) / (1.0 - kn)));
c *= mo / max(mx, 1.0e-4);
float dither = (frac(dot(Px, float2(0.7548776662, 0.5698402910))) - 0.5) / 255.0;
return c + dither;
