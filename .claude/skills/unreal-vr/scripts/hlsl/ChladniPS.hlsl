// ChladniPS - M_ChladniFloor_SC. PIXEL SHADER -> Emissive Color (lineal; MobileHDR off: sin tonemapper)
// GENERADO por scripts/gen_chladni_material.py: NO editar a mano (se pisa). Plan: docs/PLAN-SALAR-CHLADNI-2026-09-28.md
// Modos DESPLEGADOS, sin arreglos ni bucles (gotcha 399); hash sin seno (gotcha 481). Cuerpo de un Custom: termina en return.
// NODO  MaterialExpressionCustom  Description "ChladniPS"  OutputType CMOT_Float3
// ENTRADAS (77, en este orden):
//   1  LPi        float3  VertexInterpolator_1  posicion local interpolada (sin el WPO)
//   2  CamVec     float3  CameraVector  del punto hacia la camara (mundo)
//   3  Dist       float   Distance(AbsoluteWorldPosition, CameraPositionWS)  distancia real a la camara (cm)
//   4  SunDir     float3  preshader D(SunAz, SunEl)  hacia el sol (mundo)
//   5  SaltTex    texture TextureObjectParameter SaltTex  poligonos del salar horneados (gen_salt_cells.py)
//   6  SandTex    texture TextureObjectParameter SandTex  arena horneada (gen_sand_texture.py)
//   7  Part       float   ScalarParameter Part
//   8  Sym        float   ScalarParameter Sym
//   9  Kr         float   ScalarParameter Kr
//  10  BaseW      float   ScalarParameter BaseW
//  11  PlateR     float   ScalarParameter PlateR
//  12  CenterX    float   ScalarParameter CenterX
//  13  Calm       float   ScalarParameter Calm
//  14  Warp       float   ScalarParameter Warp
//  15  ReliefH    float   ScalarParameter ReliefH
//  16  ReliefW    float   ScalarParameter ReliefW
//  17  SwellH     float   ScalarParameter SwellH
//  18  SwellW     float   ScalarParameter SwellW
//  19  EdgeIn     float   ScalarParameter EdgeIn
//  20  Geo        float   ScalarParameter Geo
//  21  GeoFreq    float   ScalarParameter GeoFreq
//  22  Round      float   ScalarParameter Round
//  23  Sharp      float   ScalarParameter Sharp
//  24  VibAmp     float   ScalarParameter VibAmp
//  25  Order      float   ScalarParameter Order
//  26  W0         float   ScalarParameter W0
//  27  W1         float   ScalarParameter W1
//  28  W2         float   ScalarParameter W2
//  29  W3         float   ScalarParameter W3
//  30  W4         float   ScalarParameter W4
//  31  W5         float   ScalarParameter W5
//  32  W6         float   ScalarParameter W6
//  33  W7         float   ScalarParameter W7
//  34  V0         float   ScalarParameter V0
//  35  V1         float   ScalarParameter V1
//  36  V2         float   ScalarParameter V2
//  37  V3         float   ScalarParameter V3
//  38  V4         float   ScalarParameter V4
//  39  V5         float   ScalarParameter V5
//  40  V6         float   ScalarParameter V6
//  41  V7         float   ScalarParameter V7
//  42  SaltLit    float3  VectorParameter SaltLit
//  43  SaltShade  float3  VectorParameter SaltShade
//  44  FlatTone   float   ScalarParameter FlatTone
//  45  LightGain  float   ScalarParameter LightGain
//  46  PolyH      float   ScalarParameter PolyH
//  47  PolyKeep   float   ScalarParameter PolyKeep
//  48  PolyW      float   ScalarParameter PolyW
//  49  CellSize   float   ScalarParameter CellSize
//  50  SaltNoise  float   ScalarParameter SaltNoise
//  51  Wet        float   ScalarParameter Wet
//  52  Grain      float   ScalarParameter Grain
//  53  GrainSize  float   ScalarParameter GrainSize
//  54  Granite    float   ScalarParameter Granite
//  55  SkyTop     float3  VectorParameter SkyTop
//  56  SkyMid     float3  VectorParameter SkyMid
//  57  SkyHor     float3  VectorParameter SkyHor
//  58  SunCol     float3  VectorParameter SunCol
//  59  SunSize    float   ScalarParameter SunSize
//  60  SunGlow    float   ScalarParameter SunGlow
//  61  Haze       float   ScalarParameter Haze
//  62  FogDist    float   ScalarParameter FogDist
//  63  Dither     float   ScalarParameter Dither
//  64  WormShadow float   ScalarParameter WormShadow
//  65  ShadowElev float   ScalarParameter ShadowElev
//  66  ShadowSoft float   ScalarParameter ShadowSoft
//  67  WormGlow   float   ScalarParameter WormGlow
//  68  WormR      float   ScalarParameter WormR
//  69  WormCol    float3  VectorParameter WormCol
//  70  WS0        float3  VectorParameter WS0
//  71  WS1        float3  VectorParameter WS1
//  72  WS2        float3  VectorParameter WS2
//  73  WS3        float3  VectorParameter WS3
//  74  WS4        float3  VectorParameter WS4
//  75  WS5        float3  VectorParameter WS5
//  76  WS6        float3  VectorParameter WS6
//  77  WS7        float3  VectorParameter WS7
// --------------------------------------------------------------------------------------------------------
float sunR = max(SunSize, 0.5) * 0.0174533;
float3 Vw = -normalize(CamVec);                     // de la camara hacia el punto
[branch] if (Part > 0.5) {
  float skyC_e = Vw.z;
  float3 skyC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, skyC_e));
  skyC = lerp(SkyHor, skyC, smoothstep(-0.03, 0.26, skyC_e));
  float skyC_a = acos(clamp(dot(Vw, SunDir), -1.0, 1.0));
  skyC += SunCol * exp(-skyC_a / (sunR * 2.2)) * SunGlow * 0.3;
  skyC = lerp(skyC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, skyC_a)) * 0.92);
  skyC = lerp(skyC, SkyHor, exp(-abs(skyC_e) / 0.03) * Haze * 0.7);
  return skyC;
}
const float PI = 3.14159265;
float R = max(PlateR, 1.0);
float iR = 1.0 / R;
float calm = Calm * iR;
float ws = max(BaseW + W0 + W1 + W2 + W3 + W4 + W5 + W6 + W7, 0.001);
float act = Order + V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;
float rk = 1.0 - clamp(Round, 0.02, 0.9);              // triangular redondeada: 1 - Round
float irk = 1.0 / asin(rk);
float2 p = LPi.xy;
float fp = length(fwidth(p));                        // cm por pixel (fuera de ramas)
float2 slope = float2(0.0, 0.0);
float crest = 0.0;
float2 dq = (p - float2(CenterX, 0.0)) * iR;
float rp = length(dq);
float thp = atan2(dq.y, dq.x);
float rpJ = rp + 0.07 * (sin(3.0 * thp + 1.2) + 0.6 * sin(7.0 * thp + 0.4));   // borde irregular
float ordP = Order * (1.0 - smoothstep(EdgeIn, 1.08, rpJ));                 // donde hay mandala (centro calmo incluido): sin poligonos
float ordL = ordP * smoothstep(calm * 0.8, calm * 1.6, rp);
// relieve del mandala + ola: la MISMA altura que ChladniHeightVS, con su pendiente por diferencias finitas
[branch] if (act > 0.001 && rp < 1.3) {
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
  float2 q0B = (p + float2(2.0, 0.0) - float2(CenterX, 0.0)) * iR;
  float2 qB = q0B + Warp * 0.045 * float2(sin(q0B.y * 4.1 + 1.3) + 0.6 * sin(q0B.x * 7.3 - q0B.y * 2.2 + 0.4), sin(q0B.x * 3.7 + 2.1) + 0.6 * sin(q0B.y * 6.9 + q0B.x * 2.6 + 1.7));
  float rB = length(qB);
  float thB = atan2(qB.y, qB.x);
  float onB = smoothstep(calm * 0.6, calm * 1.4, rB);
  float rqB = max(max(max(qB.x * 0.00000 + qB.y * 1.00000, qB.x * -0.95106 + qB.y * 0.30902), max(qB.x * -0.58779 + qB.y * -0.80902, qB.x * 0.58779 + qB.y * -0.80902)), qB.x * 0.95106 + qB.y * 0.30902) * 1.23607;
  float rgB = lerp(rB, rqB, Geo);
  float FB = BaseW * lerp(cos(PI * Kr * rgB), asin(rk * cos(PI * Kr * rgB)) * irk, Geo);
  float VbB = 0.0;
  [branch] if (W0 > 0.001 || V0 > 0.001) { float mc = cos(PI * Kr * 1.0000 * rgB) * cos(Sym * 1.0 * thB + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qB.x * 1.00000 + qB.y * 0.00000) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qB.x * 0.30902 + qB.y * 0.95106) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qB.x * -0.80902 + qB.y * 0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qB.x * -0.80902 + qB.y * -0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qB.x * 0.30902 + qB.y * -0.95106) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1870, 0.4420, rB) * onB; FB += W0 * m; VbB += V0 * m; }
  [branch] if (W1 > 0.001 || V1 > 0.001) { float mc = cos(PI * Kr * 1.5000 * rgB) * cos(Sym * 2.0 * thB + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qB.x * 0.77495 + qB.y * 0.63202) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qB.x * -0.36162 + qB.y * 0.93233) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qB.x * -0.99844 + qB.y * -0.05581) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qB.x * -0.25546 + qB.y * -0.96682) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qB.x * 0.84056 + qB.y * -0.54172) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2530, 0.5980, rB) * onB; FB += W1 * m; VbB += V1 * m; }
  [branch] if (W2 > 0.001 || V2 > 0.001) { float mc = cos(PI * Kr * 2.0000 * rgB) * cos(Sym * 1.0 * thB + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qB.x * 0.49396 + qB.y * 0.86949) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qB.x * -0.67429 + qB.y * 0.73847) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qB.x * -0.91069 + qB.y * -0.41309) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qB.x * 0.11145 + qB.y * -0.99377) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qB.x * 0.97957 + qB.y * -0.20110) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1650, 0.3900, rB) * onB; FB += W2 * m; VbB += V2 * m; }
  [branch] if (W3 > 0.001 || V3 > 0.001) { float mc = cos(PI * Kr * 1.2500 * rgB) * cos(Sym * 3.0 * thB + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qB.x * 0.44466 + qB.y * 0.89570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qB.x * -0.71445 + qB.y * 0.69968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qB.x * -0.88622 + qB.y * -0.46327) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qB.x * 0.16674 + qB.y * -0.98600) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qB.x * 0.98927 + qB.y * -0.14611) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.3025, 0.7150, rB) * onB; FB += W3 * m; VbB += V3 * m; }
  [branch] if (W4 > 0.001 || V4 > 0.001) { float mc = cos(PI * Kr * 2.5000 * rgB) * cos(Sym * 2.0 * thB + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qB.x * -0.22151 + qB.y * 0.97516) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qB.x * -0.99588 + qB.y * 0.09067) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qB.x * -0.39398 + qB.y * -0.91912) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qB.x * 0.75239 + qB.y * -0.65872) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qB.x * 0.85898 + qB.y * 0.51201) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2200, 0.5200, rB) * onB; FB += W4 * m; VbB += V4 * m; }
  [branch] if (W5 > 0.001 || V5 > 0.001) { float mc = cos(PI * Kr * 3.0000 * rgB) * cos(Sym * 1.0 * thB + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qB.x * -0.27559 + qB.y * 0.96128) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qB.x * -0.99939 + qB.y * 0.03495) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qB.x * -0.34207 + qB.y * -0.93968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qB.x * 0.78798 + qB.y * -0.61570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qB.x * 0.82906 + qB.y * 0.55915) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1540, 0.3640, rB) * onB; FB += W5 * m; VbB += V5 * m; }
  [branch] if (W6 > 0.001 || V6 > 0.001) { float mc = cos(PI * Kr * 1.7500 * rgB) * cos(Sym * 3.0 * thB + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qB.x * -0.82112 + qB.y * 0.57076) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qB.x * -0.79657 + qB.y * -0.60455) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qB.x * 0.32881 + qB.y * -0.94440) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qB.x * 0.99978 + qB.y * 0.02088) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qB.x * 0.28909 + qB.y * 0.95730) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2750, 0.6500, rB) * onB; FB += W6 * m; VbB += V6 * m; }
  [branch] if (W7 > 0.001 || V7 > 0.001) { float mc = cos(PI * Kr * 2.2500 * rgB) * cos(Sym * 2.0 * thB + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qB.x * -0.85169 + qB.y * 0.52404) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qB.x * -0.76158 + qB.y * -0.64807) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qB.x * 0.38101 + qB.y * -0.92457) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qB.x * 0.99706 + qB.y * 0.07665) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qB.x * 0.23521 + qB.y * 0.97194) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2090, 0.4940, rB) * onB; FB += W7 * m; VbB += V7 * m; }
  FB /= ws;
  VbB *= 1.0 - smoothstep(0.85, 1.05, rB);
  float2 q0C = (p + float2(0.0, 2.0) - float2(CenterX, 0.0)) * iR;
  float2 qC = q0C + Warp * 0.045 * float2(sin(q0C.y * 4.1 + 1.3) + 0.6 * sin(q0C.x * 7.3 - q0C.y * 2.2 + 0.4), sin(q0C.x * 3.7 + 2.1) + 0.6 * sin(q0C.y * 6.9 + q0C.x * 2.6 + 1.7));
  float rC = length(qC);
  float thC = atan2(qC.y, qC.x);
  float onC = smoothstep(calm * 0.6, calm * 1.4, rC);
  float rqC = max(max(max(qC.x * 0.00000 + qC.y * 1.00000, qC.x * -0.95106 + qC.y * 0.30902), max(qC.x * -0.58779 + qC.y * -0.80902, qC.x * 0.58779 + qC.y * -0.80902)), qC.x * 0.95106 + qC.y * 0.30902) * 1.23607;
  float rgC = lerp(rC, rqC, Geo);
  float FC = BaseW * lerp(cos(PI * Kr * rgC), asin(rk * cos(PI * Kr * rgC)) * irk, Geo);
  float VbC = 0.0;
  [branch] if (W0 > 0.001 || V0 > 0.001) { float mc = cos(PI * Kr * 1.0000 * rgC) * cos(Sym * 1.0 * thC + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qC.x * 1.00000 + qC.y * 0.00000) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qC.x * 0.30902 + qC.y * 0.95106) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qC.x * -0.80902 + qC.y * 0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qC.x * -0.80902 + qC.y * -0.58779) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.0000 * 0.5 * (qC.x * 0.30902 + qC.y * -0.95106) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1870, 0.4420, rC) * onC; FC += W0 * m; VbC += V0 * m; }
  [branch] if (W1 > 0.001 || V1 > 0.001) { float mc = cos(PI * Kr * 1.5000 * rgC) * cos(Sym * 2.0 * thC + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qC.x * 0.77495 + qC.y * 0.63202) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qC.x * -0.36162 + qC.y * 0.93233) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qC.x * -0.99844 + qC.y * -0.05581) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qC.x * -0.25546 + qC.y * -0.96682) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.5000 * 0.5 * (qC.x * 0.84056 + qC.y * -0.54172) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2530, 0.5980, rC) * onC; FC += W1 * m; VbC += V1 * m; }
  [branch] if (W2 > 0.001 || V2 > 0.001) { float mc = cos(PI * Kr * 2.0000 * rgC) * cos(Sym * 1.0 * thC + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qC.x * 0.49396 + qC.y * 0.86949) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qC.x * -0.67429 + qC.y * 0.73847) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qC.x * -0.91069 + qC.y * -0.41309) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qC.x * 0.11145 + qC.y * -0.99377) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.0000 * 0.5 * (qC.x * 0.97957 + qC.y * -0.20110) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1650, 0.3900, rC) * onC; FC += W2 * m; VbC += V2 * m; }
  [branch] if (W3 > 0.001 || V3 > 0.001) { float mc = cos(PI * Kr * 1.2500 * rgC) * cos(Sym * 3.0 * thC + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qC.x * 0.44466 + qC.y * 0.89570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qC.x * -0.71445 + qC.y * 0.69968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qC.x * -0.88622 + qC.y * -0.46327) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qC.x * 0.16674 + qC.y * -0.98600) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.2500 * 0.5 * (qC.x * 0.98927 + qC.y * -0.14611) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.3025, 0.7150, rC) * onC; FC += W3 * m; VbC += V3 * m; }
  [branch] if (W4 > 0.001 || V4 > 0.001) { float mc = cos(PI * Kr * 2.5000 * rgC) * cos(Sym * 2.0 * thC + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qC.x * -0.22151 + qC.y * 0.97516) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qC.x * -0.99588 + qC.y * 0.09067) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qC.x * -0.39398 + qC.y * -0.91912) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qC.x * 0.75239 + qC.y * -0.65872) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.5000 * 0.5 * (qC.x * 0.85898 + qC.y * 0.51201) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2200, 0.5200, rC) * onC; FC += W4 * m; VbC += V4 * m; }
  [branch] if (W5 > 0.001 || V5 > 0.001) { float mc = cos(PI * Kr * 3.0000 * rgC) * cos(Sym * 1.0 * thC + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qC.x * -0.27559 + qC.y * 0.96128) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qC.x * -0.99939 + qC.y * 0.03495) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qC.x * -0.34207 + qC.y * -0.93968) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qC.x * 0.78798 + qC.y * -0.61570) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 3.0000 * 0.5 * (qC.x * 0.82906 + qC.y * 0.55915) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.1540, 0.3640, rC) * onC; FC += W5 * m; VbC += V5 * m; }
  [branch] if (W6 > 0.001 || V6 > 0.001) { float mc = cos(PI * Kr * 1.7500 * rgC) * cos(Sym * 3.0 * thC + 1.5708); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qC.x * -0.82112 + qC.y * 0.57076) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qC.x * -0.79657 + qC.y * -0.60455) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qC.x * 0.32881 + qC.y * -0.94440) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qC.x * 0.99978 + qC.y * 0.02088) + 0.2500))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 1.7500 * 0.5 * (qC.x * 0.28909 + qC.y * 0.95730) + 0.2500)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2750, 0.6500, rC) * onC; FC += W6 * m; VbC += V6 * m; }
  [branch] if (W7 > 0.001 || V7 > 0.001) { float mc = cos(PI * Kr * 2.2500 * rgC) * cos(Sym * 2.0 * thC + 0.0000); float mg = 0.0; [branch] if (Geo > 0.001) { mg = (asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qC.x * -0.85169 + qC.y * 0.52404) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qC.x * -0.76158 + qC.y * -0.64807) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qC.x * 0.38101 + qC.y * -0.92457) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qC.x * 0.99706 + qC.y * 0.07665) + 0.0000))) + asin(rk * cos(6.28318 * (Kr * GeoFreq * 2.2500 * 0.5 * (qC.x * 0.23521 + qC.y * 0.97194) + 0.0000)))) * 0.2 * irk; } float m = lerp(mc, mg, Geo) * smoothstep(0.2090, 0.4940, rC) * onC; FC += W7 * m; VbC += V7 * m; }
  FC /= ws;
  VbC *= 1.0 - smoothstep(0.85, 1.05, rC);
  float2 gF = float2(FB - FA, FC - FA) * 0.5;
  float2 gV = float2(VbB - VbA, VbC - VbA) * 0.5;
  float gl = max(length(gF), 1e-5);
  float dcm = FA / gl;                                             // DISTANCIA a la linea nodal (cm): mismo ancho en todas
  float lw = max(ReliefW, 0.3);
  float x = dcm / lw;
  float hs = max(saturate(1.0 - abs(x)), 1e-4);                   // perfil triangular: filo en la cresta
  float hn = pow(hs, Sharp);
  float dhdd = (abs(x) < 1.0) ? (-Sharp * pow(hs, Sharp - 1.0) * sign(dcm) / lw) : 0.0;
  float thin = 1.0 - smoothstep(0.6, 2.5, fp / lw);                 // mas fina que un pixel: se apaga (sin parpadeo)
  float sw = max(SwellW, 0.02);
  float xs = FA / sw;
  float2 slF = ReliefH * ordL * thin * dhdd * (gF / gl) + SwellH * ordL * exp(-xs * xs) * (-2.0 * FA / (sw * sw)) * gF;
  float crF = hn * ordL * thin;
  // el mandala RECTO: union de lineas (pentagonos + rayos); pendiente por diferencias finitas de medio cm
  float2 slG = float2(0.0, 0.0);
  float crG = 0.0;
  [branch] if (Geo > 0.001) {
    float2 qgGA = (p - float2(CenterX, 0.0)) * iR;
    float rgGA_ = length(qgGA);
    float tgGA = atan2(qgGA.y, qgGA.x);
    float ogGA = smoothstep(calm * 0.6, calm * 1.4, rgGA_);
    float GGA = 0.0;
    [branch] if (W0 > 0.001) { float rq = max(max(max(qgGA.x * 0.00000 + qgGA.y * 1.00000, qgGA.x * -0.95106 + qgGA.y * 0.30902), max(qgGA.x * -0.58779 + qgGA.y * -0.80902, qgGA.x * 0.58779 + qgGA.y * -0.80902)), qgGA.x * 0.95106 + qgGA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W0 * smoothstep(0.1870, 0.4420, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W1 > 0.001) { float rq = max(max(max(qgGA.x * -0.30902 + qgGA.y * 0.95106, qgGA.x * -1.00000 + qgGA.y * 0.00000), max(qgGA.x * -0.30902 + qgGA.y * -0.95106, qgGA.x * 0.80902 + qgGA.y * -0.58779)), qgGA.x * 0.80902 + qgGA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W1 * smoothstep(0.2530, 0.5980, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W2 > 0.001) { float rq = max(max(max(qgGA.x * -0.30902 + qgGA.y * 0.95106, qgGA.x * -1.00000 + qgGA.y * 0.00000), max(qgGA.x * -0.30902 + qgGA.y * -0.95106, qgGA.x * 0.80902 + qgGA.y * -0.58779)), qgGA.x * 0.80902 + qgGA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W2 * smoothstep(0.1650, 0.3900, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W3 > 0.001) { float rq = max(max(max(qgGA.x * 0.00000 + qgGA.y * 1.00000, qgGA.x * -0.95106 + qgGA.y * 0.30902), max(qgGA.x * -0.58779 + qgGA.y * -0.80902, qgGA.x * 0.58779 + qgGA.y * -0.80902)), qgGA.x * 0.95106 + qgGA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.2500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W3 * smoothstep(0.3025, 0.7150, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W4 > 0.001) { float rq = max(max(max(qgGA.x * -0.30902 + qgGA.y * 0.95106, qgGA.x * -1.00000 + qgGA.y * 0.00000), max(qgGA.x * -0.30902 + qgGA.y * -0.95106, qgGA.x * 0.80902 + qgGA.y * -0.58779)), qgGA.x * 0.80902 + qgGA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W4 * smoothstep(0.2200, 0.5200, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W5 > 0.001) { float rq = max(max(max(qgGA.x * 0.00000 + qgGA.y * 1.00000, qgGA.x * -0.95106 + qgGA.y * 0.30902), max(qgGA.x * -0.58779 + qgGA.y * -0.80902, qgGA.x * 0.58779 + qgGA.y * -0.80902)), qgGA.x * 0.95106 + qgGA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 3.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 3.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W5 * smoothstep(0.1540, 0.3640, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W6 > 0.001) { float rq = max(max(max(qgGA.x * -0.30902 + qgGA.y * 0.95106, qgGA.x * -1.00000 + qgGA.y * 0.00000), max(qgGA.x * -0.30902 + qgGA.y * -0.95106, qgGA.x * 0.80902 + qgGA.y * -0.58779)), qgGA.x * 0.80902 + qgGA.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.7500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.7500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGA - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W6 * smoothstep(0.2750, 0.6500, rgGA_) * ogGA; GGA = max(GGA, c); }
    [branch] if (W7 > 0.001) { float rq = max(max(max(qgGA.x * 0.00000 + qgGA.y * 1.00000, qgGA.x * -0.95106 + qgGA.y * 0.30902), max(qgGA.x * -0.58779 + qgGA.y * -0.80902, qgGA.x * 0.58779 + qgGA.y * -0.80902)), qgGA.x * 0.95106 + qgGA.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 2.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.2500 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGA - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGA_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W7 * smoothstep(0.2090, 0.4940, rgGA_) * ogGA; GGA = max(GGA, c); }
    float2 qgGB = (p + float2(0.5, 0.0) - float2(CenterX, 0.0)) * iR;
    float rgGB_ = length(qgGB);
    float tgGB = atan2(qgGB.y, qgGB.x);
    float ogGB = smoothstep(calm * 0.6, calm * 1.4, rgGB_);
    float GGB = 0.0;
    [branch] if (W0 > 0.001) { float rq = max(max(max(qgGB.x * 0.00000 + qgGB.y * 1.00000, qgGB.x * -0.95106 + qgGB.y * 0.30902), max(qgGB.x * -0.58779 + qgGB.y * -0.80902, qgGB.x * 0.58779 + qgGB.y * -0.80902)), qgGB.x * 0.95106 + qgGB.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGB - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W0 * smoothstep(0.1870, 0.4420, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W1 > 0.001) { float rq = max(max(max(qgGB.x * -0.30902 + qgGB.y * 0.95106, qgGB.x * -1.00000 + qgGB.y * 0.00000), max(qgGB.x * -0.30902 + qgGB.y * -0.95106, qgGB.x * 0.80902 + qgGB.y * -0.58779)), qgGB.x * 0.80902 + qgGB.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGB - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W1 * smoothstep(0.2530, 0.5980, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W2 > 0.001) { float rq = max(max(max(qgGB.x * -0.30902 + qgGB.y * 0.95106, qgGB.x * -1.00000 + qgGB.y * 0.00000), max(qgGB.x * -0.30902 + qgGB.y * -0.95106, qgGB.x * 0.80902 + qgGB.y * -0.58779)), qgGB.x * 0.80902 + qgGB.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGB - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W2 * smoothstep(0.1650, 0.3900, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W3 > 0.001) { float rq = max(max(max(qgGB.x * 0.00000 + qgGB.y * 1.00000, qgGB.x * -0.95106 + qgGB.y * 0.30902), max(qgGB.x * -0.58779 + qgGB.y * -0.80902, qgGB.x * 0.58779 + qgGB.y * -0.80902)), qgGB.x * 0.95106 + qgGB.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.2500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGB - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W3 * smoothstep(0.3025, 0.7150, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W4 > 0.001) { float rq = max(max(max(qgGB.x * -0.30902 + qgGB.y * 0.95106, qgGB.x * -1.00000 + qgGB.y * 0.00000), max(qgGB.x * -0.30902 + qgGB.y * -0.95106, qgGB.x * 0.80902 + qgGB.y * -0.58779)), qgGB.x * 0.80902 + qgGB.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGB - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W4 * smoothstep(0.2200, 0.5200, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W5 > 0.001) { float rq = max(max(max(qgGB.x * 0.00000 + qgGB.y * 1.00000, qgGB.x * -0.95106 + qgGB.y * 0.30902), max(qgGB.x * -0.58779 + qgGB.y * -0.80902, qgGB.x * 0.58779 + qgGB.y * -0.80902)), qgGB.x * 0.95106 + qgGB.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 3.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 3.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGB - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W5 * smoothstep(0.1540, 0.3640, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W6 > 0.001) { float rq = max(max(max(qgGB.x * -0.30902 + qgGB.y * 0.95106, qgGB.x * -1.00000 + qgGB.y * 0.00000), max(qgGB.x * -0.30902 + qgGB.y * -0.95106, qgGB.x * 0.80902 + qgGB.y * -0.58779)), qgGB.x * 0.80902 + qgGB.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.7500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.7500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGB - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W6 * smoothstep(0.2750, 0.6500, rgGB_) * ogGB; GGB = max(GGB, c); }
    [branch] if (W7 > 0.001) { float rq = max(max(max(qgGB.x * 0.00000 + qgGB.y * 1.00000, qgGB.x * -0.95106 + qgGB.y * 0.30902), max(qgGB.x * -0.58779 + qgGB.y * -0.80902, qgGB.x * 0.58779 + qgGB.y * -0.80902)), qgGB.x * 0.95106 + qgGB.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 2.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.2500 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGB - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGB_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W7 * smoothstep(0.2090, 0.4940, rgGB_) * ogGB; GGB = max(GGB, c); }
    float2 qgGC = (p + float2(0.0, 0.5) - float2(CenterX, 0.0)) * iR;
    float rgGC_ = length(qgGC);
    float tgGC = atan2(qgGC.y, qgGC.x);
    float ogGC = smoothstep(calm * 0.6, calm * 1.4, rgGC_);
    float GGC = 0.0;
    [branch] if (W0 > 0.001) { float rq = max(max(max(qgGC.x * 0.00000 + qgGC.y * 1.00000, qgGC.x * -0.95106 + qgGC.y * 0.30902), max(qgGC.x * -0.58779 + qgGC.y * -0.80902, qgGC.x * 0.58779 + qgGC.y * -0.80902)), qgGC.x * 0.95106 + qgGC.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGC - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W0 * smoothstep(0.1870, 0.4420, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W1 > 0.001) { float rq = max(max(max(qgGC.x * -0.30902 + qgGC.y * 0.95106, qgGC.x * -1.00000 + qgGC.y * 0.00000), max(qgGC.x * -0.30902 + qgGC.y * -0.95106, qgGC.x * 0.80902 + qgGC.y * -0.58779)), qgGC.x * 0.80902 + qgGC.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGC - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W1 * smoothstep(0.2530, 0.5980, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W2 > 0.001) { float rq = max(max(max(qgGC.x * -0.30902 + qgGC.y * 0.95106, qgGC.x * -1.00000 + qgGC.y * 0.00000), max(qgGC.x * -0.30902 + qgGC.y * -0.95106, qgGC.x * 0.80902 + qgGC.y * -0.58779)), qgGC.x * 0.80902 + qgGC.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGC - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W2 * smoothstep(0.1650, 0.3900, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W3 > 0.001) { float rq = max(max(max(qgGC.x * 0.00000 + qgGC.y * 1.00000, qgGC.x * -0.95106 + qgGC.y * 0.30902), max(qgGC.x * -0.58779 + qgGC.y * -0.80902, qgGC.x * 0.58779 + qgGC.y * -0.80902)), qgGC.x * 0.95106 + qgGC.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 1.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.2500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGC - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W3 * smoothstep(0.3025, 0.7150, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W4 > 0.001) { float rq = max(max(max(qgGC.x * -0.30902 + qgGC.y * 0.95106, qgGC.x * -1.00000 + qgGC.y * 0.00000), max(qgGC.x * -0.30902 + qgGC.y * -0.95106, qgGC.x * 0.80902 + qgGC.y * -0.58779)), qgGC.x * 0.80902 + qgGC.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 2.5000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.5000 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGC - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W4 * smoothstep(0.2200, 0.5200, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W5 > 0.001) { float rq = max(max(max(qgGC.x * 0.00000 + qgGC.y * 1.00000, qgGC.x * -0.95106 + qgGC.y * 0.30902), max(qgGC.x * -0.58779 + qgGC.y * -0.80902, qgGC.x * 0.58779 + qgGC.y * -0.80902)), qgGC.x * 0.95106 + qgGC.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 3.0000 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 3.0000 * 0.5) * R; float nA = Sym * 1.0; float a = abs(frac((tgGC - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W5 * smoothstep(0.1540, 0.3640, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W6 > 0.001) { float rq = max(max(max(qgGC.x * -0.30902 + qgGC.y * 0.95106, qgGC.x * -1.00000 + qgGC.y * 0.00000), max(qgGC.x * -0.30902 + qgGC.y * -0.95106, qgGC.x * 0.80902 + qgGC.y * -0.58779)), qgGC.x * 0.80902 + qgGC.y * 0.58779) * 1.23607; float u = rq * (Kr * GeoFreq * 1.7500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 1.7500 * 0.5) * R; float nA = Sym * 3.0; float a = abs(frac((tgGC - 0.31416) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W6 * smoothstep(0.2750, 0.6500, rgGC_) * ogGC; GGC = max(GGC, c); }
    [branch] if (W7 > 0.001) { float rq = max(max(max(qgGC.x * 0.00000 + qgGC.y * 1.00000, qgGC.x * -0.95106 + qgGC.y * 0.30902), max(qgGC.x * -0.58779 + qgGC.y * -0.80902, qgGC.x * 0.58779 + qgGC.y * -0.80902)), qgGC.x * 0.95106 + qgGC.y * 0.30902) * 1.23607; float u = rq * (Kr * GeoFreq * 2.2500 * 0.5); float dr = abs(u - round(u)) / (Kr * GeoFreq * 2.2500 * 0.5) * R; float nA = Sym * 2.0; float a = abs(frac((tgGC - 0.00000) * nA * 0.159155 + 0.5) - 0.5) * 6.28318 / nA; float ds = rgGC_ * R * sin(a); float c = pow(saturate(1.0 - min(dr, ds) / lw), Sharp) * W7 * smoothstep(0.2090, 0.4940, rgGC_) * ogGC; GGC = max(GGC, c); }
    slG = ReliefH * ordL * thin * float2(GGB - GGA, GGC - GGA) * 2.0;
    crG = GGA * ordL * thin;
  }
  slope += lerp(slF, slG, Geo) + VibAmp * gV;
  crest += lerp(crF, crG, Geo);
}
// poligonos del salar (textura periodica de 8 x 8 celdas): el mandala los va borrando
float T8 = max(CellSize, 1.0) * 8.0;
float2 uvC = p / T8;
float tx = 1.0 / 1024.0;
float c0 = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC, 0.0).r;
float cx = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(tx, 0.0), 0.0).r;
float cy = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(0.0, tx), 0.0).r;
float dv = c0 * 0.5 * CellSize;
float2 gdv = float2(cx - c0, cy - c0) * (0.5 * CellSize) / (tx * T8);
float pw = max(PolyW, 0.5);
float xv = dv / pw;
float hsv = max(saturate(1.0 - xv), 1e-4);                           // la cresta del poligono, tambien con filo
float keep = (1.0 - ordP * (1.0 - PolyKeep)) * (1.0 - smoothstep(0.5, 2.5, fp / pw));
float hv = pow(hsv, Sharp) * keep;
float dhdv = (xv < 1.0) ? (-Sharp * pow(hsv, Sharp - 1.0) / pw) : 0.0;
slope += 3.5 * PolyH * keep * dhdv * gdv;
crest += hv * PolyH;
float3 n = normalize(float3(-slope, 1.0));
// luz rasante: el plano queda en FlatTone; lo que mira al sol se entibia y lo demas se enfria
float t = FlatTone + (dot(n, SunDir) - SunDir.z) * LightGain;
float2 nq = p / 38.0;
float2 ni = floor(nq);
float2 nf = frac(nq);
nf = nf * nf * (3.0 - 2.0 * nf);
float3 n00_p = frac(float3((ni).xyx) * 0.1031);
n00_p += dot(n00_p, n00_p.yzx + 33.33);
float n00 = frac((n00_p.x + n00_p.y) * n00_p.z);
float3 n10_p = frac(float3((ni + float2(1.0, 0.0)).xyx) * 0.1031);
n10_p += dot(n10_p, n10_p.yzx + 33.33);
float n10 = frac((n10_p.x + n10_p.y) * n10_p.z);
float3 n01_p = frac(float3((ni + float2(0.0, 1.0)).xyx) * 0.1031);
n01_p += dot(n01_p, n01_p.yzx + 33.33);
float n01 = frac((n01_p.x + n01_p.y) * n01_p.z);
float3 n11_p = frac(float3((ni + float2(1.0, 1.0)).xyx) * 0.1031);
n11_p += dot(n11_p, n11_p.yzx + 33.33);
float n11 = frac((n11_p.x + n11_p.y) * n11_p.z);
float nz = (lerp(lerp(n00, n10, nf.x), lerp(n01, n11, nf.x), nf.y) - 0.5) * SaltNoise * (1.0 - smoothstep(3.0, 12.0, fp));
t += nz * 0.25;
// arena: textura periodica con mipmaps (de lejos se promedia sola), dos lecturas a escalas y giros distintos
float st = max(GrainSize, 1.0);
float3 sA = Texture2DSample(SandTex, SandTexSampler, p / st).rgb;
float2 pr = float2(p.x * 0.8 - p.y * 0.6, p.x * 0.6 + p.y * 0.8);
float3 sB = Texture2DSample(SandTex, SandTexSampler, pr / (st * 2.37)).rgb;
t += ((sA.r - 0.5) * 0.65 + (sB.r - 0.5) * 0.35) * Grain * 1.8;
float3 col = lerp(SaltShade, SaltLit, saturate(t));
// el gusano ASENTADO: sombra larga hacia el lado contrario al sol + reflejo de su color en la sal humeda
float2 sdir = normalize(SunDir.xy + float2(1e-5, 0.0));
float kS = 1.0 / tan(clamp(ShadowElev, 3.0, 80.0) * 0.0174533);
float wr = max(WormR, 1.0);
float shw = 0.0;
float glw = 0.0;
[branch] if (WS0.z > 0.0) { float hl = WS0.z * kS * 0.5; float2 dd = p - (WS0.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS0.z / 400.0)); float2 dg = p - WS0.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS1.z > 0.0) { float hl = WS1.z * kS * 0.5; float2 dd = p - (WS1.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS1.z / 400.0)); float2 dg = p - WS1.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS2.z > 0.0) { float hl = WS2.z * kS * 0.5; float2 dd = p - (WS2.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS2.z / 400.0)); float2 dg = p - WS2.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS3.z > 0.0) { float hl = WS3.z * kS * 0.5; float2 dd = p - (WS3.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS3.z / 400.0)); float2 dg = p - WS3.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS4.z > 0.0) { float hl = WS4.z * kS * 0.5; float2 dd = p - (WS4.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS4.z / 400.0)); float2 dg = p - WS4.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS5.z > 0.0) { float hl = WS5.z * kS * 0.5; float2 dd = p - (WS5.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS5.z / 400.0)); float2 dg = p - WS5.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS6.z > 0.0) { float hl = WS6.z * kS * 0.5; float2 dd = p - (WS6.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS6.z / 400.0)); float2 dg = p - WS6.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
[branch] if (WS7.z > 0.0) { float hl = WS7.z * kS * 0.5; float2 dd = p - (WS7.xy - sdir * hl); float al = dot(dd, sdir); float ac = dd.x * sdir.y - dd.y * sdir.x; float e = al * al / ((hl + wr) * (hl + wr)) + ac * ac / (wr * wr * 1.4); shw = max(shw, exp(-e * 2.0 * ShadowSoft) * saturate(1.0 - WS7.z / 400.0)); float2 dg = p - WS7.xy; glw = max(glw, exp(-dot(dg, dg) / (wr * wr * 5.0))); }
col = lerp(col, SaltShade * 0.8, saturate(WormShadow * shw));
col += WormCol * WormGlow * glw;
col += SunCol * max(t - 0.85, 0.0) * 0.5;
float dk = max(sA.g, sB.g * 0.7);
float lt = sA.b;
col = lerp(col, SaltShade * 0.6, dk * Granite * 0.8);
col = lerp(col, SaltLit * 1.06, lt * Granite * 0.45);
// agua: refleja el cielo en angulo rasante
float cosv = saturate(-Vw.z);
float fres = pow(1.0 - cosv, 5.0) * Wet * (1.0 - min(crest, 1.0) * 0.8);
float3 Rw = reflect(Vw, normalize(lerp(float3(0.0, 0.0, 1.0), n, 0.35)));
float refC_e = Rw.z;
float3 refC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, refC_e));
refC = lerp(SkyHor, refC, smoothstep(-0.03, 0.26, refC_e));
float refC_a = acos(clamp(dot(Rw, SunDir), -1.0, 1.0));
refC += SunCol * exp(-refC_a / (sunR * 2.2)) * SunGlow * 0.3;
refC = lerp(refC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, refC_a)) * 0.92);
refC = lerp(refC, SkyHor, exp(-abs(refC_e) / 0.03) * Haze * 0.7);
col = lerp(col, refC, saturate(fres));
// bruma hacia el cielo del horizonte (distancia REAL: en VR la profundidad de pixel 'nada' al girar)
float3 Hd = normalize(float3(Vw.xy, 0.0001));
float fogC_e = Hd.z;
float3 fogC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, fogC_e));
fogC = lerp(SkyHor, fogC, smoothstep(-0.03, 0.26, fogC_e));
float fogC_a = acos(clamp(dot(Hd, SunDir), -1.0, 1.0));
fogC += SunCol * exp(-fogC_a / (sunR * 2.2)) * SunGlow * 0.3;
fogC = lerp(fogC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, fogC_a)) * 0.92);
fogC = lerp(fogC, SkyHor, exp(-abs(fogC_e) / 0.03) * Haze * 0.7);
col = lerp(col, fogC, (1.0 - exp(-Dist / max(FogDist, 1.0))) * 0.85);
float3 dz_p = frac(float3((floor(Parameters.SvPosition.xy)).xyx) * 0.1031);
dz_p += dot(dz_p, dz_p.yzx + 33.33);
float dz = frac((dz_p.x + dz_p.y) * dz_p.z);
col += (dz - 0.5) * Dither / 255.0;
return col;
