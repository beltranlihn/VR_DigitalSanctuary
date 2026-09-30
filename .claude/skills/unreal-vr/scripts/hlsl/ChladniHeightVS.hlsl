// ChladniHeightVS - M_ChladniFloor_SC. VERTEX SHADER -> Transform (Local->World, vector) -> WPO. Salida (0, 0, h) en cm
// GENERADO por scripts/gen_chladni_material.py: NO editar a mano (se pisa). Plan: docs/PLAN-SALAR-CHLADNI-2026-09-28.md
// Modos DESPLEGADOS, sin arreglos ni bucles (gotcha 399); hash sin seno (gotcha 481). Cuerpo de un Custom: termina en return.
// NODO  MaterialExpressionCustom  Description "ChladniHeightVS"  OutputType CMOT_Float3
// ENTRADAS (39, en este orden):
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
//  37  PerfMode   float   ScalarParameter PerfMode
//  38  PerfForce  float   ScalarParameter PerfForce
//  39  Plain      float   ScalarParameter Plain
// --------------------------------------------------------------------------------------------------------
if (Part > 0.5) { return float3(0.0, 0.0, 0.0); }
[branch] if (Plain > 0.5) { return float3(0.0, 0.0, 0.0); }   // piso liso: quieto
[branch] if (abs(PerfMode - 3.0) < 0.5) { return float3(0.0, 0.0, 0.0); }   // banco: sin WPO
[branch] if (PerfForce > 0.5) { Order = 1.0; W0 = 1.0; V0 = 0.0; W1 = 1.0; V1 = 0.0; W2 = 1.0; V2 = 0.0; W3 = 1.0; V3 = 0.0; W4 = 1.0; V4 = 0.0; W5 = 1.0; V5 = 0.0; W6 = 1.0; V6 = 0.0; W7 = 1.0; V7 = 0.0; }
const float PI = 3.14159265;
float R = max(PlateR, 1.0);
float iR = 1.0 / R;
float calm = Calm * iR;
float ws = max(BaseW + W0 + W1 + W2 + W3 + W4 + W5 + W6 + W7, 0.001);
float act = Order + V0 + V1 + V2 + V3 + V4 + V5 + V6 + V7;
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
float FA = BaseW * cos(PI * Kr * rA);
float VbA = 0.0;
[branch] if (W0 > 0.001 || V0 > 0.001) { float m = cos(PI * Kr * 1.0000 * rA) * cos(Sym * 1.0 * thA + 0.0000) * smoothstep(0.1870, 0.4420, rA) * onA; FA += W0 * m; VbA += V0 * m; }
[branch] if (W1 > 0.001 || V1 > 0.001) { float m = cos(PI * Kr * 1.5000 * rA) * cos(Sym * 2.0 * thA + 1.5708) * smoothstep(0.2530, 0.5980, rA) * onA; FA += W1 * m; VbA += V1 * m; }
[branch] if (W2 > 0.001 || V2 > 0.001) { float m = cos(PI * Kr * 2.0000 * rA) * cos(Sym * 1.0 * thA + 1.5708) * smoothstep(0.1650, 0.3900, rA) * onA; FA += W2 * m; VbA += V2 * m; }
[branch] if (W3 > 0.001 || V3 > 0.001) { float m = cos(PI * Kr * 1.2500 * rA) * cos(Sym * 3.0 * thA + 0.0000) * smoothstep(0.3025, 0.7150, rA) * onA; FA += W3 * m; VbA += V3 * m; }
[branch] if (W4 > 0.001 || V4 > 0.001) { float m = cos(PI * Kr * 2.5000 * rA) * cos(Sym * 2.0 * thA + 1.5708) * smoothstep(0.2200, 0.5200, rA) * onA; FA += W4 * m; VbA += V4 * m; }
[branch] if (W5 > 0.001 || V5 > 0.001) { float m = cos(PI * Kr * 3.0000 * rA) * cos(Sym * 1.0 * thA + 0.0000) * smoothstep(0.1540, 0.3640, rA) * onA; FA += W5 * m; VbA += V5 * m; }
[branch] if (W6 > 0.001 || V6 > 0.001) { float m = cos(PI * Kr * 1.7500 * rA) * cos(Sym * 3.0 * thA + 1.5708) * smoothstep(0.2750, 0.6500, rA) * onA; FA += W6 * m; VbA += V6 * m; }
[branch] if (W7 > 0.001 || V7 > 0.001) { float m = cos(PI * Kr * 2.2500 * rA) * cos(Sym * 2.0 * thA + 0.0000) * smoothstep(0.2090, 0.4940, rA) * onA; FA += W7 * m; VbA += V7 * m; }
FA /= ws;
VbA *= 1.0 - smoothstep(0.85, 1.05, rA);
float ordL = Order * (1.0 - smoothstep(EdgeIn, 1.08, rpJ)) * smoothstep(calm * 0.8, calm * 1.6, rp);   // centro calmo: sin mandala bajo el usuario
float x = FA / max(SwellW, 0.02);
float h = SwellH * ordL * exp(-x * x) + VibAmp * VbA;   // solo la loma SUAVE: la cresta fina va por pixel
return float3(0.0, 0.0, h);
