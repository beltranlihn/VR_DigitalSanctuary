// ChladniPS - M_ChladniFloor_SC. PIXEL SHADER -> Emissive Color (lineal; MobileHDR off: sin tonemapper)
// GENERADO por scripts/gen_chladni_material.py: NO editar a mano (se pisa). Plan: docs/PLAN-SALAR-CHLADNI-2026-09-28.md
// Modos DESPLEGADOS, sin arreglos ni bucles (gotcha 399); hash sin seno (gotcha 481). Cuerpo de un Custom: termina en return.
// NODO  MaterialExpressionCustom  Description "ChladniPS"  OutputType CMOT_Float3
// ENTRADAS (66, en este orden):
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
//  42  PerfMode   float   ScalarParameter PerfMode
//  43  PerfForce  float   ScalarParameter PerfForce
//  44  Plain      float   ScalarParameter Plain
//  45  SaltLit    float3  VectorParameter SaltLit
//  46  SaltShade  float3  VectorParameter SaltShade
//  47  FlatTone   float   ScalarParameter FlatTone
//  48  LightGain  float   ScalarParameter LightGain
//  49  PolyH      float   ScalarParameter PolyH
//  50  PolyKeep   float   ScalarParameter PolyKeep
//  51  PolyW      float   ScalarParameter PolyW
//  52  CellSize   float   ScalarParameter CellSize
//  53  SaltNoise  float   ScalarParameter SaltNoise
//  54  Wet        float   ScalarParameter Wet
//  55  Grain      float   ScalarParameter Grain
//  56  GrainSize  float   ScalarParameter GrainSize
//  57  Granite    float   ScalarParameter Granite
//  58  SkyTop     float3  VectorParameter SkyTop
//  59  SkyMid     float3  VectorParameter SkyMid
//  60  SkyHor     float3  VectorParameter SkyHor
//  61  SunCol     float3  VectorParameter SunCol
//  62  SunSize    float   ScalarParameter SunSize
//  63  SunGlow    float   ScalarParameter SunGlow
//  64  Haze       float   ScalarParameter Haze
//  65  FogDist    float   ScalarParameter FogDist
//  66  Dither     float   ScalarParameter Dither
// --------------------------------------------------------------------------------------------------------
float sunR = max(SunSize, 0.5) * 0.0174533;
float3 Vw = -normalize(CamVec);                     // de la camara hacia el punto
[branch] if (Part > 0.5) {
  [branch] if (abs(PerfMode - 5.0) < 0.5) { return SkyMid; }   // banco: cielo plano
  float skyC_e = Vw.z;
  float3 skyC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, skyC_e));
  skyC = lerp(SkyHor, skyC, smoothstep(-0.03, 0.26, skyC_e));
  float skyC_a = acos(clamp(dot(Vw, SunDir), -1.0, 1.0));
  skyC += SunCol * exp(-skyC_a / (sunR * 2.2)) * SunGlow * 0.3;
  skyC = lerp(skyC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, skyC_a)) * 0.92);
  skyC = lerp(skyC, SkyHor, exp(-abs(skyC_e) / 0.03) * Haze * 0.7);
  return skyC;
}
[branch] if (abs(PerfMode - 4.0) < 0.5) { return lerp(SaltShade, SaltLit, FlatTone); }   // banco: piso plano
// piso LISO (el patron apagado, no borrado): el tono del plano + el agua y la bruma, para que siga fundiendose con
// el horizonte. Sin mandala, poligonos, grano ni ola
[branch] if (Plain > 0.5) {
  float3 colP = lerp(SaltShade, SaltLit, FlatTone);
  float fresP = pow(1.0 - saturate(-Vw.z), 5.0) * Wet;
  [branch] if (fresP > 0.002) {
    float3 RwP = reflect(Vw, float3(0.0, 0.0, 1.0));
    float refP_e = RwP.z;
    float3 refP = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, refP_e));
    refP = lerp(SkyHor, refP, smoothstep(-0.03, 0.26, refP_e));
    float refP_a = acos(clamp(dot(RwP, SunDir), -1.0, 1.0));
    refP += SunCol * exp(-refP_a / (sunR * 2.2)) * SunGlow * 0.3;
    refP = lerp(refP, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, refP_a)) * 0.92);
    refP = lerp(refP, SkyHor, exp(-abs(refP_e) / 0.03) * Haze * 0.7);
    colP = lerp(colP, refP, saturate(fresP));
  }
  float3 HdP = normalize(float3(Vw.xy, 0.0001));
  float fogP_e = 0.0;
  float3 fogP = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, fogP_e));
  fogP = lerp(SkyHor, fogP, smoothstep(-0.03, 0.26, fogP_e));
  float fogP_a = acos(clamp(dot(HdP, SunDir), -1.0, 1.0));
  fogP += SunCol * exp(-fogP_a / (sunR * 2.2)) * SunGlow * 0.3;
  fogP = lerp(fogP, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, fogP_a)) * 0.92);
  fogP = lerp(fogP, SkyHor, exp(-abs(fogP_e) / 0.03) * Haze * 0.7);
  colP = lerp(colP, fogP, (1.0 - exp(-Dist / max(FogDist, 1.0))) * 0.85);
  float3 dzP_p = frac(float3((floor(Parameters.SvPosition.xy)).xyx) * 0.1031);
  dzP_p += dot(dzP_p, dzP_p.yzx + 33.33);
  float dzP = frac((dzP_p.x + dzP_p.y) * dzP_p.z);
  return colP + (dzP - 0.5) * Dither / 255.0;
}
[branch] if (PerfForce > 0.5) { Order = 1.0; W0 = 1.0; V0 = 0.0; W1 = 1.0; V1 = 0.0; W2 = 1.0; V2 = 0.0; W3 = 1.0; V3 = 0.0; W4 = 1.0; V4 = 0.0; W5 = 1.0; V5 = 0.0; W6 = 1.0; V6 = 0.0; W7 = 1.0; V7 = 0.0; }
const float PI = 3.14159265;
float R = max(PlateR, 1.0);
float iR = 1.0 / R;
float calm = Calm * iR;
float ws = max(BaseW + W0 + W1 + W2 + W3 + W4 + W5 + W6 + W7, 0.001);
float act = Order + V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;
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
float vsum = V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;
// relieve del mandala + ola: la MISMA altura que ChladniHeightVS, con su pendiente ANALITICA. Donde no hay
// relieve (ordL 0: centro calmo y fuera del borde) y no hay ola, no aporta nada: no se evalua
[branch] if (act > 0.001 && rp < 1.3 && (ordL > 0.0001 || vsum > 0.001) && !(abs(PerfMode - 2.0) < 0.5)) {
  float FAo = 0.0;
  float2 gFo = float2(0.0, 0.0);
  float2 gVo = float2(0.0, 0.0);
  float2 q0 = (p - float2(CenterX, 0.0)) * iR;
  float kw = Warp * 0.045;
  float s1, c1, s2, c2, s3, c3, s4, c4;
  sincos(q0.y * 4.1 + 1.3, s1, c1);
  sincos(q0.x * 7.3 - q0.y * 2.2 + 0.4, s2, c2);
  sincos(q0.x * 3.7 + 2.1, s3, c3);
  sincos(q0.y * 6.9 + q0.x * 2.6 + 1.7, s4, c4);
  float2 q = q0 + kw * float2(s1 + 0.6 * s2, s3 + 0.6 * s4);
  float Jxx = 1.0 + kw * 4.38 * c2;                 // dq.x/dq0.x
  float Jxy = kw * (4.1 * c1 - 1.32 * c2);          // dq.x/dq0.y
  float Jyx = kw * (3.7 * c3 + 1.56 * c4);          // dq.y/dq0.x
  float Jyy = 1.0 + kw * 4.14 * c4;                 // dq.y/dq0.y
  float r = max(length(q), 1e-5);
  float th = atan2(q.y, q.x);
  float onw = max(calm * 0.8, 1e-5);
  float ont = saturate((r - calm * 0.6) / onw);
  float on = ont * ont * (3.0 - 2.0 * ont);
  float don = 6.0 * ont * (1.0 - ont) / onw;
  // anillos: rk_n = PI*Kr*r*n/4, n = 1..12, por suma de angulos
  float ru = PI * Kr * 0.25;
  float rs1, rc1;
  sincos(ru * r, rs1, rc1);
  float rc2 = rc1 * rc1 - rs1 * rs1; float rs2 = rs1 * rc1 + rc1 * rs1;
  float rc3 = rc2 * rc1 - rs2 * rs1; float rs3 = rs2 * rc1 + rc2 * rs1;
  float rc4 = rc3 * rc1 - rs3 * rs1; float rs4 = rs3 * rc1 + rc3 * rs1;
  float rc5 = rc4 * rc1 - rs4 * rs1; float rs5 = rs4 * rc1 + rc4 * rs1;
  float rc6 = rc5 * rc1 - rs5 * rs1; float rs6 = rs5 * rc1 + rc5 * rs1;
  float rc7 = rc6 * rc1 - rs6 * rs1; float rs7 = rs6 * rc1 + rc6 * rs1;
  float rc8 = rc7 * rc1 - rs7 * rs1; float rs8 = rs7 * rc1 + rc7 * rs1;
  float rc9 = rc8 * rc1 - rs8 * rs1; float rs9 = rs8 * rc1 + rc8 * rs1;
  float rc10 = rc9 * rc1 - rs9 * rs1; float rs10 = rs9 * rc1 + rc9 * rs1;
  float rc11 = rc10 * rc1 - rs10 * rs1; float rs11 = rs10 * rc1 + rc10 * rs1;
  float rc12 = rc11 * rc1 - rs11 * rs1; float rs12 = rs11 * rc1 + rc11 * rs1;
  // simetrias: Sym*th*m, m = 1..3 (Chebyshev)
  float as1, ac1;
  sincos(Sym * th, as1, ac1);
  float ac2 = 2.0 * ac1 * ac1 - 1.0; float as2 = 2.0 * as1 * ac1;
  float ac3 = ac1 * (4.0 * ac1 * ac1 - 3.0); float as3 = as1 * (3.0 - 4.0 * as1 * as1);
  float Fa = BaseW * rc4;
  float dFr = -BaseW * ru * 4.0 * rs4;
  float dFt = 0.0;
  float Va = 0.0;
  float dVr = 0.0;
  float dVt = 0.0;
  [branch] if (W0 > 0.001 || V0 > 0.001) { float t = saturate((r - 0.1870) * 3.92157); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 3.92157; float env = S * on; float denv = dS * on + S * don; float cA = rc4; float sA = rs4; float cB = ac1; float sB = as1; float m = cA * cB * env; float mr = (-ru * 4.0 * sA * env + cA * denv) * cB; float mt = -Sym * 1.0 * cA * sB * env; Fa += W0 * m; dFr += W0 * mr; dFt += W0 * mt; Va += V0 * m; dVr += V0 * mr; dVt += V0 * mt; }
  [branch] if (W1 > 0.001 || V1 > 0.001) { float t = saturate((r - 0.2530) * 2.89855); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 2.89855; float env = S * on; float denv = dS * on + S * don; float cA = rc6; float sA = rs6; float cB = (-as2); float sB = ac2; float m = cA * cB * env; float mr = (-ru * 6.0 * sA * env + cA * denv) * cB; float mt = -Sym * 2.0 * cA * sB * env; Fa += W1 * m; dFr += W1 * mr; dFt += W1 * mt; Va += V1 * m; dVr += V1 * mr; dVt += V1 * mt; }
  [branch] if (W2 > 0.001 || V2 > 0.001) { float t = saturate((r - 0.1650) * 4.44444); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 4.44444; float env = S * on; float denv = dS * on + S * don; float cA = rc8; float sA = rs8; float cB = (-as1); float sB = ac1; float m = cA * cB * env; float mr = (-ru * 8.0 * sA * env + cA * denv) * cB; float mt = -Sym * 1.0 * cA * sB * env; Fa += W2 * m; dFr += W2 * mr; dFt += W2 * mt; Va += V2 * m; dVr += V2 * mr; dVt += V2 * mt; }
  [branch] if (W3 > 0.001 || V3 > 0.001) { float t = saturate((r - 0.3025) * 2.42424); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 2.42424; float env = S * on; float denv = dS * on + S * don; float cA = rc5; float sA = rs5; float cB = ac3; float sB = as3; float m = cA * cB * env; float mr = (-ru * 5.0 * sA * env + cA * denv) * cB; float mt = -Sym * 3.0 * cA * sB * env; Fa += W3 * m; dFr += W3 * mr; dFt += W3 * mt; Va += V3 * m; dVr += V3 * mr; dVt += V3 * mt; }
  [branch] if (W4 > 0.001 || V4 > 0.001) { float t = saturate((r - 0.2200) * 3.33333); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 3.33333; float env = S * on; float denv = dS * on + S * don; float cA = rc10; float sA = rs10; float cB = (-as2); float sB = ac2; float m = cA * cB * env; float mr = (-ru * 10.0 * sA * env + cA * denv) * cB; float mt = -Sym * 2.0 * cA * sB * env; Fa += W4 * m; dFr += W4 * mr; dFt += W4 * mt; Va += V4 * m; dVr += V4 * mr; dVt += V4 * mt; }
  [branch] if (W5 > 0.001 || V5 > 0.001) { float t = saturate((r - 0.1540) * 4.76190); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 4.76190; float env = S * on; float denv = dS * on + S * don; float cA = rc12; float sA = rs12; float cB = ac1; float sB = as1; float m = cA * cB * env; float mr = (-ru * 12.0 * sA * env + cA * denv) * cB; float mt = -Sym * 1.0 * cA * sB * env; Fa += W5 * m; dFr += W5 * mr; dFt += W5 * mt; Va += V5 * m; dVr += V5 * mr; dVt += V5 * mt; }
  [branch] if (W6 > 0.001 || V6 > 0.001) { float t = saturate((r - 0.2750) * 2.66667); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 2.66667; float env = S * on; float denv = dS * on + S * don; float cA = rc7; float sA = rs7; float cB = (-as3); float sB = ac3; float m = cA * cB * env; float mr = (-ru * 7.0 * sA * env + cA * denv) * cB; float mt = -Sym * 3.0 * cA * sB * env; Fa += W6 * m; dFr += W6 * mr; dFt += W6 * mt; Va += V6 * m; dVr += V6 * mr; dVt += V6 * mt; }
  [branch] if (W7 > 0.001 || V7 > 0.001) { float t = saturate((r - 0.2090) * 3.50877); float S = t * t * (3.0 - 2.0 * t); float dS = 6.0 * t * (1.0 - t) * 3.50877; float env = S * on; float denv = dS * on + S * don; float cA = rc9; float sA = rs9; float cB = ac2; float sB = as2; float m = cA * cB * env; float mr = (-ru * 9.0 * sA * env + cA * denv) * cB; float mt = -Sym * 2.0 * cA * sB * env; Fa += W7 * m; dFr += W7 * mr; dFt += W7 * mt; Va += V7 * m; dVr += V7 * mr; dVt += V7 * mt; }
  float iws = 1.0 / ws;
  Fa *= iws; dFr *= iws; dFt *= iws;
  float ft = saturate((r - 0.85) * 5.0);
  float fade = 1.0 - ft * ft * (3.0 - 2.0 * ft);
  dVr = dVr * fade - Va * 30.0 * ft * (1.0 - ft);                 // d(1 - smoothstep(0.85, 1.05, r))/dr = -6 t (1 - t) / 0.2
  dVt *= fade;
  float ir = 1.0 / r;
  float ir2 = ir * ir;
  float2 gqF = float2(dFr * q.x * ir - dFt * q.y * ir2, dFr * q.y * ir + dFt * q.x * ir2);
  float2 gqV = float2(dVr * q.x * ir - dVt * q.y * ir2, dVr * q.y * ir + dVt * q.x * ir2);
  FAo = Fa;
  gFo = float2(Jxx * gqF.x + Jyx * gqF.y, Jxy * gqF.x + Jyy * gqF.y) * iR;
  gVo = float2(Jxx * gqV.x + Jyx * gqV.y, Jxy * gqV.x + Jyy * gqV.y) * iR;
  float FA = FAo;
  float2 gF = gFo;
  float2 gV = gVo;
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
  slope += ReliefH * ordL * thin * dhdd * (gF / gl) + SwellH * ordL * exp(-xs * xs) * (-2.0 * FA / (sw * sw)) * gF + VibAmp * gV;
  crest += hn * ordL * thin;
}
[branch] if (abs(PerfMode - 6.0) < 0.5) { float3 n6 = normalize(float3(-slope, 1.0)); return lerp(SaltShade, SaltLit, saturate(FlatTone + (dot(n6, SunDir) - SunDir.z) * LightGain)); }   // banco: sin acabado
// poligonos del salar (textura periodica de 8 x 8 celdas): el mandala los va borrando y de lejos se apagan.
// Donde su aporte es < 1/500 (dentro del mandala, a lo lejos) no se leen las 3 texturas
float pw = max(PolyW, 0.5);
float keep = (1.0 - ordP * (1.0 - PolyKeep)) * (1.0 - smoothstep(0.5, 2.5, fp / pw));
[branch] if (keep * PolyH > 0.002 && !(abs(PerfMode - 7.0) < 0.5)) {
  float T8 = max(CellSize, 1.0) * 8.0;
  float2 uvC = p / T8;
  float tx = 1.0 / 1024.0;
  float c0 = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC, 0.0).r;
  float cx = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(tx, 0.0), 0.0).r;
  float cy = Texture2DSampleLevel(SaltTex, SaltTexSampler, uvC + float2(0.0, tx), 0.0).r;
  float dv = c0 * 0.5 * CellSize;
  float2 gdv = float2(cx - c0, cy - c0) * (0.5 * CellSize) / (tx * T8);
  float xv = dv / pw;
  float hsv = max(saturate(1.0 - xv), 1e-4);                           // la cresta del poligono, tambien con filo
  float hv = pow(hsv, Sharp) * keep;
  float dhdv = (xv < 1.0) ? (-Sharp * pow(hsv, Sharp - 1.0) / pw) : 0.0;
  slope += 3.5 * PolyH * keep * dhdv * gdv;
  crest += hv * PolyH;
}
float3 n = normalize(float3(-slope, 1.0));
// luz rasante: el plano queda en FlatTone; lo que mira al sol se entibia y lo demas se enfria
float t = FlatTone + (dot(n, SunDir) - SunDir.z) * LightGain;
float3 sA = float3(0.5, 0.0, 0.0);
float3 sB = float3(0.5, 0.0, 0.0);
[branch] if (!(abs(PerfMode - 1.0) < 0.5)) {
  [branch] if (fp < 12.0) {
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
    t += (lerp(lerp(n00, n10, nf.x), lerp(n01, n11, nf.x), nf.y) - 0.5) * SaltNoise * (1.0 - smoothstep(3.0, 12.0, fp)) * 0.25;
  }
  // arena: textura periodica con mipmaps (de lejos se promedia sola), dos lecturas a escalas y giros distintos
  float st = max(GrainSize, 1.0);
  sA = Texture2DSample(SandTex, SandTexSampler, p / st).rgb;
  float2 pr = float2(p.x * 0.8 - p.y * 0.6, p.x * 0.6 + p.y * 0.8);
  sB = Texture2DSample(SandTex, SandTexSampler, pr / (st * 2.37)).rgb;
  t += ((sA.r - 0.5) * 0.65 + (sB.r - 0.5) * 0.35) * Grain * 1.8;
}
float3 col = lerp(SaltShade, SaltLit, saturate(t));
col += SunCol * max(t - 0.85, 0.0) * 0.5;
float dk = max(sA.g, sB.g * 0.7);
float lt = sA.b;
col = lerp(col, SaltShade * 0.6, dk * Granite * 0.8);
col = lerp(col, SaltLit * 1.06, lt * Granite * 0.45);
// agua: refleja el cielo en angulo rasante. Donde el Fresnel es < 1/500 (mirando hacia abajo) no se calcula
float cosv = saturate(-Vw.z);
float fres = pow(1.0 - cosv, 5.0) * Wet * (1.0 - min(crest, 1.0) * 0.8);
[branch] if (fres > 0.002 && !(abs(PerfMode - 8.0) < 0.5)) {
  float3 Rw = reflect(Vw, normalize(lerp(float3(0.0, 0.0, 1.0), n, 0.35)));
  float refC_e = Rw.z;
  float3 refC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, refC_e));
  refC = lerp(SkyHor, refC, smoothstep(-0.03, 0.26, refC_e));
  float refC_a = acos(clamp(dot(Rw, SunDir), -1.0, 1.0));
  refC += SunCol * exp(-refC_a / (sunR * 2.2)) * SunGlow * 0.3;
  refC = lerp(refC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, refC_a)) * 0.92);
  refC = lerp(refC, SkyHor, exp(-abs(refC_e) / 0.03) * Haze * 0.7);
  col = lerp(col, refC, saturate(fres));
}
// bruma hacia el cielo del horizonte (distancia REAL: en VR la profundidad de pixel 'nada' al girar).
// Mira al horizonte: elevacion 0 fija, el gradiente del cielo se pliega a constantes; queda el halo del sol
[branch] if (!(abs(PerfMode - 9.0) < 0.5)) {
  float3 Hd = normalize(float3(Vw.xy, 0.0001));
  float fogC_e = 0.0;
  float3 fogC = lerp(SkyMid, SkyTop, smoothstep(0.03, 0.75, fogC_e));
  fogC = lerp(SkyHor, fogC, smoothstep(-0.03, 0.26, fogC_e));
  float fogC_a = acos(clamp(dot(Hd, SunDir), -1.0, 1.0));
  fogC += SunCol * exp(-fogC_a / (sunR * 2.2)) * SunGlow * 0.3;
  fogC = lerp(fogC, SunCol, (1.0 - smoothstep(sunR * 0.9, sunR, fogC_a)) * 0.92);
  fogC = lerp(fogC, SkyHor, exp(-abs(fogC_e) / 0.03) * Haze * 0.7);
  col = lerp(col, fogC, (1.0 - exp(-Dist / max(FogDist, 1.0))) * 0.85);
}
float3 dz_p = frac(float3((floor(Parameters.SvPosition.xy)).xyx) * 0.1031);
dz_p += dot(dz_p, dz_p.yzx + 33.33);
float dz = frac((dz_p.x + dz_p.y) * dz_p.z);
col += (dz - 0.5) * Dither / 255.0;
return col;
