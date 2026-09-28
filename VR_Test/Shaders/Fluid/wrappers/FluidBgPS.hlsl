// @uses FluidColor
// @inputs V,FTop,FMid,FBot,Glow,Absorb
// @outputs return:Float3
// FONDO del fluido: el medio en el infinito. La dirección sale de la CÁMARA (V = CameraVectorWS, del
// píxel hacia el ojo), así el cascarón puede estar en cualquier lugar y a cualquier radio: siempre se
// ve "en el infinito" y coincide EXACTO con el color hacia el que se funde todo lo demás (misma
// FluidColor). El actor va sin rotar: el Z del mundo es el Z local.
// Dither R2 en un espacio aproximadamente CODIFICADO (8 bits sin tonemapper): el degradado no hace bandas.
LVLib L;
float3 d = -normalize(V.xyz);
float3 c = L.FluidColor(d, FTop, FMid, FBot, Glow, Absorb);
float n = frac(dot(Parameters.SvPosition.xy, float2(0.7548776662, 0.5698402910)));
// Gamma 2,0 (sqrt / cuadrado) en vez de pow 2,2: sin ruido s^2 = c EXACTO; las dos pow float3 eran la
// mitad del costo de este PS a pantalla completa (revisión COS-2: -0,35..-0,46 ms estimados).
float3 s = max(sqrt(max(c, 0.0)) + (n - 0.5) / 255.0, 0.0);
return s * s;
