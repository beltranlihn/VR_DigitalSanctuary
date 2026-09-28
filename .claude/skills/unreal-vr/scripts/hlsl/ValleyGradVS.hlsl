// ValleyGradVS - M_BreathValley_SC, VERTEX SHADER -> VertexInterpolator_0 -> VI1 del PS.  v2 (revision 2026-09-28)
// Devuelve (dh/dx, dh/dy, h, hf) en una pasada. hf = fraccion de loma (0..1).
// Misma cuenta que ValleyHeightVS (h identica); las derivadas de cada quintica van escritas a mano:
//   S5(t) = t^3 (t (6 t - 15) + 10),  dS5/dx = 30 t^2 (1 - t)^2 / (b - a).
// El GRADIENTE es el exacto de h MAS el termino de SOMBREADO del oleaje, Av grad(s), con Av = SwellShade * S5(SwellNear,
// SwellShadeFull, r): el llano ondula en la luz sin mover la geometria (sin bordes de oclusion). No incluye Av' s.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "ValleyGradVS"  OutputType CMOT_Float4
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float4 = (dh/dx, dh/dy, h, hf), en local (cm y cm/cm). hf = fraccion de loma 0..1 (aclarado de cimas).
//       El gradiente incluye el sombreado del oleaje (ver arriba). Part 1 (cielo) o PerfMode 1/3 -> (0, 0, 0, 0).
//       -> VertexInterpolator_0 (pin VS) -> su pin PS -> entrada VI1 de ValleyPS.
// ENTRADAS (31, en este orden; las 29 primeras son las MISMAS que ValleyHeightVS, mismas expresiones):
//   1  LP              float3  LocalPosition, pin XYZ          posicion del vertice en el espacio del actor (cm); el disco es plano (z = 0)
//   2  Part            float   ScalarParameter Part            0 suelo, 1 cielo (lo pone el Construction Script)
//   3  PerfMode        float   ScalarParameter PerfMode        banco: 1 y 3 = vertices baratos (WPO 0)
//   4  HillAmp         float   ScalarParameter HillAmp         2200 cm (alto de las colinas medias)
//   5  HillScale       float   ScalarParameter HillScale       8 (multiplica las longitudes de onda de las dunas: 100-240 m)
//   6  HillSeed        float   ScalarParameter HillSeed        63 (grados; gira el campo de colinas medias)
//   7  HillNear        float   ScalarParameter HillNear        4500 cm (las colinas medias empiezan)
//   8  HillFull        float   ScalarParameter HillFull        12000 cm (colinas medias plenas)
//   9  HillFade        float   ScalarParameter HillFade        19000 cm (empiezan a apagarse)
//  10  HillEnd         float   ScalarParameter HillEnd         26000 cm (apagadas; el codigo usa max(HillEnd, HillFade + 1))
//  11  DuneLow         float   ScalarParameter DuneLow         -0.35 (umbral de la loma: por debajo, llano)
//  12  DuneHigh        float   ScalarParameter DuneHigh        1.2
//  13  FarBase         float   ScalarParameter FarBase         2600 cm (anillo lejano: garantia del horizonte)
//  14  FarAmp          float   ScalarParameter FarAmp          5500 cm (colinas lejanas sobre el anillo)
//  15  FarScale        float   ScalarParameter FarScale        22 (longitudes de onda lejanas: 275-660 m)
//  16  FarSeed         float   ScalarParameter FarSeed         151 (grados)
//  17  FarIn           float   ScalarParameter FarIn           28000 cm (empieza la capa lejana)
//  18  FarFull         float   ScalarParameter FarFull         40000 cm (colinas lejanas plenas)
//  19  FarCrest        float   ScalarParameter FarCrest        47000 cm (cresta del anillo)
//  20  FarBack         float   ScalarParameter FarBack         59000 cm (todo vale 0 desde aqui: borde de la malla oculto)
//  21  SwellAmp        float   ScalarParameter SwellAmp        1880 cm (oleaje geometrico: amplitud a SwellFar; mas lejos crece con r)
//  22  SwellNear       float   ScalarParameter SwellNear       1500 cm (nada se mueve ni cambia de sombreado a menos de esto)
//  23  SwellIn         float   ScalarParameter SwellIn         28000 cm (el oleaje GEOMETRICO empieza aqui, sobre el anillo lejano)
//  24  SwellFar        float   ScalarParameter SwellFar        40000 cm (desde aqui amplitud ANGULAR constante SwellAmp/SwellFar)
//  25  SwellScale      float   ScalarParameter SwellScale      2.5 (multiplica las longitudes de onda del oleaje: 100-225 m; menos facetea la silueta)
//  26  SwellSpeed      float   ScalarParameter SwellSpeed      1 (multiplica la frecuencia: periodos 31-46 s); fijar y dejar
//  27  SwellSeed       float   ScalarParameter SwellSeed       0 (grados; gira las 4 direcciones del oleaje)
//  28  MorphAmt        float   ScalarParameter MorphAmt        0.15 (respiracion de la amplitud de cada duna media, en su lugar)
//  29  MorphSpeed      float   ScalarParameter MorphSpeed      1 (periodos 41-83 s); fijar y dejar
//  30  SwellShade      float   ScalarParameter SwellShade      1000 cm (oleaje SOLO en el sombreado: amplitud equivalente en la normal)
//  31  SwellShadeFull  float   ScalarParameter SwellShadeFull  5000 cm (el sombreado del oleaje entra de SwellNear a aqui)
// TIEMPO: se lee View.GameTime adentro (uniforme fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
//         Las fases del oleaje y de la respiracion se reducen con frac (en vueltas) ANTES del sin:
//         argumento acotado en Adreno aunque la sesion dure horas.
// RAMAS: if [branch] por radio, como en ValleyHeightVS. La rama del oleaje empieza en SwellNear (el sombreado);
//        la geometria del oleaje vale 0 exacto hasta SI = max(SwellIn, SwellNear).
// REGLAS: material en MFPM_Full_MaterialExpressionOnly; sin bucles ni arreglos (gotcha 399, Adreno).
//         Un Custom por salida (gotcha 454): el WPO y el interpolador se compilan en funciones separadas.
// CONTROL: docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 12. Cableado completo: Valley_CABLEADO.md.
// --------------------------------------------------------------------------------------------------------
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float4(0.0, 0.0, 0.0, 0.0); }
float Tt = View.GameTime;
float x = LP.x;
float y = LP.y;
float r = sqrt(x * x + y * y);
float rs = max(r, 1.0);
float h = 0.0;
float gr = 0.0;
float gx = 0.0;
float gy = 0.0;
float hf = 0.0;
// h, gr (d/dr de las envolventes radiales: se multiplica por p/r al final), gx/gy (el resto) y hf, antes del retiro
float FC = max(FarCrest, FarIn + 1.0);
float FB = max(FarBack, FC + 1.0);
float HE = max(HillEnd, HillFade + 1.0);
// ---- capa 1: colinas medias; la respiracion (uniforme por cuadro) se calcula DENTRO de la rama, fase con frac
[branch]
if (r > HillNear && r < HE)
{
  float m0 = 1.00 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 53.0) + 0.0));
  float m1 = 0.75 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 67.0) + 2.1));
  float m2 = 0.55 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 41.0) + 4.4));
  float m3 = 0.35 * (1.0 + MorphAmt * sin(6.2831853 * frac(MorphSpeed * Tt / 83.0) + 1.3));
  float sH, cH;
  sincos(radians(HillSeed), sH, cH);
  float kh = 6.2831853 / max(HillScale, 0.05);
  float ax0 = kh / 3000.0 * (0.95105652 * cH - 0.30901699 * sH);
  float ay0 = kh / 3000.0 * (0.95105652 * sH + 0.30901699 * cH);
  float ax1 = kh / 2200.0 * (-0.19080900 * cH - 0.98162718 * sH);
  float ay1 = kh / 2200.0 * (-0.19080900 * sH + 0.98162718 * cH);
  float ax2 = kh / 1650.0 * (-0.79863551 * cH - 0.60181502 * sH);
  float ay2 = kh / 1650.0 * (-0.79863551 * sH + 0.60181502 * cH);
  float ax3 = kh / 1250.0 * (-0.61566148 * cH + 0.78801075 * sH);
  float ay3 = kh / 1250.0 * (-0.61566148 * sH - 0.78801075 * cH);
  float s0, c0, s1, c1, s2, c2, s3, c3;
  sincos(ax0 * x + ay0 * y + 0.0, s0, c0);
  sincos(ax1 * x + ay1 * y + 1.7, s1, c1);
  sincos(ax2 * x + ay2 * y + 4.1, s2, c2);
  sincos(ax3 * x + ay3 * y + 2.9, s3, c3);
  float sig = (m0 * s0 + m1 * s1 + m2 * s2 + m3 * s3) / 2.65;
  float gsx = (m0 * c0 * ax0 + m1 * c1 * ax1 + m2 * c2 * ax2 + m3 * c3 * ax3) / 2.65;
  float gsy = (m0 * c0 * ay0 + m1 * c1 * ay1 + m2 * c2 * ay2 + m3 * c3 * ay3) / 2.65;
  float DW = max(DuneHigh - DuneLow, 0.01);
  float tf = saturate((sig - DuneLow) / DW);
  float f = tf * tf * tf * (tf * (6.0 * tf - 15.0) + 10.0);
  float df = 30.0 * tf * tf * (1.0 - tf) * (1.0 - tf) / DW;
  float HW = max(HillFull - HillNear, 1.0);
  float ta = saturate((r - HillNear) / HW);
  float ea = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0);
  float dea = 30.0 * ta * ta * (1.0 - ta) * (1.0 - ta) / HW;
  float EW = HE - HillFade;
  float tb = saturate((r - HillFade) / EW);
  float eb = 1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0);
  float deb = -30.0 * tb * tb * (1.0 - tb) * (1.0 - tb) / EW;
  float env = ea * eb;
  h += HillAmp * env * f;
  gr += HillAmp * (dea * eb + ea * deb) * f;
  gx += HillAmp * env * df * gsx;
  gy += HillAmp * env * df * gsy;
  hf += env * f;
}
// ---- capa 2: anillo lejano + colinas lejanas (no respiran)
[branch]
if (r > FarIn && r < FB)
{
  float sF, cF;
  sincos(radians(FarSeed), sF, cF);
  float kf = 6.2831853 / max(FarScale, 0.05);
  float bx0 = kf / 3000.0 * (0.95105652 * cF - 0.30901699 * sF);
  float by0 = kf / 3000.0 * (0.95105652 * sF + 0.30901699 * cF);
  float bx1 = kf / 2200.0 * (-0.19080900 * cF - 0.98162718 * sF);
  float by1 = kf / 2200.0 * (-0.19080900 * sF + 0.98162718 * cF);
  float bx2 = kf / 1650.0 * (-0.79863551 * cF - 0.60181502 * sF);
  float by2 = kf / 1650.0 * (-0.79863551 * sF + 0.60181502 * cF);
  float bx3 = kf / 1250.0 * (-0.61566148 * cF + 0.78801075 * sF);
  float by3 = kf / 1250.0 * (-0.61566148 * sF - 0.78801075 * cF);
  float u0, v0, u1, v1, u2, v2, u3, v3;
  sincos(bx0 * x + by0 * y + 0.0, u0, v0);
  sincos(bx1 * x + by1 * y + 1.7, u1, v1);
  sincos(bx2 * x + by2 * y + 4.1, u2, v2);
  sincos(bx3 * x + by3 * y + 2.9, u3, v3);
  float sgF = (1.00 * u0 + 0.75 * u1 + 0.55 * u2 + 0.35 * u3) / 2.65;
  float gfx = (1.00 * v0 * bx0 + 0.75 * v1 * bx1 + 0.55 * v2 * bx2 + 0.35 * v3 * bx3) / 2.65;
  float gfy = (1.00 * v0 * by0 + 0.75 * v1 * by1 + 0.55 * v2 * by2 + 0.35 * v3 * by3) / 2.65;
  float tl = saturate((sgF + 0.7) / 1.9);
  float fl = tl * tl * tl * (tl * (6.0 * tl - 15.0) + 10.0);
  float dfl = 30.0 * tl * tl * (1.0 - tl) * (1.0 - tl) / 1.9;
  float RW = FC - FarIn;
  float tr = saturate((r - FarIn) / RW);
  float er = tr * tr * tr * (tr * (6.0 * tr - 15.0) + 10.0);
  float der = 30.0 * tr * tr * (1.0 - tr) * (1.0 - tr) / RW;
  float FW = max(FarFull - FarIn, 1.0);
  float te = saturate((r - FarIn) / FW);
  float ee = te * te * te * (te * (6.0 * te - 15.0) + 10.0);
  float dee = 30.0 * te * te * (1.0 - te) * (1.0 - te) / FW;
  h += FarBase * er + FarAmp * ee * fl;
  gr += FarBase * der + FarAmp * dee * fl;
  gx += FarAmp * ee * dfl * gfx;
  gy += FarAmp * ee * dfl * gfy;
  hf += ee * fl;
}
// ---- capa 3: oleaje viajero. Geometria A = SwellAmp * S5(SI, SwellFar, r) * r / SwellFar (0 exacto hasta SI);
// sombreado Av = SwellShade * S5(SwellNear, SwellShadeFull, r), que solo suma Av * grad(s) a la normal
[branch]
if (r > SwellNear && r < FB)
{
  float SI = max(SwellIn, SwellNear);
  float SF = max(SwellFar, SI + 1.0);
  float QW = SF - SI;
  float tq = saturate((r - SI) / QW);
  float eq = tq * tq * tq * (tq * (6.0 * tq - 15.0) + 10.0);
  float A = SwellAmp * eq * r / SF;
  float dA = SwellAmp * (30.0 * tq * tq * (1.0 - tq) * (1.0 - tq) / QW * r + eq) / SF;
  float tv = saturate((r - SwellNear) / max(SwellShadeFull - SwellNear, 1.0));
  float Av = SwellShade * tv * tv * tv * (tv * (6.0 * tv - 15.0) + 10.0);
  float oS, oC;
  sincos(radians(SwellSeed), oS, oC);
  float iq = 1.0 / max(SwellScale, 0.05);
  float d0x = 0.93969262 * oC - 0.34202014 * oS;
  float d0y = 0.93969262 * oS + 0.34202014 * oC;
  float d1x = -0.99619470 * oC - 0.08715574 * oS;
  float d1y = -0.99619470 * oS + 0.08715574 * oC;
  float d2x = -0.25881905 * oC + 0.96592583 * oS;
  float d2y = -0.25881905 * oS - 0.96592583 * oC;
  float d3x = -0.08715574 * oC - 0.99619470 * oS;
  float d3y = -0.08715574 * oS + 0.99619470 * oC;
  float z0, k0, z1, k1, z2, k2, z3, k3;
  sincos(6.2831853 * frac((d0x * x + d0y * y) * iq / 9000.0 + 0.00 - frac(SwellSpeed * Tt / 42.0)), z0, k0);
  sincos(6.2831853 * frac((d1x * x + d1y * y) * iq / 7000.0 + 0.37 - frac(SwellSpeed * Tt / 36.0)), z1, k1);
  sincos(6.2831853 * frac((d2x * x + d2y * y) * iq / 5500.0 + 0.73 - frac(SwellSpeed * Tt / 31.0)), z2, k2);
  sincos(6.2831853 * frac((d3x * x + d3y * y) * iq / 4000.0 + 0.18 - frac(SwellSpeed * Tt / 46.0)), z3, k3);
  float s = (1.00 * z0 + 0.85 * z1 + 0.70 * z2 + 0.40 * z3) / 2.95;
  float kq = 6.2831853 * iq / 2.95;
  float sx = kq * (1.00 * k0 * d0x / 9000.0 + 0.85 * k1 * d1x / 7000.0 + 0.70 * k2 * d2x / 5500.0 + 0.40 * k3 * d3x / 4000.0);
  float sy = kq * (1.00 * k0 * d0y / 9000.0 + 0.85 * k1 * d1y / 7000.0 + 0.70 * k2 * d2y / 5500.0 + 0.40 * k3 * d3y / 4000.0);
  h += A * s;
  gr += dA * s;
  gx += (A + Av) * sx;
  gy += (A + Av) * sy;
}
// retiro detras de la cresta: bk = 1 - S5(FC, FB, r); gradiente de bk * h (mas bk * sombreado del oleaje)
float BW = FB - FC;
float tk = saturate((r - FC) / BW);
float bk = 1.0 - tk * tk * tk * (tk * (6.0 * tk - 15.0) + 10.0);
float dbk = -30.0 * tk * tk * (1.0 - tk) * (1.0 - tk) / BW;
float gxo = bk * (gx + gr * x / rs) + dbk * h * x / rs;
float gyo = bk * (gy + gr * y / rs) + dbk * h * y / rs;
return float4(gxo, gyo, bk * h, saturate(bk * hf));
