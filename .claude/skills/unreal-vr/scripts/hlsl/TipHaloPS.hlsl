// TipHaloPS v1 - M_TB_TipHalo (Unlit, Additive), PIXEL SHADER. Halo de energia de la punta del pincel (2026-09-30).
// Pedido de Beltran: "el punto desde donde se dibuja debe tener un halo, un poco mas cool, de que ahi sale energia".
// Esfera (BasicShapes/Sphere) colgada de SM_Tip. Con dot(N,V) se reconstruye el radio proyectado r (0 centro, 1 borde):
//   core  = resplandor suave, max en el centro, se apaga en la silueta (pow(ndv, Softness)).
//   waves = anillos que salen hacia afuera (fase WavePh 0..1, la empuja el Blueprint: sin Time -> sin fp16).
//   pulse = respiracion lenta (PulseV 0..1, tambien desde el BP).
//   Boost 0..1 (dibujando): mas anillos y mas brillo.
// Entradas: N (VertexNormalWS), V (CameraVector), Color, Intensity, Boost, WavePh, PulseV, WaveFreq, Softness.
float ndv = saturate(dot(normalize(N), normalize(V)));
float r = sqrt(saturate(1.0 - ndv * ndv));
float core = pow(ndv, max(Softness, 0.5));
float ring = 0.5 + 0.5 * sin((r * WaveFreq - WavePh) * 6.2831853);
ring = ring * ring * (r * (1.0 - r) * 4.0);
float pulse = 0.8 + 0.2 * PulseV;
float e = core * core * pulse * (1.0 + 0.8 * Boost) + ring * (0.18 + 0.5 * Boost) * ndv;
return Color * e * Intensity;
