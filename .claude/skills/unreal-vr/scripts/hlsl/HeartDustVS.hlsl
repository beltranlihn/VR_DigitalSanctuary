// HeartDustVS - M_HeartDust_SC, VERTEX SHADER -> World Position Offset (via Transform vector Local->World). v1 2026-10-01
// EL POLVO DE LA ETAPA DEL LATIDO: motas FIJAS al mar (BP_HeartDust_SC va pegado al root de BP_HeartScape_SC, asi que
// su espacio local es el del mar: origen = la esfera central). Cuando la VUELTA rota y baja el mar, las motas cercanas
// pasan de costado y las lejanas despacio: el paralaje dice "estoy girando y subiendo". Deriva de pocos cm (si se
// movieran mucho se leeria viento, no giro). Dos poblaciones en la MISMA malla (UV1.x): 0 polvo, 1 particulas.
// Tamano ANGULAR con piso (no centellea); se apaga cerca de la cara (NearFade) y a lo lejos (FarFade).
// SEMILLAS invariantes a la V invertida del importador (gotcha 302) y a las UV en fp16.
// Modelo de referencia (mismo codigo en numpy + chequeo): scripts/heart_dust_model.py. Malla: scripts/gen_heart_dust.py.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "HeartDustVS"  OutputType CMOT_Float3
//       additionalOutputs: DustV CMOT_Float4 (-> VertexInterpolator -> DustV de HeartDustPS). La salida principal
//       se llama "return" (gotcha 453). Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = desplazamiento LOCAL del vertice -> Transform (vector, Local -> World) -> WPO.
//        DustV  = (esquina x, esquina y, alfa, tipo) para el pixel shader.
// ENTRADAS (17, en este orden):
//   1  LP              float3  LocalPosition                                       posicion local del vertice: mota + esquina
//   2  Crn             float2  TexCoord 0                                          (esquina k 0..3, 0.5)
//   3  Sa              float2  TexCoord 1                                          (tipo 0 polvo / 1 particula, fase 1)
//   4  Sb              float2  TexCoord 2                                          (b brillo/tamano, fase 2)
//   5  CamL            float3  CameraPositionWS -> TransformPosition (World -> Local)  la camara de ESTE ojo, en local
//   6  DustReveal      float   ScalarParameter DustReveal 1                        0 = sin polvo, 1 = pleno (lo escribe el BP)
//   7  DustAlpha       float   ScalarParameter DustAlpha 0.22                      opacidad del polvo
//   8  DustSizeDeg     float   ScalarParameter DustSizeDeg 0.1                     tamano angular del polvo (grados)
//   9  SparkAlpha      float   ScalarParameter SparkAlpha 0.55                     opacidad de las particulas
//  10  SparkSizeDeg    float   ScalarParameter SparkSizeDeg 0.2                    tamano angular de las particulas (grados)
//  11  Twinkle         float   ScalarParameter Twinkle 0.6                         titileo lento de las particulas (0 = ninguno)
//  12  SizeMinDeg      float   ScalarParameter SizeMinDeg 0.07                     piso del tamano angular (no centellea)
//  13  SizeVar         float   ScalarParameter SizeVar 0.35                        variacion del tamano (+-)
//  14  DriftAmp        float   ScalarParameter DriftAmp 6                          deriva de cada mota (cm)
//  15  DriftSpeed      float   ScalarParameter DriftSpeed 0.18                     ritmo de la deriva
//  16  NearFade        float   ScalarParameter NearFade 60                         se apagan a menos de esto de la cara (cm)
//  17  FarFade         float   ScalarParameter FarFade 2600                        se apagan hacia esta distancia (cm)
// USA ADEMAS: View.GameTime (anima en el viewport sin Play). Sin bucles, sin arreglos (regla Adreno, gotcha 399), sin half.
// --------------------------------------------------------------------------------------------------------
float Tt = View.GameTime;
if (!(Tt > -1.0e9 && Tt < 1.0e9)) { Tt = 0.0; }
float kc = floor(Crn.x + 0.5);
float cx = step(0.5, kc) * step(kc, 2.5);
float cy = step(1.5, kc);
float3 P0 = LP - float3(0.0, (2.0 * cx - 1.0) * 0.2, (2.0 * cy - 1.0) * 0.2);
float kind = floor(Sa.x + 0.5);
float ph1 = Sa.y;
float bs = Sb.x;
float ph2 = Sb.y;
float rv = saturate(DustReveal);
float t = Tt * DriftSpeed;
float3 D = DriftAmp * float3(sin(t * (0.7 + 0.6 * bs) + 6.2831853 * ph1),
                             sin(t * (0.9 + 0.5 * ph2) + 6.2831853 * ph2 + 1.7),
                             0.6 * sin(t * (0.5 + 0.4 * ph1) + 6.2831853 * bs + 3.1));
float3 P = P0 + D;
float3 Dv = P - CamL;
float dist = max(length(Dv), 1.0e-3);
float nf = smoothstep(0.35 * NearFade, NearFade, dist);
float ff = saturate((FarFade - dist) / max(0.35 * FarFade, 1.0));
ff = ff * ff * (3.0 - 2.0 * ff);
float tw = 1.0 - Twinkle * 0.5 * (1.0 + sin(Tt * (0.4 + 0.6 * bs) + 6.2831853 * ph1));
float br = 0.5 + 0.5 * frac(bs * 7.3 + ph2);
float a0 = lerp(DustAlpha, SparkAlpha * tw, kind) * br;
float al = min(a0 * nf * ff * rv, 0.9);
float s0 = lerp(DustSizeDeg, SparkSizeDeg, kind);
float sdeg = max(s0 * (1.0 + SizeVar * (2.0 * frac(bs * 3.1 + ph1) - 1.0)), SizeMinDeg);
float hsz = 0.5 * dist * tan(radians(sdeg)) * step(0.002, al);
float3 fw = normalize(CamL - P + float3(1.0e-4, 0.0, 0.0));
float3 rt = normalize(cross(float3(0.0, 0.0, 1.0), fw) + float3(0.0, 1.0e-4, 0.0));
float3 up = cross(fw, rt);
float2 c = float2(cx, cy) * 2.0 - 1.0;
float3 dst = P + (rt * c.x + up * c.y) * hsz;
DustV = float4(c.x, c.y, al, kind);
float3 offs = dst - LP;
if (!(dot(offs, offs) < 1.0e8)) { offs = float3(0.0, 0.0, 0.0); }
return offs;
