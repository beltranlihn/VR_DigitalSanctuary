// @uses CellShade,Caustic
// @inputs NrmC,FluidAb,Pw,Ctr,CamL,CellHigh,CellLow,CellFill,Light,Caus,Phase
// @outputs return:Float3
// CÉLULA MEDIA = MEMBRANA TRANSLÚCIDA CON UN NÚCLEO PERLA ADENTRO, como la célula de Loving (2026-09-30, Beltrán: "las otras
// amebas quedaron demasiado low poly y se ven como globitos flotando; más cercanas a la estética de la principal, sin consumir
// mucho"). Sigue siendo UNA pasada opaca (sin orden de translúcidos ni sobre-dibujo): lo de atrás es el color del MEDIO en esa
// dirección (FluidAb), que es lo que se ve a través del agua.
//   núcleo: esfera ANALÍTICA (rayo cámara -> píxel contra la esfera Ctr del VS): redonda y sin facetas aunque la malla sea de
//           642 / 42 vértices; sombreado perla (CellShade) + cáusticas; borde difuso (el núcleo se ve A TRAVÉS de la membrana).
//   membrana: la superficie de la malla (la ameba), película lila: cuerpo casi transparente (CellBody = CellHigh.a), borde de
//           Fresnel más denso y el LIMBO se desvanece en el medio -> la silueta facetada de la icoesfera no se ve.
// Cáusticas por píxel solo en lo que mira hacia arriba; absorción hacia el color del medio (a lo lejos se funde EXACTA en el fondo).
// Light = dirección de la luz (la misma de la célula de Loving). CamL = cámara en espacio LOCAL (la misma que usa el VS).
// 🔴 Material en precisión COMPLETA (MFPM_Full_MaterialExpressionOnly): Pw.xy / 18 cm llega a +-100 y la fase a 20 pi.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float phC = lerp(T * Caus.z, Phase.y, step(0.5, Phase.w));
float3 N  = NrmC.xyz * rsqrt(max(dot(NrmC.xyz, NrmC.xyz), 1.0e-4));
float3 Lv = normalize(Light.xyz + float3(0.0, 0.0, 1.0e-3));
float3 V  = normalize(Pw.xyz - CamL.xyz + float3(1.0e-4, 0.0, 0.0));
float cs  = max(Caus.x * L.Caustic(Pw.xy / max(Caus.y, 1.0), phC) * max(N.z, 0.0), 0.0);
// --- núcleo perla (analítico) ---
float  ri   = max(Ctr.w, 0.1);
float3 oc   = CamL.xyz - Ctr.xyz;
float  b    = dot(oc, V);
float  disc = b * b - (dot(oc, oc) - ri * ri);
float  hitK = saturate(disc / (ri * ri * 0.45));     // borde del núcleo difuso (elegido mirando 0,12 / 0,45 / 0,8)
float  tH   = -b - sqrt(max(disc, 0.0));
float3 Nn   = normalize(CamL.xyz + V * tH - Ctr.xyz + float3(0.0, 0.0, 1.0e-4));
float3 core = L.CellShade(Nn, Lv, float4(CellHigh.rgb, 1.0), CellLow, CellFill) * (1.0 + cs);
// --- membrana ---
float NV    = saturate(abs(NrmC.w));
float fres  = pow(1.0 - NV, 2.5);
float limb  = smoothstep(0.0, 0.22, NV);
float filmA = lerp(0.10 + 0.25 * saturate(CellHigh.a), 0.75, fres) * limb;
float3 film = CellHigh.rgb * (0.55 + 0.45 * (dot(N, Lv) * 0.5 + 0.5)) * (1.0 + 0.5 * cs);
// medio de atrás -> núcleo visto a través de la membrana -> membrana
float3 c = lerp(FluidAb.rgb, core, hitK * 0.85);
c = lerp(c, film, filmA);
return lerp(FluidAb.rgb, c, 1.0 - saturate(FluidAb.a));
