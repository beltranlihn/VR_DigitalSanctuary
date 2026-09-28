// ValleyHeightVS - M_BreathValley_SC, VERTEX SHADER -> Transform (Local->World, vector) -> WPO.  v2 (revision 2026-09-28)
// Plan: docs/PLAN-VALLE-ENTERING-2026-09-27.md. Solo la ALTURA h (una evaluacion). Espacio LOCAL, cm.
// Tres capas radiales (colinas medias que respiran, anillo + colinas lejanas, oleaje viajero) con rampas QUINTICAS (C2).
// El oleaje mueve la GEOMETRIA solo en la capa lejana (desde SwellIn): en el llano no hay bordes de oclusion.
// Sin bucles ni arreglos (gotcha 399): las 4 dunas y las 4 olas van escritas una por una.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "ValleyHeightVS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = (0, 0, h): desplazamiento LOCAL en cm. Part 1 (cielo) o PerfMode 1/3 -> (0, 0, 0).
//       -> Transform (vector, Local -> World) -> World Position Offset.
// ENTRADAS (29, en este orden; ValleyGradVS tiene las MISMAS 29 en el mismo orden, mas 2 al final):
//   1  LP          float3  LocalPosition, pin XYZ      posicion del vertice en el espacio del actor (cm); el disco es plano (z = 0)
//   2  Part        float   ScalarParameter Part        0 suelo, 1 cielo (lo pone el Construction Script)
//   3  PerfMode    float   ScalarParameter PerfMode    banco: 1 y 3 = vertices baratos (WPO 0)
//   4  HillAmp     float   ScalarParameter HillAmp     2200 cm (alto de las colinas medias)
//   5  HillScale   float   ScalarParameter HillScale   8 (multiplica las longitudes de onda de las dunas: 100-240 m)
//   6  HillSeed    float   ScalarParameter HillSeed    63 (grados; gira el campo de colinas medias)
//   7  HillNear    float   ScalarParameter HillNear    4500 cm (las colinas medias empiezan)
//   8  HillFull    float   ScalarParameter HillFull    12000 cm (colinas medias plenas)
//   9  HillFade    float   ScalarParameter HillFade    19000 cm (empiezan a apagarse)
//  10  HillEnd     float   ScalarParameter HillEnd     26000 cm (apagadas; el codigo usa max(HillEnd, HillFade + 1))
//  11  DuneLow     float   ScalarParameter DuneLow     -0.35 (umbral de la loma: por debajo, llano)
//  12  DuneHigh    float   ScalarParameter DuneHigh    1.2
//  13  FarBase     float   ScalarParameter FarBase     2600 cm (anillo lejano: garantia del horizonte)
//  14  FarAmp      float   ScalarParameter FarAmp      5500 cm (colinas lejanas sobre el anillo)
//  15  FarScale    float   ScalarParameter FarScale    22 (longitudes de onda lejanas: 275-660 m)
//  16  FarSeed     float   ScalarParameter FarSeed     151 (grados)
//  17  FarIn       float   ScalarParameter FarIn       28000 cm (empieza la capa lejana)
//  18  FarFull     float   ScalarParameter FarFull     40000 cm (colinas lejanas plenas)
//  19  FarCrest    float   ScalarParameter FarCrest    47000 cm (cresta del anillo)
//  20  FarBack     float   ScalarParameter FarBack     59000 cm (todo vale 0 desde aqui: borde de la malla oculto)
//  21  SwellAmp    float   ScalarParameter SwellAmp    1880 cm (oleaje geometrico: amplitud a SwellFar; mas lejos crece con r)
//  22  SwellNear   float   ScalarParameter SwellNear   1500 cm (nada se mueve ni cambia de sombreado a menos de esto)
//  23  SwellIn     float   ScalarParameter SwellIn     28000 cm (el oleaje GEOMETRICO empieza aqui, sobre el anillo lejano)
//  24  SwellFar    float   ScalarParameter SwellFar    40000 cm (desde aqui amplitud ANGULAR constante SwellAmp/SwellFar)
//  25  SwellScale  float   ScalarParameter SwellScale  2.5 (multiplica las longitudes de onda del oleaje: 100-225 m; menos facetea la silueta)
//  26  SwellSpeed  float   ScalarParameter SwellSpeed  1 (multiplica la frecuencia: periodos 31-46 s); fijar y dejar
//  27  SwellSeed   float   ScalarParameter SwellSeed   0 (grados; gira las 4 direcciones del oleaje)
//  28  MorphAmt    float   ScalarParameter MorphAmt    0.15 (respiracion de la amplitud de cada duna media, en su lugar)
//  29  MorphSpeed  float   ScalarParameter MorphSpeed  1 (periodos 41-83 s); fijar y dejar
// TIEMPO: se lee View.GameTime adentro (uniforme fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
//         Las fases del oleaje y de la respiracion se reducen con frac (en vueltas) ANTES del sin:
//         argumento acotado en Adreno aunque la sesion dure horas.
// RAMAS: cada capa va en un if [branch] por radio (coherente: la malla va anillo por anillo). Fuera de su banda la
//        capa vale 0 exacto con derivada 0 (la quintica es plana en sus extremos): saltearla no cambia nada.
//        El limite de la rama de colinas es HE = max(HillEnd, HillFade + 1): con HillEnd < HillFade la rampa de
//        apagado se estira hasta HE en lugar de cortar la capa (sin acantilado).
// REGLAS: material en MFPM_Full_MaterialExpressionOnly; sin bucles ni arreglos (gotcha 399, Adreno).
//         La h tiene que ser IDENTICA a la de ValleyGradVS: si se toca una cuenta, se toca en las dos.
// CONTROL: docs/PLAN-VALLE-ENTERING-2026-09-27.md, seccion 12. Cableado completo: Valley_CABLEADO.md.
// --------------------------------------------------------------------------------------------------------
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float3(0.0, 0.0, 0.0); }
float Tt = View.GameTime;
float x = LP.x;
float y = LP.y;
float r = sqrt(x * x + y * y);
float h = 0.0;
float FC = max(FarCrest, FarIn + 1.0);
float FB = max(FarBack, FC + 1.0);
float HE = max(HillEnd, HillFade + 1.0);
float SI = max(SwellIn, SwellNear);
// ---- capa 1: colinas medias (banda polar HillNear..HE), dunas con umbral: llanos entre lomas. La amplitud de cada
// duna respira con su periodo (uniforme por cuadro); se calcula DENTRO de la rama, con la fase reducida con frac.
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
  float sig = (m0 * sin(ax0 * x + ay0 * y + 0.0) + m1 * sin(ax1 * x + ay1 * y + 1.7) + m2 * sin(ax2 * x + ay2 * y + 4.1) + m3 * sin(ax3 * x + ay3 * y + 2.9)) / 2.65;
  float tf = saturate((sig - DuneLow) / max(DuneHigh - DuneLow, 0.01));
  float ta = saturate((r - HillNear) / max(HillFull - HillNear, 1.0));
  float tb = saturate((r - HillFade) / (HE - HillFade));
  float ea = ta * ta * ta * (ta * (6.0 * ta - 15.0) + 10.0);
  float eb = 1.0 - tb * tb * tb * (tb * (6.0 * tb - 15.0) + 10.0);
  h += HillAmp * ea * eb * tf * tf * tf * (tf * (6.0 * tf - 15.0) + 10.0);
}
// ---- capa 2: anillo lejano (tapa el horizonte) + colinas lejanas encima (no respiran: las mueve el oleaje)
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
  float sgF = (1.00 * sin(bx0 * x + by0 * y + 0.0) + 0.75 * sin(bx1 * x + by1 * y + 1.7) + 0.55 * sin(bx2 * x + by2 * y + 4.1) + 0.35 * sin(bx3 * x + by3 * y + 2.9)) / 2.65;
  float tl = saturate((sgF + 0.7) / 1.9);
  float tr = saturate((r - FarIn) / (FC - FarIn));
  float te = saturate((r - FarIn) / max(FarFull - FarIn, 1.0));
  float er = tr * tr * tr * (tr * (6.0 * tr - 15.0) + 10.0);
  float ee = te * te * te * (te * (6.0 * te - 15.0) + 10.0);
  h += FarBase * er + FarAmp * ee * tl * tl * tl * (tl * (6.0 * tl - 15.0) + 10.0);
}
// ---- capa 3: oleaje viajero (4 ondas planas). GEOMETRIA solo desde SI = max(SwellIn, SwellNear), sobre el anillo
// lejano; amplitud angular constante desde SwellFar. (El sombreado del oleaje en el llano va solo en ValleyGradVS.)
[branch]
if (r > SI && r < FB)
{
  float SF = max(SwellFar, SI + 1.0);
  float tq = saturate((r - SI) / (SF - SI));
  float A = SwellAmp * tq * tq * tq * (tq * (6.0 * tq - 15.0) + 10.0) * r / SF;
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
  float o0 = 6.2831853 * frac((d0x * x + d0y * y) * iq / 9000.0 + 0.00 - frac(SwellSpeed * Tt / 42.0));
  float o1 = 6.2831853 * frac((d1x * x + d1y * y) * iq / 7000.0 + 0.37 - frac(SwellSpeed * Tt / 36.0));
  float o2 = 6.2831853 * frac((d2x * x + d2y * y) * iq / 5500.0 + 0.73 - frac(SwellSpeed * Tt / 31.0));
  float o3 = 6.2831853 * frac((d3x * x + d3y * y) * iq / 4000.0 + 0.18 - frac(SwellSpeed * Tt / 46.0));
  h += A * (1.00 * sin(o0) + 0.85 * sin(o1) + 0.70 * sin(o2) + 0.40 * sin(o3)) / 2.95;
}
// retiro detras de la cresta: todo vale 0 desde FarBack (el borde de la malla queda oculto)
float tk = saturate((r - FC) / (FB - FC));
h *= 1.0 - tk * tk * tk * (tk * (6.0 * tk - 15.0) + 10.0);
return float3(0.0, 0.0, h);
