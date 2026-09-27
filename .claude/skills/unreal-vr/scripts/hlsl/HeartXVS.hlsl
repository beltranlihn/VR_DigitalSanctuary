// HeartXVS v6 - M_HeartScape_SC, VERTEX SHADER -> VertexInterpolator_2 (ondas 0-3) y _3 (ondas 4-7).
// Devuelve la coordenada de cresta x de 4 ondas (misma cuenta que HeartHeightVS). El PS dibuja la linea fina
// con x INTERPOLADO: sin trigonometria por pixel. KO = 0 en el nodo A y 4 en el nodo B (lo unico que cambia).
float KO = 0.0;
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return float4(100.0, 100.0, 100.0, 100.0); }
float Tt = View.GameTime;
float live = step(0.5, Live);
float period = 60.0 * max(floor(BeatDivider + 0.5), 1.0) / max(PreviewBPM, 1.0);
float wd = 0.5 / max(PushSpeed, 0.05) * max(Speed, 1.0);   // la onda nace cuando la esfera toca fondo
float ph = Tt / period;
float fph = frac(ph);
float bIdx = floor(ph);
float spc = lerp(period * Speed, Spacing, live);
float Rch = max(Reach, 1.0);
float Dmx = (spc > 1.0) ? 7.7 * spc : 1e9;   // antes de reciclar el casillero (8 latidos) la onda ya se fue
float Wd = max(Width, 1.0);
float Lb = floor(Lobes + 0.5);
float WR = max(WellRadius, 1.0);
float2 p = LP.xy;
float r = length(p);
float th = atan2(p.y, p.x + 1e-4);
float4 WW[4] = { V0, V1, V2, V3 };
float xs[4];
[unroll] for (int k = 0; k < 4; k++)
{
  float kk = KO + k;
  float d = lerp((fph + kk) * period * Speed, Beat.z - WW[k].x, live) - wd;
  float u = saturate(d / Rch);
  float W = Wd * (1.0 + Spread * u);
  float xa = (r - (1.732 * WR + d)) / W;
  xs[k] = xa;
  // la linea solo necesita x exacto cerca de 0: lejos de la cresta alcanza con xa
  if (abs(xa) < 1.5 + Warp)
  {
    float sd = lerp(frac(sin((bIdx - kk) * 12.9898) * 43758.5453), WW[k].z, live) * 6.2831853;
    xs[k] = xa + Warp * (0.65 * sin((Lb - 1.0) * th + 3.1 * sd) + 0.35 * sin((Lb + 1.0) * th - 0.7 * sd));
  }
}
return float4(xs[0], xs[1], xs[2], xs[3]);
