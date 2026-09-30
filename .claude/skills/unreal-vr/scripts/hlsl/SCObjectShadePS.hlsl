// SCObjectShadePS v1 - M_SCObject_SC, PIXEL SHADER (unlit). El hormigon de la familia (timbre, SAVE MELODY, sensor, HUD):
// el mismo sombreado falso de la paleta (DrawPaletteShadePS: hemisferio + luz principal con wrap + relleno desde la vista,
// manchado + grano, mascara blanca por UV1) + FLASH: luz calida que se suma (la aparicion 'luz primero' la baja de 1 a 0
// mientras la pieza "se enfria"; el clac de la pieza que asoma). Ver blender-3d/assets/aparicion-luz.md.
// Entradas: N (VertexNormalWS), V (CameraVector), P (LocalPosition, cm), Base, M (R de MaskTex en UV1), UVm (UV1),
//           Ink, InkGlow, LightDir, Ambient, Diffuse, Wrap, Fill, SelfGlow, Grain, GrainScale, Mottle, MottleScale,
//           Flash, FlashColor.
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
c += FlashColor * Flash;          // aparicion 'luz primero': la pieza nace de luz y se enfria
return c;
