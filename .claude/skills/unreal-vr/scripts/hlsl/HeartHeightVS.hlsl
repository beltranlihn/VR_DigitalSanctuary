// HeartHeightVS v6 - M_HeartScape_SC, VERTEX SHADER -> WPO (via Transform Local->World). Solo la ALTURA.
// Unreal compila el WPO y cada VertexInterpolator en funciones separadas: cada salida vuelve a llamar a su
// Custom. Por eso este nodo calcula SOLO h (una evaluacion), sin gradiente ni cresta (esos van en HeartGradVS).
// Part 0 membrana, 1 esfera central, 2 cielo, 3 esferas que emergen. PerfMode 1/3 = vertices baratos (banco).
float Tt = View.GameTime;
float live = step(0.5, Live);
float pm = floor(PerfMode + 0.5);
// El pulso VISUAL va a 1/BeatDivider del ritmo cardiaco: el actor emite uno de cada N latidos.
// PreviewBPM es el ritmo cardiaco simulado, asi el preview del editor late igual que en Play.
float period = 60.0 * max(floor(BeatDivider + 0.5), 1.0) / max(PreviewBPM, 1.0);
float ph = Tt / period;
float fph = frac(ph);
float bIdx = floor(ph);
// UN pulso y UN empuje por latido visual, con la misma curva suave g(x) = x^2 e^(2(1-x)): arranca en 0 con
// pendiente 0, cima 1 en x = 1 y cae sin quiebres. Se suman el latido actual y los dos anteriores, cada uno con
// su intensidad (Beat.xy, BeatP.xy, BeatP.zw, escritos por el actor en el MISMO cuadro): no salta nada al latir.
float tP = max(PulseRise, 0.05);
float PushT = 0.5 / max(PushSpeed, 0.05);   // segundos hasta el fondo del empuje
float Pulse = 0.0;
float Push = 0.0;
[unroll] for (int bb = 0; bb < 3; bb++)
{
  float tB = (bb == 0) ? Beat.x : ((bb == 1) ? BeatP.x : BeatP.z);
  float iB = (bb == 0) ? Beat.y : ((bb == 1) ? BeatP.y : BeatP.w);
  float aB = lerp((fph + bb) * period, Beat.w - tB, live);
  float IB = lerp(PreviewIntensity, iB, live);
  float xP = max(aB / tP, 0.0);
  float xS = max(aB / PushT, 0.0);
  Pulse += IB * xP * xP * exp(2.0 - 2.0 * xP);
  Push += IB * xS * xS * exp(2.0 - 2.0 * xS);
}
float wd = PushT * max(Speed, 1.0);   // la onda nace cuando la esfera toca fondo (vineta 3 del dibujo)
float spc = lerp(period * Speed, Spacing, live);
float Rch = max(Reach, 1.0);
float Dmx = (spc > 1.0) ? 7.7 * spc : 1e9;   // antes de reciclar el casillero (8 latidos) la onda ya se fue
if (Part > 2.5)
{
  // ---- esferas que emergen: una instancia del ISM por esfera ----
  // OA = (x, y, salida) y OB = (radio, semilla, ameba) por instancia. Salida: vivo = momento en que la cresta
  // SIN retardo llega a su radio (lo escribe el actor); preview = indice de fase (ciclo de OrbMax latidos).
  float WRo = max(WellRadius, 1.0);
  float2 sp = OA.xy;
  float rsp = length(sp);
  float Ro = max(OB.x, 1.0);
  float so = OB.y * 6.2831853;
  float Nq = max(floor(OrbMax + 0.5), 1.0);
  float cyc = Nq * period;
  float dr = max(rsp - 1.732 * WRo, 0.0);
  float relP = OA.z * period + PushT + dr / max(Speed, 1.0);
  float age = lerp(fmod(Tt - relP + 1.0 + 1000.0 * cyc, cyc) - 1.0, Beat.w - OA.z - PushT, live);
  // vida FIJA: no depende de nada que cambie latido a latido (en la v5 dependia de Spacing y todas saltaban juntas)
  float lifeE = max(lerp(min(OrbLife, cyc - 2.0), OrbLife, live), 2.5);
  // pulso: UNO por onda, con la misma curva suave, cuando su cresta pasa bajo el punto de salida (sin la estela)
  float4 WO[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
  float pO = 0.0;
  [unroll] for (int ko = 0; ko < 8; ko++)
  {
    float d = lerp((fph + ko) * period * Speed, Beat.z - WO[ko].x, live) - wd;
    float I = lerp(PreviewIntensity, WO[ko].y, live);
    float u = saturate(d / Rch);
    float xk = max((d - dr) / (max(Speed, 1.0) * tP), 0.0);
    pO += I * (1.0 - smoothstep(FadeStart, 1.0, u)) * xk * xk * exp(2.0 - 2.0 * xk);
  }
  float pulseO = saturate(pO);
  // subida en UNA sola curva: sumergida (invisible) hasta que llega la cresta; un impulso suave (velocidad 0 al
  // arrancar) la saca por encima de la cresta, y una subida de globo acelera suave y sigue constante hasta
  // RiseHeight al final de su vida. En la v5 eran dos rampas en serie: salia disparada y quedaba ~1 s casi
  // frenada mientras la atravesaba la cresta siguiente ("pegadas").
  float ur = saturate(dr / Rch);
  float launch = lerp(PreviewIntensity, 1.0, live) * lerp(HeightStart, HeightEnd, ur) * (1.0 - smoothstep(FadeStart, 1.0, ur));
  float a0 = max(age, 0.0);
  float T1 = max(RiseTime, 0.1);
  float riseK = saturate(a0 / T1);
  float gA = (a0 < T1) ? T1 * riseK * riseK * riseK * (1.0 - 0.5 * riseK) : a0 - 0.5 * T1;
  float gL = max(lifeE - 0.5 * T1, 1.0);
  float eI = 1.0 - exp(-a0 / max(0.6 * EmergeTime, 0.05));
  float Bup = 1.3 * launch + 2.45 * Ro + 10.0;
  float zc = -1.4 * Ro - 8.0 + Bup * eI * eI + RiseHeight * gA / gL * (0.75 + 0.5 * frac(OB.y * 13.7));
  // crece invisible bajo el agua y se desvanece encogiendo en el ultimo tramo (OrbFade = fraccion de la vida)
  float fin = max(OrbFade, 0.05) * lifeE;
  float lifeK = smoothstep(-0.6, 0.2, age) * (1.0 - smoothstep(lifeE - fin, lifeE, age));
  float3 cO = float3(sp, zc);
  cO += OrbSway * riseK * float3(sin(Tt * 0.37 + so), sin(Tt * 0.29 + 1.7 * so), 0.3 * sin(Tt * 0.5 + 2.3 * so));
  // ameba del secuenciador (M_BlobOrb_SC + BP_OrbDirector_SC.LookWobble): forma grumosa estatica + onda lenta,
  // frecuencia, velocidad, eje de giro y respiracion propios de cada esfera. Toda la vida, desde que nace.
  float3 dirO = normalize(LP + float3(0.0, 0.0, 1e-5));
  float h1 = frac(OB.y * 7.31 + 0.13);
  float h2 = frac(OB.y * 3.77 + 0.51);
  float h3 = frac(OB.y * 5.19 + 0.29);
  float psO = OB.y * 10.2 - 5.1;
  float WFo = 3.0 * (0.7 + 0.6 * h1);
  float WSo = 0.35 * (0.6 + 0.8 * h2);
  float3 axO = normalize(float3(h1, h2, h3) - 0.5 + float3(0.0, 0.0, 0.001));
  float saO, caO;
  sincos(so - 0.349 * Tt, saO, caO);   // giro lento, 20 grados por segundo
  float3 du = dirO * caO + cross(axO, dirO) * saO + axO * dot(axO, dirO) * (1.0 - caO);
  float wsO = sin(du.x * WFo + psO * 1.7) + sin(du.y * WFo * 1.31 + psO * 3.1) + sin(du.z * WFo * 0.77 + psO * 5.3);
  float wmO = sin(du.x * WFo * 1.9 + Tt * WSo + psO * 2.3) * sin(du.y * WFo * 1.3 - Tt * WSo * 0.83 + psO * 1.9);
  float sJ = 1.0 + (frac(psO * 0.137 + 0.31) - 0.5) * 0.5;
  float brO = 1.0 + 0.25 * max(0.55 * sin(-0.754 * Tt * sJ + psO * 2.7) + 0.45 * sin(0.581 * Tt * sJ + 2.32 + psO * 4.1), 0.0);
  float amtO = OrbMorph * OB.z;
  float shO = 1.0 + amtO * (0.25 * wsO + 0.55 * wmO);
  // estiron propio de cada esfera (elipsoide orientado por la semilla): la ameba deja de leerse redonda
  float3 axE = normalize(float3(h3, h1, h2) - 0.5 + float3(0.001, 0.0, 0.0));
  float3 pS = dirO * shO;
  pS += 0.3 * OB.z * dot(pS, axE) * axE;
  return cO + pS * Ro * brO * lifeK * (1.0 + OrbKick * pulseO) - LP;
}
if (Part > 1.5) { return float3(0.0, 0.0, 0.0); }
if (Part > 0.5)
{
  // esfera central: flota (vaiven lento) y en cada latido visual da UN empuje suave hacia abajo que hunde el agua
  // (vineta 2) y la suelta al volver a subir (vineta 3); se achata un poco al empujar. Ameba del secuenciador:
  // forma grumosa que cambia lento + giro lento (la v5 "hervia" 6 a 10 veces mas rapido). Frecuencias mas bajas
  // que en las esferas chicas: con las del secuenciador la central quedaba "coliflor".
  float3 dir = normalize(LP + float3(0.0, 0.0, 1e-5));
  float3 ax = float3(0.3162, 0.5270, 0.7906);
  float sa, ca;
  sincos(-0.1396 * Tt, sa, ca);   // 8 grados por segundo
  float3 du = dir * ca + cross(ax, dir) * sa + ax * dot(ax, dir) * (1.0 - ca);
  float ws = sin(du.x * 2.6 + 2.21) + sin(du.y * 3.4 + 4.03) + sin(du.z * 2.0 + 6.89);
  float wm = sin(du.x * 4.2 + Tt * 0.35 + 2.99) * sin(du.y * 3.4 - Tt * 0.29 + 2.47);
  float WA = HeartMorph * (1.0 + 0.8 * Pulse);
  float R = HeartRadius * (1.0 + PulseScale * Pulse);
  float sqz = HeartSquash * Push;
  float3 sq = float3(1.0 + 0.5 * sqz, 1.0 + 0.5 * sqz, 1.0 - sqz);
  float dz = -HeartSink * Push + HeartFloat * sin(Tt * HeartFloatSpeed * 6.2831853 + 0.7);
  return dir * (1.0 + WA * (0.25 * ws + 0.55 * wm)) * R * sq + float3(0.0, 0.0, HeartZ + dz) - LP;
}
if (pm == 1.0 || pm == 3.0) { return float3(0.0, 0.0, 0.0); }
float Wd = max(Width, 1.0);
float Bl = max(BirthDistance, 1.0);
float Lb = floor(Lobes + 0.5);
float WR = max(WellRadius, 1.0);
float2 p = LP.xy;
float r2 = dot(p, p);
float r = sqrt(r2);
float th = atan2(p.y, p.x + 1e-4);
float4 WW[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
float h = 0.0;
[unroll] for (int k = 0; k < 8; k++)
{
  float d = lerp((fph + k) * period * Speed, Beat.z - WW[k].x, live) - wd;
  float I = lerp(PreviewIntensity, WW[k].y, live);
  float u = saturate(d / Rch);
  float W = Wd * (1.0 + Spread * u);
  float life = I * (1.0 - smoothstep(FadeStart, 1.0, u)) * smoothstep(0.0, Bl, d) * (1.0 - smoothstep(0.8 * Dmx, Dmx, d));
  float xa = (r - (1.732 * WR + d)) / W;
  // corte: fuera de esta franja el aporte de la onda es < 0,2 % de su altura (invisible)
  if (life < 0.001 || xa > 2.5 + Warp || xa < -2.5 * (1.0 + Tail) - Warp) { continue; }
  float sd = lerp(frac(sin((bIdx - k) * 12.9898) * 43758.5453), WW[k].z, live) * 6.2831853;
  float warp = Warp * (0.65 * sin((Lb - 1.0) * th + 3.1 * sd) + 0.35 * sin((Lb + 1.0) * th - 0.7 * sd));
  float x = xa + warp;
  float hills = 1.0 + Hills * (0.6 * sin(Lb * th + sd) + 0.3 * sin((Lb + 2.0) * th - 1.7 * sd) + 0.1 * sin((2.0 * Lb + 1.0) * th + 2.3 * sd));
  float behind = step(x, 0.0);
  float a = 1.0 + Tail * behind;
  float mm = RingMix * behind;
  h += life * lerp(HeightStart, HeightEnd, u) * max(hills, 0.0) * exp(-(x * x) / (a * a)) * (1.0 - mm + mm * cos(Ringing * x));
}
// el pozo lo hunde el EMPUJE, con el mismo tiempo que la esfera (en reposo el agua queda casi plana)
float rho2 = r2 / (WR * WR);
h -= (WellDepth + WellBeat * Push) * (1.0 - rho2) * exp(-0.5 * rho2);
float rr = (r - WR * 1.732) / (WR * 0.6);
h += RimExtra * (1.0 + 0.6 * Push) * exp(-rr * rr);
float2 q = p / max(SwellScale, 1.0);
float ts = Tt * SwellSpeed;
float tf = saturate((r - WR) / (3.0 * WR));
h += Swell * (0.5 * sin(q.x + ts) * sin(0.8 * q.y - 0.7 * ts) + 0.3 * sin(1.7 * (q.x + q.y) + 1.3 * ts) + 0.2 * sin(2.3 * (q.x - 2.0 * q.y) - 0.9 * ts)) * tf * tf * (3.0 - 2.0 * tf);
float4 BB[4] = { B0, B1, B2, B3 };
[unroll] for (int j = 0; j < 4; j++)
{
  float ab = Beat.w - BB[j].w - PushT;
  float eb = smoothstep(-0.4, 0.3, ab) * (1.0 - smoothstep(0.3, 2.0, ab));
  float2 db = p - BB[j].xy;
  float Rb = max(BB[j].z, 1.0) * 1.8;
  h += step(0.5, BB[j].z) * live * BumpAmp * BB[j].z * eb * exp(-dot(db, db) / (Rb * Rb));
}
return float3(0.0, 0.0, h);
