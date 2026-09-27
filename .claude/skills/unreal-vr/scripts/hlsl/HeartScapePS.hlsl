// HeartScapePS v6 - M_HeartScape_SC, PIXEL SHADER. Sombreado mate unlit en espacio LOCAL.
// VI1 = HeartGradVS (membrana: dh/dx, dh/dy, h, cresta | esfera: normal). LPi = posicion local interpolada.
// XA/XB = coordenada de cresta de las 8 ondas (HeartXVS), interpolada: la linea no usa trigonometria por pixel.
// CamL = CameraVector en local. Dist = distancia REAL a la camara (la profundidad de vista "nadaba" al girar la cabeza).
// PerfMode 2/3 = pixeles baratos (banco de medicion).
float3 V = normalize(CamL);
float Tt = View.GameTime;
float pm = floor(PerfMode + 0.5);
float live = step(0.5, Live);
float period = 60.0 * max(floor(BeatDivider + 0.5), 1.0) / max(PreviewBPM, 1.0);
float ph = Tt / period;
float fph = frac(ph);
// el mismo pulso suave que los VS (g(x) = x^2 e^(2(1-x)), latido actual + los dos anteriores): un solo pulso
float tP = max(PulseRise, 0.05);
float Pulse = 0.0;
[unroll] for (int bb = 0; bb < 3; bb++)
{
  float tB = (bb == 0) ? Beat.x : ((bb == 1) ? BeatP.x : BeatP.z);
  float iB = (bb == 0) ? Beat.y : ((bb == 1) ? BeatP.y : BeatP.w);
  float aB = lerp((fph + bb) * period, Beat.w - tB, live);
  float xP = max(aB / tP, 0.0);
  Pulse += lerp(PreviewIntensity, iB, live) * xP * xP * exp(2.0 - 2.0 * xP);
}
float wd = 0.5 / max(PushSpeed, 0.05) * max(Speed, 1.0);   // la onda nace cuando la esfera toca fondo
float cl = cos(radians(LightEl));
float3 L = float3(cl * cos(radians(LightAz)), cl * sin(radians(LightAz)), sin(radians(LightEl)));
// cielo en la direccion de la mirada; tambien es el color al que tiende la niebla
float3 dirv = -V;
float3 sky = lerp(SkyHorizon.rgb, SkyZenith.rgb, smoothstep(0.0, 0.65, dirv.z));
float2 hz = dirv.xy / max(length(dirv.xy), 1e-4);
float2 gd = float2(cos(radians(GlowAz)), sin(radians(GlowAz)));
float side = pow(max(dot(hz, gd), 0.0), 2.5) * (1.0 - smoothstep(0.0, 0.45, abs(dirv.z)));
sky = lerp(sky, SkyHorizonGlow.rgb, side * HorizonGlow);
// dither estatico contra el banding (no hay TAA en Quest)
float3 p3 = frac(float3(Parameters.SvPosition.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
float dith = (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0;
// derivadas FUERA de ramas y bucles
float4 fA = fwidth(XA);
float4 fB = fwidth(XB);
if (Part > 1.5 && Part < 2.5) { return sky + dith; }
if (pm >= 2.0) { return ((Part > 0.5) ? HeartLit.rgb : ColLit.rgb) + dith; }
float fog = 1.0 - exp(-max(Dist - FogStart, 0.0) / max(FogDist, 1.0));
float3 col = float3(0.0, 0.0, 0.0);
if (Part > 2.5)
{
  // esferas que emergen: mate como la central, sin nucleo fijo; brillan cuando pasa una onda por debajo
  float3 N = normalize(VI1.xyz);
  float wrap = saturate((dot(N, L) + Wrap) / (1.0 + Wrap));
  col = lerp(HeartShadow.rgb, HeartLit.rgb, lerp(ShadeFloor, 1.0, wrap));
  float ndv = saturate(dot(N, V));
  col = lerp(col, HeartRimColor.rgb, saturate(HeartRim * 0.8 * pow(1.0 - ndv, 2.5)));
  col = lerp(col, HeartCore.rgb, saturate(VI1.w * OrbGlint) * pow(ndv, 1.5));
}
else if (Part > 0.5)
{
  // esfera central: mate, nucleo luminoso de frente, borde luminoso, recibe el charco de abajo
  float3 N = normalize(VI1.xyz);
  float wrap = saturate((dot(N, L) + Wrap) / (1.0 + Wrap));
  col = lerp(HeartShadow.rgb, HeartLit.rgb, lerp(ShadeFloor, 1.0, wrap));
  col += ColGlow.rgb * PoolGlow * 0.35 * saturate(0.5 - 0.5 * N.z) * (0.6 + 0.4 * Pulse);
  float ndv = saturate(dot(N, V));
  col = lerp(col, HeartCore.rgb, saturate(pow(ndv, 2.2) * (CoreGlow + CoreBeat * Pulse)));
  col = lerp(col, HeartRimColor.rgb, saturate(HeartRim * pow(1.0 - ndv, 2.5) * (0.7 + 0.5 * Pulse)));
}
else
{
  float3 N = normalize(float3(-VI1.x, -VI1.y, 1.0));
  float wrap = saturate((dot(N, L) + Wrap) / (1.0 + Wrap));
  col = lerp(ColShadow.rgb, ColLit.rgb, lerp(ShadeFloor, 1.0, wrap));
  col *= 1.0 - Valley * saturate(-VI1.z / 40.0);
  float fres = pow(1.0 - saturate(dot(N, V)), max(SheenPow, 0.5));
  col = lerp(col, ColSheen.rgb, saturate(Sheen * fres));
  // linea de luz sobre la cresta; donde seria mas fina que un pixel se ensancha y se atenua
  float ln = 0.0;
  if (LineGlow > 0.001)
  {
    float spc = lerp(period * Speed, Spacing, live);
    float Rch = max(Reach, 1.0);
    float Dmx = (spc > 1.0) ? 7.7 * spc : 1e9;
    float Bl = max(BirthDistance, 1.0);
    float LW = max(LineWidth, 0.005);
    float4 WW[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
    float xs[8] = { XA.x, XA.y, XA.z, XA.w, XB.x, XB.y, XB.z, XB.w };
    float fs[8] = { fA.x, fA.y, fA.z, fA.w, fB.x, fB.y, fB.z, fB.w };
    [unroll] for (int k = 0; k < 8; k++)
    {
      float d = lerp((fph + k) * period * Speed, Beat.z - WW[k].x, live) - wd;
      float I = lerp(PreviewIntensity, WW[k].y, live);
      float u = saturate(d / Rch);
      float life = I * (1.0 - smoothstep(FadeStart, 1.0, u)) * smoothstep(0.0, Bl, d) * (1.0 - smoothstep(0.8 * Dmx, Dmx, d));
      float lw = max(LW, 1.2 * fs[k]);
      ln += life * (LW / lw) * exp(-(xs[k] * xs[k]) / (lw * lw));
    }
  }
  col = lerp(col, ColLine.rgb, saturate(LineGlow * ln));
  col = lerp(col, ColGlow.rgb, saturate(CrestGlow * VI1.w) * 0.55);
  // la esfera como luz puntual sobre las crestas cercanas
  float3 dl = float3(0.0, 0.0, HeartZ) - float3(LPi.xy, VI1.z);
  float dd = max(dot(dl, dl), 1.0);
  float wh = saturate((dot(N, dl * rsqrt(dd)) + 0.3) / 1.3);
  float att = 1.0 / (1.0 + dd / max(HeartLightRadius * HeartLightRadius, 1.0));
  col = lerp(col, ColGlow.rgb, saturate(HeartLight * wh * att * (0.6 + 0.5 * Pulse)));
  // charco de luz bajo la esfera
  float rp2 = dot(LPi.xy, LPi.xy);
  col += ColGlow.rgb * PoolGlow * (0.55 + 0.45 * Pulse) * exp(-rp2 / max(PoolRadius * PoolRadius, 1.0)) * 0.5;
}
return lerp(col, sky, fog) + dith;
