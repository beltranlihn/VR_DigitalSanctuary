// ChargeRingFramePS v1 - M_ChargeRing_Frame_SC, PIXEL SHADER (unlit). El metal de SM_ChargeRing_SC.
// La obra no tiene luces: el metal se sombrea aca (difuso + especular + reflejo cielo/suelo + fresnel, que es lo
// que hace brillar los biseles) y ademas la luz de cada cavidad TINE SUS PAREDES segun la carga (el rebote que
// un material unlit no recibe).
// Entradas: N (VertexNormalWS), V (CameraVectorWS), P (LocalPosition, cm), Px (ScreenPosition.PixelPosition),
//           MetalColor, LightDir, Ambient, Diffuse, Spec, Gloss, SkyColor, GroundColor, Env,
//           C0..C4, K0..K4, Pastel, EmptyLevel, FullLevel, EdgeSoftness, WallGlow.
// 🔴 Constantes de la MALLA (no son perillas): salen de blender-3d/scripts/gen_charge_ring.py. Si cambia la
//    malla, cambian aca: R 23 cm, cavidades 0,644-0,837 R, cara en x 0,11 R, piso en x 0,07 R, barras 0,12 R.
float3 n = normalize(N);
float3 v = normalize(V);
float3 l = normalize(LightDir);
float ndl = saturate(dot(n, l));
float3 r = reflect(-v, n);
float rdl = saturate(dot(r, l));
float fres = pow(1.0 - saturate(dot(n, v)), 3.0);
float3 env = lerp(GroundColor, SkyColor, saturate(r.z * 0.5 + 0.5));
float3 col = MetalColor * (Ambient + Diffuse * ndl)
           + env * (Env * lerp(0.3, 1.0, fres))
           + Spec * (pow(rdl, max(Gloss, 1.0)) + 0.15 * pow(rdl, 3.0));
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
float dither = (frac(dot(Px, float2(0.7548776662, 0.5698402910))) - 0.5) / 255.0;
return col + dither;
