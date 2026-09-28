// ChladniHeightVS - M_ChladniFloor_SC. VERTEX SHADER -> Transform (Local->World, vector) -> WPO. Salida (0, 0, h) en cm
// GENERADO por scripts/gen_chladni_material.py: NO editar a mano (se pisa). Plan: docs/PLAN-SALAR-CHLADNI-2026-09-28.md
// Modos DESPLEGADOS, sin arreglos ni bucles (gotcha 399); hash sin seno (gotcha 481). Cuerpo de un Custom: termina en return.
// NODO  MaterialExpressionCustom  Description "ChladniHeightVS"  OutputType CMOT_Float3
// ENTRADAS (36, en este orden):
//   1  LP         float3  LocalPosition, pin XYZ  posicion del vertice (cm, espacio del actor)
//   2  Part       float   ScalarParameter Part  0 piso, 1 cielo
//   3  Sym        float   ScalarParameter Sym
//   4  Kr         float   ScalarParameter Kr
//   5  BaseW      float   ScalarParameter BaseW
//   6  PlateR     float   ScalarParameter PlateR
//   7  CenterX    float   ScalarParameter CenterX
//   8  Calm       float   ScalarParameter Calm
//   9  Warp       float   ScalarParameter Warp
//  10  ReliefH    float   ScalarParameter ReliefH
//  11  ReliefW    float   ScalarParameter ReliefW
//  12  SwellH     float   ScalarParameter SwellH
//  13  SwellW     float   ScalarParameter SwellW
//  14  EdgeIn     float   ScalarParameter EdgeIn
//  15  Geo        float   ScalarParameter Geo
//  16  GeoFreq    float   ScalarParameter GeoFreq
//  17  Round      float   ScalarParameter Round
//  18  Sharp      float   ScalarParameter Sharp
//  19  VibAmp     float   ScalarParameter VibAmp
//  20  Order      float   ScalarParameter Order
//  21  W0         float   ScalarParameter W0
//  22  W1         float   ScalarParameter W1
//  23  W2         float   ScalarParameter W2
//  24  W3         float   ScalarParameter W3
//  25  W4         float   ScalarParameter W4
//  26  W5         float   ScalarParameter W5
//  27  W6         float   ScalarParameter W6
//  28  W7         float   ScalarParameter W7
//  29  V0         float   ScalarParameter V0
//  30  V1         float   ScalarParameter V1
//  31  V2         float   ScalarParameter V2
//  32  V3         float   ScalarParameter V3
//  33  V4         float   ScalarParameter V4
//  34  V5         float   ScalarParameter V5
//  35  V6         float   ScalarParameter V6
//  36  V7         float   ScalarParameter V7
// --------------------------------------------------------------------------------------------------------
if (Part > 0.5) { return float3(0.0, 0.0, 0.0); }
const float PI = 3.14159265;
float R = max(PlateR, 1.0);
float iR = 1.0 / R;
float calm = Calm * iR;
float ws = max(BaseW + W0 + W1 + W2 + W3 + W4 + W5 + W6 + W7, 0.001);
float act = Order + V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;
float rk = 1.0 - clamp(Round, 0.02, 0.9);              // triangular redondeada: 1 - Round
float irk = 1.0 / asin(rk);
[branch] if (act < 0.001) { return float3(0.0, 0.0, 0.0); }
float2 p = LP.xy;
float2 dq = (p - float2(CenterX, 0.0)) * iR;
float rp = length(dq);
float thp = atan2(dq.y, dq.x);
float rpJ = rp + 0.07 * (sin(3.0 * thp + 1.2) + 0.6 * sin(7.0 * thp + 0.4));   // borde irregular
[branch] if (rp > 1.3) { return float3(0.0, 0.0, 0.0); }
float2 q0A = (p - float2(CenterX, 0.0)) * iR;
float2 qA = q0A + Warp * 0.045 * float2(sin(q0A.y * 4.1 + 1.3) + 0.6 * sin(q0A.x * 7.3 - q0A.y * 2.2 + 0.4), sin(q0A.x * 3.7 + 2.1) + 0.6 * sin(q0A.y * 6.9 + q0A.x * 2.6 + 1.7));
float rA = length(qA);
float thA = atan2(qA.y, qA.x);
float onA = smoothstep(calm * 0.6, calm * 1.4, rA);
float rqA = max(max(max(qA.x * 0.00000 + qA.y * 1.00000, qA.x * -0.95106 + qA.y * 0.30902), max(qA.x * -0.58779 + qA.y * -0.80902, qA.x * 0.58779 + qA.y * -0.80902)), qA.x * 0.95106 + qA.y * 0.30902) * 1.23607;
float rgA = lerp(rA, rqA, Geo);
float FA = BaseW * lerp(cos(PI * Kr * rgA), asin(rk * cos(PI * Kr * rgA)) * irk, Geo);
float VbA = 0.0;
[branch] if (W0 > 0.001 || V0 > 0.001) { float mc = cos(PI * Kr * 1.0000 * rgA) * cos(Sym * 1.0 * thA + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qA.x * 1.00000 + qA.y * 0.00000) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qA.x * 0.30902 + qA.y * 0.95106) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qA.x * -0.80902 + qA.y * 0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qA.x * -0.80902 + qA.y * -0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qA.x * 0.30902 + qA.y * -0.95106) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1870, 0.4420, rA) * onA; FA += W0 * m; VbA += V0 * m; }
[branch] if (W1 > 0.001 || V1 > 0.001) { float mc = cos(PI * Kr * 1.5000 * rgA) * cos(Sym * 2.0 * thA + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qA.x * 0.77495 + qA.y * 0.63202) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qA.x * -0.36162 + qA.y * 0.93233) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qA.x * -0.99844 + qA.y * -0.05581) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qA.x * -0.25546 + qA.y * -0.96682) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qA.x * 0.84056 + qA.y * -0.54172) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2530, 0.5980, rA) * onA; FA += W1 * m; VbA += V1 * m; }
[branch] if (W2 > 0.001 || V2 > 0.001) { float mc = cos(PI * Kr * 2.0000 * rgA) * cos(Sym * 1.0 * thA + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qA.x * 0.49396 + qA.y * 0.86949) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qA.x * -0.67429 + qA.y * 0.73847) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qA.x * -0.91069 + qA.y * -0.41309) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qA.x * 0.11145 + qA.y * -0.99377) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qA.x * 0.97957 + qA.y * -0.20110) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1650, 0.3900, rA) * onA; FA += W2 * m; VbA += V2 * m; }
[branch] if (W3 > 0.001 || V3 > 0.001) { float mc = cos(PI * Kr * 1.2500 * rgA) * cos(Sym * 3.0 * thA + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qA.x * 0.44466 + qA.y * 0.89570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qA.x * -0.71445 + qA.y * 0.69968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qA.x * -0.88622 + qA.y * -0.46327) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qA.x * 0.16674 + qA.y * -0.98600) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qA.x * 0.98927 + qA.y * -0.14611) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.3025, 0.7150, rA) * onA; FA += W3 * m; VbA += V3 * m; }
[branch] if (W4 > 0.001 || V4 > 0.001) { float mc = cos(PI * Kr * 2.5000 * rgA) * cos(Sym * 2.0 * thA + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qA.x * -0.22151 + qA.y * 0.97516) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qA.x * -0.99588 + qA.y * 0.09067) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qA.x * -0.39398 + qA.y * -0.91912) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qA.x * 0.75239 + qA.y * -0.65872) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qA.x * 0.85898 + qA.y * 0.51201) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2200, 0.5200, rA) * onA; FA += W4 * m; VbA += V4 * m; }
[branch] if (W5 > 0.001 || V5 > 0.001) { float mc = cos(PI * Kr * 3.0000 * rgA) * cos(Sym * 1.0 * thA + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qA.x * -0.27559 + qA.y * 0.96128) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qA.x * -0.99939 + qA.y * 0.03495) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qA.x * -0.34207 + qA.y * -0.93968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qA.x * 0.78798 + qA.y * -0.61570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qA.x * 0.82906 + qA.y * 0.55915) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1540, 0.3640, rA) * onA; FA += W5 * m; VbA += V5 * m; }
[branch] if (W6 > 0.001 || V6 > 0.001) { float mc = cos(PI * Kr * 1.7500 * rgA) * cos(Sym * 3.0 * thA + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qA.x * -0.82112 + qA.y * 0.57076) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qA.x * -0.79657 + qA.y * -0.60455) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qA.x * 0.32881 + qA.y * -0.94440) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qA.x * 0.99978 + qA.y * 0.02088) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qA.x * 0.28909 + qA.y * 0.95730) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2750, 0.6500, rA) * onA; FA += W6 * m; VbA += V6 * m; }
[branch] if (W7 > 0.001 || V7 > 0.001) { float mc = cos(PI * Kr * 2.2500 * rgA) * cos(Sym * 2.0 * thA + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qA.x * -0.85169 + qA.y * 0.52404) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qA.x * -0.76158 + qA.y * -0.64807) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qA.x * 0.38101 + qA.y * -0.92457) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qA.x * 0.99706 + qA.y * 0.07665) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qA.x * 0.23521 + qA.y * 0.97194) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2090, 0.4940, rA) * onA; FA += W7 * m; VbA += V7 * m; }
FA /= ws;
VbA *= 1.0 - smoothstep(0.85, 1.05, rA);
float ordL = Order * (1.0 - smoothstep(EdgeIn, 1.08, rpJ)) * smoothstep(calm * 0.8, calm * 1.6, rp);   // centro calmo: sin mandala bajo el usuario
float x = FA / max(SwellW, 0.02);
float lwv = max(ReliefW, 0.3) * 4.0;                              // la loma de geometria: 4 veces mas ancha que la cresta
float2 qgA = (p - float2(CenterX, 0.0)) * iR;
float rgA_ = length(qgA);
float tgA = atan2(qgA.y, qgA.x);
float ogA = smoothstep(calm * 0.6, calm * 1.4, rgA_);
float GA = 0.0;
[branch] if (W0 > 0.001) { float rq = max(max(max(qgA.x * 0.00000 + qgA.y * 1.00000, qgA.x * -0.95106 + qgA.y * 0.30902), max(qgA.x * -0.58779 + qgA.y * -0.80902, qgA.x * 0.58779 + qgA.y * -0.80902)), qgA.x * 0.95106 + qgA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W0 * smoothstep(0.1870, 0.4420, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W1 > 0.001) { float rq = max(max(max(qgA.x * -0.30902 + qgA.y * 0.95106, qgA.x * -1.00000 + qgA.y * 0.00000), max(qgA.x * -0.30902 + qgA.y * -0.95106, qgA.x * 0.80902 + qgA.y * -0.58779)), qgA.x * 0.80902 + qgA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W1 * smoothstep(0.2530, 0.5980, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W2 > 0.001) { float rq = max(max(max(qgA.x * -0.30902 + qgA.y * 0.95106, qgA.x * -1.00000 + qgA.y * 0.00000), max(qgA.x * -0.30902 + qgA.y * -0.95106, qgA.x * 0.80902 + qgA.y * -0.58779)), qgA.x * 0.80902 + qgA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W2 * smoothstep(0.1650, 0.3900, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W3 > 0.001) { float rq = max(max(max(qgA.x * 0.00000 + qgA.y * 1.00000, qgA.x * -0.95106 + qgA.y * 0.30902), max(qgA.x * -0.58779 + qgA.y * -0.80902, qgA.x * 0.58779 + qgA.y * -0.80902)), qgA.x * 0.95106 + qgA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.2500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W3 * smoothstep(0.3025, 0.7150, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W4 > 0.001) { float rq = max(max(max(qgA.x * -0.30902 + qgA.y * 0.95106, qgA.x * -1.00000 + qgA.y * 0.00000), max(qgA.x * -0.30902 + qgA.y * -0.95106, qgA.x * 0.80902 + qgA.y * -0.58779)), qgA.x * 0.80902 + qgA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W4 * smoothstep(0.2200, 0.5200, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W5 > 0.001) { float rq = max(max(max(qgA.x * 0.00000 + qgA.y * 1.00000, qgA.x * -0.95106 + qgA.y * 0.30902), max(qgA.x * -0.58779 + qgA.y * -0.80902, qgA.x * 0.58779 + qgA.y * -0.80902)), qgA.x * 0.95106 + qgA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 3.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 3.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W5 * smoothstep(0.1540, 0.3640, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W6 > 0.001) { float rq = max(max(max(qgA.x * -0.30902 + qgA.y * 0.95106, qgA.x * -1.00000 + qgA.y * 0.00000), max(qgA.x * -0.30902 + qgA.y * -0.95106, qgA.x * 0.80902 + qgA.y * -0.58779)), qgA.x * 0.80902 + qgA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.7500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.7500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W6 * smoothstep(0.2750, 0.6500, rgA_) * ogA; GA = max(GA, c); }
[branch] if (W7 > 0.001) { float rq = max(max(max(qgA.x * 0.00000 + qgA.y * 1.00000, qgA.x * -0.95106 + qgA.y * 0.30902), max(qgA.x * -0.58779 + qgA.y * -0.80902, qgA.x * 0.58779 + qgA.y * -0.80902)), qgA.x * 0.95106 + qgA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 2.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.2500 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lwv), Sharp) * W7 * smoothstep(0.2090, 0.4940, rgA_) * ogA; GA = max(GA, c); }
float h = SwellH * ordL * lerp(exp(-x * x), GA, Geo) + VibAmp * VbA;   // solo la loma SUAVE: la cresta fina va por pixel
return float3(0.0, 0.0, h);
