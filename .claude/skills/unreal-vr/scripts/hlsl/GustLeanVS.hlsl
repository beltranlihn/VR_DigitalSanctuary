// GustLeanVS - M_BreathValley_SC (capa de vida), VERTEX SHADER, entre ValleyGradVS y VertexInterpolator_0. v1 2026-09-28
// LA FRANJA DE LUZ DE LA RAFAGA en el llano y en las colinas. No toca la geometria: recibe la salida de ValleyGradVS
// (dh/dx, dh/dy, h, hf) y le suma, SOLO donde pasa el frente de la rafaga (mas alla de GustNear del usuario):
//   - una INCLINACION de la normal hacia la luz (la hierba peinada por el viento agarra luz): GustK.yz;
//   - opcional, una inclinacion HACIA EL USUARIO que rompe el brillo rasante (franja oscura, "pelo erizado"): GustK.w;
//   - mas "fraccion de cima" (el aclarado CrestLight del PS): w' = sqrt(w^2 + a GustK.x) -> la franja se aclara hacia
//     ColLit sin pasarse (CrestLight x w'^2 sigue siendo un lerp entre 0 y 1 con los rangos del plan).
// Con GustK = 0 (el default: sin rafaga) la rama uniforme se saltea y devuelve G SIN TOCAR: neutro exacto en el
// modelo (el HLSL traducido, Vida_check.py); en la GPU se confirma con el control negativo del paso M5 de la receta.
// En el cielo (Part 1) tambien. La forma del frente es la MISMA que usa el polvo (vida_model).
// Modelo de referencia: scripts/vida_model.py (gust_lean_vs). Verificador: scripts/hlsl/Vida_check.py.
// Plan: docs/PLAN-VIDA-VALLE-2026-09-28.md (seccion 6).
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "GustLeanVS"  OutputType CMOT_Float4
//       sin additionalOutputs (la salida se llama "", gotcha 482). Es el CUERPO de la funcion: termina en return.
// SALIDA float4 = (dh/dx, dh/dy, h, hf) con la rafaga -> VertexInterpolator_0 (pin VS) -> VI1 de ValleyPS.
// ENTRADAS (8, en este orden):
//   1  G               float4  Custom ValleyGradVS                                 el gradiente del valle (lo que antes iba al VI0)
//   2  LP              float3  LocalPosition, pin XYZ                              posicion del vertice en el espacio del valle (cm)
//   3  Part            float   ScalarParameter Part                                0 suelo, 1 cielo
//   4  GustP           float4  VectorParameter GustP, pin RGBA                     (Ox, Oy, dx, dy) trayectoria, espacio del valle: lo escribe el BP
//   5  GustQ           float4  VectorParameter GustQ, pin RGBA                     (s frente, W ancho, e0, e1): lo escribe el BP
//   6  GustR           float4  VectorParameter GustR, pin RGBA                     (rampa, Lf0, Lf1, GustNear): lo escribe el BP
//   7  GustK           float4  VectorParameter GustK, pin RGBA                     (luz, inclinacion x, inclinacion y, erizado) x Amp: lo escribe el BP
//   8  GustS           float4  VectorParameter GustS, pin RGBA                     (usuario x, usuario y, -, -) espacio del valle: lo escribe el BP
// USA ADEMAS: nada. Sin bucles, sin arreglos ni indices dinamicos (regla Adreno, gotcha 399), sin half.
// --------------------------------------------------------------------------------------------------------
float ox = G.x;
float oy = G.y;
float ow = G.w;
float kk = abs(GustK.x) + abs(GustK.y) + abs(GustK.z) + abs(GustK.w);
[branch]
if (Part < 0.5 && kk > 0.0)
{
    float2 dd = GustP.zw;
    float2 rel = LP.xy - GustP.xy;
    float xg = dot(rel, dd);
    float eta = abs(rel.y * dd.x - rel.x * dd.y);
    float rp = max(GustR.x, 1.0);
    float ta = saturate((xg - GustQ.z) / rp);
    float tb = saturate((xg - (GustQ.w - rp)) / rp);
    float Ax = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0) * (1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0));
    float th = saturate((eta - GustR.y) / max(GustR.z - GustR.y, 1.0));
    float hx = 1.0 - th * th * th * (th * (6.0 * th - 15.0) + 10.0);
    float tu = saturate(((GustQ.x - xg) / max(GustQ.y, 1.0) + 2.0) * 0.25);
    float bl = 16.0 * tu * tu * (1.0 - tu) * (1.0 - tu);
    float2 sv = LP.xy - GustS.xy;
    float rs = length(sv);
    float tn = saturate((rs - GustR.w) / max(GustR.w, 1.0));
    float nf = tn * tn * tn * (tn * (6.0 * tn - 15.0) + 10.0);
    float a = Ax * hx * bl * nf;
    float tvx = -sv.x / max(rs, 1.0);
    float tvy = -sv.y / max(rs, 1.0);
    ox = G.x - a * (GustK.y + GustK.w * tvx);
    oy = G.y - a * (GustK.z + GustK.w * tvy);
    float gl = a * GustK.x;
    if (gl > 0.0) { ow = sqrt(G.w * G.w + gl); }
}
return float4(ox, oy, G.z, ow);
