// ChargeRingFramePS v3 - M_ChargeRing_Frame_SC y M_ChargeRing_FrameHUD_SC, PIXEL SHADER (unlit). El cuerpo de
// SM_ChargeRing_SC.
// v3 (2026-09-30, Beltran: "mucho mejor; que el aro delgado que esta por afuera en el borde sea de luz, calida"): el
// canto exterior del NUCLEO (lo que sobresale de las placas, r > 0,955 R) es LUZ calida = pin SkyColor = parametro
// RimLight (color x brillo; negro = apagado), como las cintas de luz de los botones (M_SCLight_SC).
// v2 (2026-09-30, Beltran: "el material del anillo esta muy oscuro, debe ser mas de la onda de los otros botones"):
// el metal oscuro (v1: difuso + especular + reflejo cielo/suelo; respaldo en hlsl_backups/) pasa al HORMIGON de la
// familia de botones = el sombreado de SCObjectShadePS (hemisferio + luz principal con wrap + relleno desde la vista,
// manchado grande + grano fino que se apaga cuando el pixel es mas grande que el grano). Se CONSERVA el rebote: la luz
// de cada cavidad tine sus paredes segun la carga (lo que un material unlit no recibe).
// Entradas: los PINES conservan los nombres de la v1 (no se recablea el material); los PARAMETROS se renombraron:
//   pin MetalColor = parametro Base · pin Spec = Fill · pin Gloss = Wrap · pin Env = SelfGlow ·
//   pin SkyColor = RimLight (v3) · pin GroundColor sin uso.
//   N (VertexNormalWS), V (CameraVectorWS), P (LocalPosition, cm), Px (ScreenPosition.PixelPosition), LightDir,
//   Ambient, Diffuse, C0..C4, K0..K4, Pastel, EmptyLevel, FullLevel, EdgeSoftness, WallGlow.
// Manchado y grano con las constantes de la familia (M_SCObject_SC: Mottle 0,08 a 3 cm, Grain 0,06 a 0,08 cm).
// 🔴 Constantes de la MALLA (no son perillas): salen de blender-3d/scripts/gen_charge_ring.py. Si cambia la
//    malla, cambian aca: R 23 cm, cavidades 0,644-0,837 R, cara en x 0,11 R, piso en x 0,07 R, barras 0,12 R.
struct RingLib
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
RingLib L;
float3 n = normalize(N);
float3 v = normalize(V);
float3 l = normalize(LightDir);
float key = saturate((dot(n, l) + Gloss) / (1.0 + Gloss));          // Gloss = Wrap
float fill = saturate(dot(n, v));
float hemi = 0.5 + 0.5 * n.z;
float shade = Ambient * hemi + Diffuse * key + Spec * fill;          // Spec = Fill
float m = L.VN(P / 3.0);
float3 gp = P / 0.08;
float g = (L.VN(gp) + 0.5 * L.VN(gp * 2.7)) / 1.5 - 0.5;
float foot = length(fwidth(gp));
float3 alb = MetalColor * (1.0 + 0.08 * (m - 0.5) * 2.0) * (1.0 + 0.12 * g * saturate(1.5 - foot));   // MetalColor = Base
float3 col = alb * (shade + Env);                                    // Env = SelfGlow
// --- rebote de las cavidades: misma cuenta que la UV de los pisos (gen_charge_ring.py: slot_uv) ---
float RR = 23.0;
float rf = length(P.yz) / RR;
float ax = abs(P.x) / RR;
float ang = degrees(atan2(P.z, -P.y));                    // el FBX espeja Y: asi se mide igual que en Blender
float s = fmod(fmod(ang - 90.0, 360.0) + 360.0, 360.0);   // 0..360 desde la barra de arriba, antihorario
float j = min(floor(s / 72.0), 4.0);
float d = degrees(asin(saturate(0.06 / max(rf, 0.3))));
float t = saturate((s - j * 72.0 - d) / (72.0 - 2.0 * d));
float c = (j < 0.5) ? C0 : ((j < 1.5) ? C1 : ((j < 2.5) ? C2 : ((j < 3.5) ? C3 : C4)));
float3 k = (j < 0.5) ? K0 : ((j < 1.5) ? K1 : ((j < 2.5) ? K2 : ((j < 3.5) ? K3 : K4)));
k = lerp(k, float3(1.0, 1.0, 1.0), saturate(Pastel));
float e = max(EdgeSoftness, 0.002);
float lit = saturate((saturate(c) * (1.0 + e) - t) / e);
float band = smoothstep(0.614, 0.639, rf) * (1.0 - smoothstep(0.842, 0.867, rf));
float depth = saturate((0.11 - ax) / 0.04);               // 0 en la cara, 1 en el piso
col += k * (band * depth * depth * WallGlow * lerp(EmptyLevel, FullLevel, lit));
// v3: el aro exterior del nucleo es luz calida (las placas terminan en 0,955 R; el rincon redondeado hace el paso suave)
float rim = smoothstep(0.957, 0.967, rf);
col = lerp(col, SkyColor, rim);                            // SkyColor = RimLight
float dither = (frac(dot(Px, float2(0.7548776662, 0.5698402910))) - 0.5) / 255.0;
return col + dither;
