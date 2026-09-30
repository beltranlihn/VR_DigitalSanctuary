// DrawPaletteShadePS v1 - M_DrawPalette_SC, PIXEL SHADER (unlit). La paleta de la etapa de dibujo (blender-3d/assets/draw-palette.md).
// Pedido de Beltran (2026-09-29): hormigon calido, MATE (sin reflejos), en un nivel SIN luz direccional -> algo de
// emision propia pero con SOMBREADO para que se lea en 3D. Luz falsa: principal fija en el mundo (wrap), relleno desde
// la vista y un hemisferio (arriba claro). Iconos de pincel (T_Ico_*) y textos UNDO/REDO en BLANCO por mascara.
// Entradas: N (VertexNormalWS), V (CameraVector), P (LocalPosition, cm), Base (color), M (mascara, R de MaskTex),
//           UVm (UV de la mascara ya girada/escalada: fuera de 0..1 no hay mascara), Ink, InkGlow, LightDir,
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
// hormigon: manchado grande + grano fino (se apaga cuando el pixel es mas grande que el grano)
float m = L.VN(P / max(MottleScale, 0.1));
float3 gp = P / max(GrainScale, 0.01);
float g = (L.VN(gp) + 0.5 * L.VN(gp * 2.7)) / 1.5 - 0.5;
float foot = length(fwidth(gp));
float3 alb = Base * (1.0 + Mottle * (m - 0.5) * 2.0) * (1.0 + 2.0 * Grain * g * saturate(1.5 - foot));
float3 c = alb * (shade + SelfGlow);
// mascara (icono / texto) en blanco
float inside = step(0.0, UVm.x) * step(UVm.x, 1.0) * step(0.0, UVm.y) * step(UVm.y, 1.0);
float mk = saturate(M) * inside;
c = lerp(c, Ink * (0.55 * shade + InkGlow), mk);
return c;
