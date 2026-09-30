// AuraVS - M_AlmaAura_SC, VERTEX SHADER -> World Position Offset (via Transform vector Local->World). v1 2026-09-30
// EL AURA DE ALMA: una nube de motas diminutas y muy translucidas en un cascaron de 1,3 a 1,8 radios alrededor de Alma.
// Cada quad de SM_AlmaAura_SC es una mota en su lugar de reposo (espacio del Body: SM_AlmaSphere tiene radio 50). Este VS
// le suma (1) un GIRO lento y diferencial del cascaron alrededor de un eje que deriva (cada mota a su ritmo: el cascaron
// se "cizalla" y nunca se ve rigido) y (2) CURL NOISE: el rotor de un potencial de senos, un flujo SIN DIVERGENCIA (las
// motas vecinas se mueven juntas, como humo), dos octavas con frecuencias en relacion no entera. Decide su alfa (titileo
// lento) y su tamano ANGULAR (con piso: no centellea). Cuando Alma habla, el BP escribe AuraSpeak (suavizado) y adelanta
// AuraPhase: el flujo se acelera sin saltos (la fase se integra en el BP), el curl se amplia, el cascaron se abre un poco
// y las motas brillan mas. AuraReveal (lo escribe el BP desde AppearT) las apaga cuando Alma no esta.
// SEMILLAS invariantes a la V invertida del importador (gotcha 302) y a las UV en fp16: lo asimetrico en U, en V fases.
// Modelo de referencia (mismo codigo en numpy + chequeo): scripts/alma_aura_model.py. Malla: scripts/gen_alma_aura.py.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "AuraVS"  OutputType CMOT_Float3
//       additionalOutputs: AuraV CMOT_Float4 (-> VertexInterpolator -> AuraV de AuraPS). La salida principal
//       se llama "return" (gotcha 453). Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = desplazamiento LOCAL del vertice -> Transform (vector, Local -> World) -> WPO.
//        AuraV  = (esquina x, esquina y, alfa, mezcla de color) para el pixel shader.
// ENTRADAS (22, en este orden):
//   1  LP              float3  LocalPosition                                       posicion local del vertice: mota + esquina
//   2  Crn             float2  TexCoord 0                                          (esquina k 0..3, 0.5)
//   3  Sa              float2  TexCoord 1                                          (b brillo/tamano, fase 1)
//   4  Sb              float2  TexCoord 2                                          (tw ritmo del titileo, fase 2)
//   5  CamL            float3  CameraPositionWS -> TransformPosition (World -> Local)  la camara de ESTE ojo, en local
//   6  AuraSpeak       float   ScalarParameter AuraSpeak 0                         la voz, suavizada (0..1): la escribe el BP
//   7  AuraPhase       float   ScalarParameter AuraPhase 0                         fase extra integrada por el BP (s): acelera sin saltos
//   8  AuraReveal      float   ScalarParameter AuraReveal 1                        0 = Alma no esta (sin motas), 1 = plena
//   9  AuraAlpha       float   ScalarParameter AuraAlpha 0.35                      opacidad de las motas
//  10  SizeDeg         float   ScalarParameter SizeDeg 0.16                        tamano angular (grados)
//  11  SizeMinDeg      float   ScalarParameter SizeMinDeg 0.1                      piso del tamano angular (no centellea)
//  12  SizeVar         float   ScalarParameter SizeVar 0.35                        variacion del tamano (+-)
//  13  Twinkle         float   ScalarParameter Twinkle 0.45                        titileo lento (0 = ninguno)
//  14  ShellScale      float   ScalarParameter ShellScale 1                        escala del cascaron (1 = 1,3 a 1,8 radios)
//  15  Breath          float   ScalarParameter Breath 0.03                         respiracion lenta del radio de cada mota
//  16  CurlAmp         float   ScalarParameter CurlAmp 5.5                         amplitud del curl (unidades del Body: 50 = el radio de Alma)
//  17  CurlFreq        float   ScalarParameter CurlFreq 1.6                        frecuencia del curl (por radio de Alma)
//  18  FlowSpeed       float   ScalarParameter FlowSpeed 0.35                      ritmo del flujo
//  19  SwirlSpeed      float   ScalarParameter SwirlSpeed 0.08                     giro del cascaron (rad/s)
//  20  SpeakCurl       float   ScalarParameter SpeakCurl 0.6                       al hablar: curl x (1 + SpeakCurl)
//  21  SpeakExpand     float   ScalarParameter SpeakExpand 0.05                    al hablar: el cascaron se abre (fraccion)
//  22  SpeakGlow       float   ScalarParameter SpeakGlow 0.6                       al hablar: alfa x (1 + SpeakGlow)
// USA ADEMAS: View.GameTime (anima en el viewport sin Play). Sin bucles, sin arreglos (regla Adreno, gotcha 399), sin half.
// --------------------------------------------------------------------------------------------------------
float Tt = View.GameTime;
if (!(Tt > -1.0e9 && Tt < 1.0e9)) { Tt = 0.0; }
float kc = floor(Crn.x + 0.5);
float cx = step(0.5, kc) * step(kc, 2.5);
float cy = step(1.5, kc);
float3 P0 = LP - float3(0.0, (2.0 * cx - 1.0) * 0.2, (2.0 * cy - 1.0) * 0.2);
float bs = Sa.x;
float ph1 = Sa.y;
float tws = Sb.x;
float ph2 = Sb.y;
float sp = saturate(AuraSpeak);
float rv = saturate(AuraReveal);
float Tf = Tt + AuraPhase;
// ---- giro lento del cascaron alrededor de un eje que deriva; cada mota a su ritmo (rotacion diferencial) ----
float3 ax = normalize(float3(0.35 * sin(0.041 * Tf + 1.3), 0.45 * cos(0.029 * Tf + 0.4), 1.0));
float th = Tf * SwirlSpeed * (0.6 + 0.8 * frac(bs * 3.7 + ph1));
float sth;
float cth;
sincos(th, sth, cth);
float3 Pr = P0 * cth + cross(ax, P0) * sth + ax * dot(ax, P0) * (1.0 - cth);
Pr *= ShellScale * (1.0 + Breath * sin(0.45 * Tf + 6.2831853 * ph2) + SpeakExpand * sp);
// ---- curl noise: rotor de psi = (sin(1.3y)+sin(1.9z), sin(1.7z)+sin(1.1x), sin(2.0x)+sin(1.5y)), dos octavas ----
float3 q = Pr * (CurlFreq / 50.0);
float t1 = Tf * FlowSpeed;
float3 C1 = float3(1.5 * cos(1.5 * q.y + 0.71 * t1 + 0.9) - 1.7 * cos(1.7 * q.z - 0.53 * t1 + 2.9),
                   1.9 * cos(1.9 * q.z + 0.61 * t1 + 4.2) - 2.0 * cos(2.0 * q.x - 0.67 * t1 + 3.3),
                   1.1 * cos(1.1 * q.x + 0.83 * t1 + 5.1) - 1.3 * cos(1.3 * q.y - 0.97 * t1 + 0.4));
float3 q2 = q * 2.13 + float3(3.1, 1.7, 5.3);
float t2 = t1 * 1.37;
float3 C2 = float3(1.5 * cos(1.5 * q2.y - 0.59 * t2 + 2.2) - 1.7 * cos(1.7 * q2.z + 0.77 * t2 + 0.3),
                   1.9 * cos(1.9 * q2.z - 0.87 * t2 + 1.6) - 2.0 * cos(2.0 * q2.x + 0.49 * t2 + 5.7),
                   1.1 * cos(1.1 * q2.x - 0.63 * t2 + 3.9) - 1.3 * cos(1.3 * q2.y + 0.91 * t2 + 2.6));
float3 P = Pr + (C1 + 0.45 * C2) * (CurlAmp * (1.0 + SpeakCurl * sp) / 2.8);
// ---- alfa: titileo lento + brillo propio + la voz + la aparicion ----
float tw = 1.0 - Twinkle * 0.5 * (1.0 + sin(Tf * (0.35 + 0.5 * tws) + 6.2831853 * ph1));
float br = 0.45 + 0.55 * frac(bs * 7.1 + ph2);
float3 Dv = P - CamL;
float dist = max(length(Dv), 1.0e-3);
float nearF = smoothstep(8.0, 30.0, dist);
float al = min(AuraAlpha * br * tw * (1.0 + SpeakGlow * sp) * rv * nearF, 0.9);
// ---- tamano ANGULAR con piso (la escala del Body se cancela: distancia y tamano estan en las mismas unidades) ----
float sdeg = max(SizeDeg * (1.0 + SizeVar * (2.0 * frac(bs * 3.1 + ph1) - 1.0)) * (1.0 + 0.25 * sp), SizeMinDeg);
float hsz = 0.5 * dist * tan(radians(sdeg)) * saturate(rv * 2.0) * step(0.002, al);
// ---- sprite hacia la camara de este ojo ----
float3 fw = normalize(CamL - P + float3(1.0e-4, 0.0, 0.0));
float3 rt = normalize(cross(float3(0.0, 0.0, 1.0), fw) + float3(0.0, 1.0e-4, 0.0));
float3 up = cross(fw, rt);
float2 c = float2(cx, cy) * 2.0 - 1.0;
float3 dst = P + (rt * c.x + up * c.y) * hsz;
AuraV = float4(c.x, c.y, al, frac(bs * 5.3 + ph1));
float3 offs = dst - LP;
if (!(dot(offs, offs) < 1.0e6)) { offs = float3(0.0, 0.0, 0.0); }
return offs;
