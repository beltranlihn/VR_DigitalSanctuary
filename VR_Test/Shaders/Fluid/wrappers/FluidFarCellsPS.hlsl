// @uses
// @inputs Crn,FA,FB,LQ,CellHigh,CellLow
// @outputs return:Float3,Alpha:Float1,Dith:Float1
// SILUETA de una célula lejana (Masked + alpha-to-coverage): núcleo con BORDE DE AMEBA (3 y 5 lóbulos
// que giran) + 3-5 satélites; el disco que gana da la "normal" de una esfera para el mismo bicolor de
// las medias, con la luz del MUNDO proyectada en el quad (LQ, del VS). Absorción hacia el medio (FA).
// El fundido por cercanía/borde (FB.x) va al COLOR (hacia el medio) y el alfa queda SOLO para el borde
// de la silueta: el A2C del móvil de UE cuantiza la cobertura a 4 niveles (el primero ya es 25 %) y
// el fundido por alfa aparecía a saltos (revisión MAT-2 / MOV-1). El VS además achica la silueta en el
// último tramo del fundido, así una silueta casi fundida no tapa (con profundidad) lo que tiene detrás.
// Dith = la máscara con dither R2 SOLO si alguna vez se apaga el A2C: entonces el corte tiene que ser
// 0,5 explícito (con el default 0,333 dibuja un cuadrado punteado).
// Bucle de cota CONSTANTE (regla Adreno). Todo en coordenadas del quad (-1..1): apto half.
float2 uv = Crn.xy * 2.0 - 1.0;
float sd = FB.y;
float rot = FB.z;
// atan2(0,0) es indefinido en SPIR-V (GLSL.std.450) y con la UV en half el píxel central cae EXACTO
// en 0 (revisión MAT-6 / MOV-4). Ahí el ángulo no importa (se divide una longitud 0).
float ang = (dot(uv, uv) > 1.0e-4) ? atan2(uv.y, uv.x) : 0.0;
float rC = 0.36 * (1.0 + 0.12 * sin(3.0 * ang + 2.0 * rot) + 0.06 * sin(5.0 * ang - rot + sd * 7.0));
float2 dc = uv / rC;
float best = 1.0 - length(dc);
float3 n = float3(dc, sqrt(max(1.0 - dot(dc, dc), 0.0)));
float nSat = 3.0 + floor(frac(sd * 7.7) * 2.999);
[unroll] for (int k = 0; k < 5; k++)
{
    float fk = (float)k;
    float a = rot + fk * 1.2566371 + 0.5 * sin(sd * 17.0 + fk * 3.1);
    float2 cc = 0.62 * float2(cos(a), sin(a));
    float r = 0.13 + 0.05 * sin(sd * 9.0 + fk * 2.3);
    float2 d = (uv - cc) / r;
    float fv = (1.0 - length(d)) * step(fk, nSat - 0.5);
    if (fv > best) { best = fv; n = float3(d, sqrt(max(1.0 - dot(d, d), 0.0))); }
}
float3 nn = n * rsqrt(max(dot(n, n), 1.0e-4));
float3 lq = LQ.xyz * rsqrt(max(dot(LQ.xyz, LQ.xyz), 1.0e-4));
float w = lerp(1.0, dot(nn, lq) * 0.5 + 0.5, CellLow.a);
float3 c = lerp(CellLow.rgb, CellHigh.rgb, w);
// gelatina, como las medias: el cuerpo se ve en CellHigh.a (CellBody), el borde conserva el brillo
float fres = pow(1.0 - saturate(nn.z), 2.5);
float vis = lerp(saturate(CellHigh.a), 1.0, fres);
c = lerp(FA.rgb, c, (1.0 - saturate(FA.a)) * vis);
c = lerp(FA.rgb, c, saturate(FB.x));
Alpha = smoothstep(0.0, 0.12, best);
float nz = frac(dot(Parameters.SvPosition.xy, float2(0.7548776662, 0.5698402910)));
Dith = Alpha - nz + 0.5;
return c;
