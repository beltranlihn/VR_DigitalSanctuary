// BreathAirVS - M_BreathAir_SC, VERTEX SHADER -> World Position Offset (via Transform vector Local->World). v2 2026-09-28
// EL ALIENTO VISIBLE (Entering). Cada quad de SM_BreathAir_SC es una mota: este VS calcula su CENTRO, su alfa y su
// tamano SIN ESTADO, con las semillas de la malla y lo que el BP empuja por cuadro (transporte integrado, envolventes,
// marco con retardo). Todo en el espacio LOCAL del componente = el espacio de la CAMARA (el componente cuelga de la
// camara del pawn con transform relativo identidad): X adelante, Y derecha, Z arriba de la cabeza, cm.
//   Corriente 0 (inhalar): del volumen de adelante (marco con retardo, InTilt bajo la mirada) a la boca EXACTA, por
//   una Bezier que pasa cerca de un FOCO visible (FocusDist, FocusTilt): se juntan de costado mientras se acercan y
//   recien despues bajan a la boca, ya apagadas por la cercania al ojo (InFocus 0 = la recta de la v1).
//   Corriente 1 (exhalar): pluma que sale de la boca EXACTA, frena, se abre, sube apenas, se apaga hacia PlumeLen.
// Confort por mota (con la camara de CADA ojo, CamL): invisible a menos de NearMin de ese ojo, invisible por encima de
// ElevMax (grados respecto de la mirada), lo que se mueve rapido en la vista se apaga (SpeedFade), tamano angular con
// tope y con piso (0,2 grados: debajo centellea; lo que se agranda baja de alfa por (fisico / dibujado)^2). Los quads
// con alfa < 0,002 colapsan a tamano 0: no cuestan pixeles.
// SEMILLAS invariantes a la V invertida del importador FBX (gotcha 302): lo asimetrico va en U; en V solo uniformes o
// (b + 1) / 2 (el disco es simetrico). Ver breath_air_model.encode_uv / decode_uv.
// Modelo de referencia: scripts/breath_air_model.py (vs). Verificador: scripts/hlsl/BreathAir_check.py.
// Plan: docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "BreathAirVS"  OutputType CMOT_Float3
//       additionalOutputs: AirV CMOT_Float4 (-> VertexInterpolator -> AirV de BreathAirPS). La salida principal
//       se llama "return" (gotcha 453). Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = desplazamiento LOCAL (cm) del vertice -> Transform (vector, Local -> World) -> WPO.
//        AirV   = (esquina x, esquina y, alfa, corriente) para el pixel shader.
// ENTRADAS (45, en este orden):
//   1  LP              float3  LocalPosition                                       posicion local del vertice (cm, sin WPO)
//   2  Crn             float2  TexCoord 0                                          esquina del quad (0/1, 0/1)
//   3  Sa              float2  TexCoord 1                                          (e, u): desfase en la cinta, profundidad
//   4  Sb              float2  TexCoord 2                                          (a, (b + 1) / 2): punto en el disco unitario
//   5  Sc              float2  TexCoord 3                                          (corriente, ph): 0 inhala / 1 exhala; fase de la turbulencia
//   6  CamL            float3  CameraPositionWS -> TransformPosition (World -> Local)  la camara de ESTE ojo, en local
//   7  AirT            float4  VectorParameter AirT, pin RGBA                      (Tin, Tout, Fout, Glob): lo escribe el BP
//   8  AirE            float4  VectorParameter AirE, pin RGBA                      (Ein, Eout, InRate, OutRate): lo escribe el BP
//   9  MouthL          float3  VectorParameter MouthL, pin RGB                     boca exacta en local (cm): lo escribe el BP
//  10  LagM            float3  VectorParameter LagM, pin RGB                       boca con retardo, en local: lo escribe el BP
//  11  LagA            float3  VectorParameter LagA, pin RGB                       eje del marco con retardo (adelante), local
//  12  LagR            float3  VectorParameter LagR, pin RGB                       eje del marco con retardo (derecha), local
//  13  LagU            float3  VectorParameter LagU, pin RGB                       eje del marco con retardo (arriba), local
//  14  UpL             float3  VectorParameter UpL, pin RGB                        arriba del MUNDO en local (la subida tibia)
//  15  InTilt          float   ScalarParameter InTilt 24                           grados bajo el marco del volumen de inhalar
//  16  InNear          float   ScalarParameter InNear 40                           cm: lo mas cerca que nace una mota de inhalar
//  17  InFar           float   ScalarParameter InFar 95                            cm: lo mas lejos
//  18  InSpreadH       float   ScalarParameter InSpreadH 30                        grados: ancho del volumen
//  19  InSpreadV       float   ScalarParameter InSpreadV 12                        grados: alto del volumen
//  20  InAccel         float   ScalarParameter InAccel 1.35                        >1 = lento lejos, acelera al llegar (sumidero)
//  21  InSwirl         float   ScalarParameter InSwirl 35                          grados de remolino hasta la boca (mitad a cada lado)
//  22  InAlpha         float   ScalarParameter InAlpha 0.45                        opacidad pico de inhalar
//  23  InSizeCm        float   ScalarParameter InSizeCm 0.22                       diametro fisico de la mota (cm)
//  24  InFocus         float   ScalarParameter InFocus 0.8                         0 = recta a la boca; 1 = pasa por el foco
//  25  FocusDist       float   ScalarParameter FocusDist 34                        cm del foco a la boca con retardo
//  26  FocusTilt       float   ScalarParameter FocusTilt 16                        grados del foco bajo el marco con retardo
//  27  OutTilt         float   ScalarParameter OutTilt 18                          grados bajo el marco de la pluma (debajo del metaball)
//  28  PlumeLen        float   ScalarParameter PlumeLen 110                        cm: donde termina la pluma
//  29  OutStart        float   ScalarParameter OutStart 15                         cm: donde se empieza a ver (condensacion)
//  30  OutDecel        float   ScalarParameter OutDecel 1.8                        >1 = chorro que frena
//  31  OutSpread       float   ScalarParameter OutSpread 16                        grados: apertura del cono
//  32  OutFlat         float   ScalarParameter OutFlat 0.6                         aplastamiento vertical del cono
//  33  Buoy            float   ScalarParameter Buoy 10                             cm: subida tibia al final
//  34  Turb            float   ScalarParameter Turb 3                              cm: turbulencia (se detiene en las pausas)
//  35  OutAlpha        float   ScalarParameter OutAlpha 0.5                        opacidad pico de la pluma
//  36  OutSizeCm       float   ScalarParameter OutSizeCm 0.28                      diametro fisico al salir (cm)
//  37  OutGrow         float   ScalarParameter OutGrow 0.8                         crecimiento hasta el final (x1,8)
//  38  NearMin         float   ScalarParameter NearMin 22                          cm al ojo: invisible debajo (confort)
//  39  NearFull        float   ScalarParameter NearFull 45                         cm al ojo: plena desde aca
//  40  ElevMax         float   ScalarParameter ElevMax -4                          grados respecto de la mirada: invisible arriba
//  41  ElevSoft        float   ScalarParameter ElevSoft 6                          grados de fundido debajo de ElevMax
//  42  MaxDeg          float   ScalarParameter MaxDeg 0.4                          tope de tamano angular (inhalar)
//  43  MaxDegOut       float   ScalarParameter MaxDegOut 0.55                      tope de tamano angular (pluma)
//  44  SpeedFade0      float   ScalarParameter SpeedFade0 20                       grados/s: desde aca lo rapido se apaga
//  45  SpeedFade1      float   ScalarParameter SpeedFade1 40                       grados/s: apagado del todo
// USA ADEMAS: nada (ni View ni texturas). Sin bucles, sin arreglos ni indices dinamicos (regla Adreno), sin half.
// REGLAS: dos [branch] por la bandera de corriente (los vertices van ordenados: casi sin divergencia).
// --------------------------------------------------------------------------------------------------------
float isOut = step(0.5, Sc.x);
float e = Sa.x;
float u = Sa.y;
float2 ab = float2(Sb.x, 2.0 * Sb.y - 1.0);
float ph = Sc.y;
float3 Mx = MouthL;
float3 Mg = LagM;
float3 A0 = LagA;
float3 R0 = LagR;
float3 U0 = LagU;
float3 P = Mx;
float3 tg = A0;
float spd = 0.0;
float al = 0.0;
float sz = 0.0;
float mxd = MaxDeg;
[branch]
if (isOut < 0.5)
{
    float ti = radians(InTilt);
    float3 Ai = cos(ti) * A0 - sin(ti) * U0;
    float3 Ui = cos(ti) * U0 + sin(ti) * A0;
    float s = frac(e + AirT.x);
    float d0 = InNear + (InFar - InNear) * pow(max(u, 1.0e-4), 0.8);
    float w = pow(max(s, 1.0e-4), InAccel);
    float sw = radians(InSwirl) * w * (2.0 * step(0.5, ph) - 1.0);
    float ca = cos(sw);
    float sa = sin(sw);
    float a2 = ab.x * ca - ab.y * sa;
    float b2 = ab.x * sa + ab.y * ca;
    float3 st = Mg + Ai * d0 + R0 * (d0 * tan(radians(InSpreadH)) * a2) + Ui * (d0 * tan(radians(InSpreadV)) * b2);
    float3 en = Mx + float3(ab.x, ab.y, 2.0 * u - 1.0);
    float tf = radians(FocusTilt);
    float3 fp = Mg + (cos(tf) * A0 - sin(tf) * U0) * FocusDist;
    float3 cp = 0.5 * (st + en) + (fp - 0.5 * (st + en)) * InFocus;
    float iw = 1.0 - w;
    P = (iw * iw) * st + (2.0 * iw * w) * cp + (w * w) * en;
    tg = (2.0 * iw) * (cp - st) + (2.0 * w) * (en - cp);
    spd = length(tg) * InAccel * pow(max(s, 1.0e-4), InAccel - 1.0) * AirE.z;
    al = InAlpha * smoothstep(0.0, 0.2, s) * AirE.x;
    sz = InSizeCm;
}
[branch]
if (isOut > 0.5)
{
    float to = radians(OutTilt);
    float3 Ao = cos(to) * A0 - sin(to) * U0;
    float3 Uo = cos(to) * U0 + sin(to) * A0;
    float s = frac(e + AirT.y);
    float kk = 1.0 - pow(max(1.0 - s, 1.0e-4), OutDecel);
    float x = OutStart + (PlumeLen - OutStart) * kk;
    float tsp = tan(radians(OutSpread));
    float rad = 1.5 + x * tsp;
    float3 bs = Mx + (Mg - Mx) * smoothstep(0.0, 0.6, s);
    float tu = 6.2831853 * AirT.y;
    float3 tb = Turb * s * float3(sin(3.0 * tu + 6.2831853 * ph), sin(2.0 * tu + 6.2831853 * frac(ph * 7.13 + 0.37)), sin(3.0 * tu + 6.2831853 * frac(ph * 13.7 + 0.71)));
    P = bs + Ao * x + R0 * (rad * ab.x) + Uo * (rad * OutFlat * ab.y) + UpL * (Buoy * s * s) + tb;
    tg = Ao + tsp * (R0 * ab.x + Uo * (OutFlat * ab.y));
    spd = length(tg) * (PlumeLen - OutStart) * OutDecel * pow(max(1.0 - s, 1.0e-4), OutDecel - 1.0) * AirE.w;
    float fr = saturate((AirT.z - s) / 0.08);
    al = OutAlpha * fr * smoothstep(0.02, 0.12, s) * (1.0 - smoothstep(0.5, 1.0, s)) * AirE.y;
    sz = OutSizeCm * (1.0 + OutGrow * s);
    mxd = MaxDegOut;
}
// ---- confort y tamano: las dos corrientes, contra la camara de ESTE ojo ----
float3 D = P - CamL;
float dist = max(length(D), 1.0e-3);
float3 Dn = D / dist;
al = al * smoothstep(NearMin, NearFull, dist);
float se0 = sin(radians(ElevMax - ElevSoft));
float se1 = sin(radians(ElevMax));
al = al * (1.0 - smoothstep(se0, se1, Dn.z));
float tl = max(length(tg), 1.0e-4);
float om = degrees(spd * length(cross(tg / tl, Dn)) / dist);
al = al * (1.0 - smoothstep(SpeedFade0, SpeedFade1, om));
al = al * AirT.w;
float szn = dist * tan(radians(0.2));
float kq = saturate(sz / szn);
al = al * kq * kq;
float szw = clamp(sz, szn, dist * tan(radians(mxd)));
float hsz = 0.5 * szw * step(0.002, al);
// ---- sprite hacia la camara de este ojo ----
float3 f = normalize(CamL - P + float3(1.0e-4, 0.0, 0.0));
float3 rt = normalize(cross(float3(0.0, 0.0, 1.0), f) + float3(0.0, 1.0e-4, 0.0));
float3 up = cross(f, rt);
float2 c = Crn * 2.0 - 1.0;
float3 dst = P + (rt * c.x + up * c.y) * hsz;
AirV = float4(c.x, c.y, al, isOut);
float3 offs = dst - LP;
if (!(dot(offs, offs) < 1.0e8)) { offs = float3(0.0, 0.0, 0.0); }
return offs;
