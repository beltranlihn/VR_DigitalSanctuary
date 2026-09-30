// HallInteriorPS v3 - M_Hall_Interior_SC, PIXEL SHADER (unlit). El interior del hall-portal.
// La luz viene HORNEADA de Blender (Cycles) en CANALES DE UV (blender-3d/scripts/bake_export_hall.py):
// UV2 = (R, G), UV3 = (B, 0); irradiancia float, 1 = percentil 80 de lo iluminado (el oculo pasa de 1).
// 🔴 No en color de vertice: el importador de Unreal lo descarto. Unreal invierte la V: G llega como 1 - G.
// Entradas: L2 (TexCoord 2), L3 (TexCoord 3), P (LocalPosition, cm), Px (ScreenPosition.PixelPosition),
//           Albedo, AlbedoDark, LightScale, LightGamma, GrainScale (cm), GrainAmount, MottleScale (cm), MottleAmount,
//   v3:     G (salida de HallGroovesPS: nucleo, halo, labio), GrooveColor, D (PixelDepth, cm),
//           HazeColor, HazeDensity (1/cm), HazeAmount, Knee.
// 🔴 Material en MFPM_Full_MaterialExpressionOnly: P llega a 730 cm y el ruido en fp16 se rompe.
// v3 (2026-09-29, "blancos muy quemados" en el preview Android = sin tonemapper): hombro suave por el canal
//     maximo (conserva el tono) desde Knee hasta 1; bruma calida por distancia (solo en este material:
//     el exterior negro no la recibe); hendiduras iluminadas con halo.
struct HallLib
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
HallLib L;
// manchado suave (dos octavas grandes) -> mezcla entre el albedo claro y el oscuro
float m = 0.65 * L.VN(P / max(MottleScale, 1.0)) + 0.35 * L.VN(P / max(MottleScale * 0.33, 1.0));
float3 alb = lerp(Albedo, AlbedoDark, saturate((m - 0.5) * 2.0 * MottleAmount + 0.5 * MottleAmount));
// grano fino de granito, atenuado cuando el pixel es mas grande que el grano (sin titileo en la Quest)
float3 gp = P / max(GrainScale, 0.05);
float foot = length(fwidth(gp));
float g = (L.VN(gp) + 0.5 * L.VN(gp * 2.7)) / 1.5 - 0.5;
alb *= 1.0 + 2.0 * GrainAmount * g * saturate(1.5 - foot);
// luz horneada
float3 light = pow(max(float3(L2.x, 1.0 - L2.y, L3.x), 0.0), LightGamma) * LightScale;
// hendiduras: labio oscuro sobre la superficie + nucleo emisivo + halo que lava la superficie
float3 c = alb * light * G.z + GrooveColor * (G.x + G.y * alb * 2.0);
// bruma calida por distancia
float fog = saturate((1.0 - exp(-D * HazeDensity)) * HazeAmount);
c = lerp(c, HazeColor, fog);
// hombro suave: nada pasa de 1, el tono se conserva
float mx = max(max(c.r, c.g), c.b);
float kn = min(Knee, 0.99);
float mo = (mx < kn) ? mx : kn + (1.0 - kn) * (1.0 - exp(-(mx - kn) / (1.0 - kn)));
c *= mo / max(mx, 1.0e-4);
float dither = (frac(dot(Px, float2(0.7548776662, 0.5698402910))) - 0.5) / 255.0;
return c + dither;
