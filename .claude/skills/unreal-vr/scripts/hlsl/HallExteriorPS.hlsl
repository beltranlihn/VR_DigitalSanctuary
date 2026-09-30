// HallExteriorPS v4 - M_Hall_Exterior_SC, PIXEL SHADER (unlit). El exterior negro del hall-portal + la linea de luz
// alrededor del marco de cada puerta (pedido de Beltran 2026-09-29: "ayudara a que se sienta como portal").
// Sobre negro, el halo es lo que se ve como resplandor: el nucleo es la ranura, el halo el aire iluminado.
// Entradas: P (LocalPosition, cm), RingR (radio del anillo en elevacion, cm), RingWidth (cm), RingCore,
//           RingGlow, RingGlowWidth (cm), RingColor.
// Geometria fija (gen_hall_portal.py): centro de puerta z 245, puertas en +X y -X; |x| < 650 = lejos de las puertas.
// 🔴 MFPM_Full_MaterialExpressionOnly: P llega a ~760 cm; en fp16 el paso es 0,5 cm y la linea de 1,5 cm tiembla.
float eD = length(float2(P.y, P.z - 245.0));
float d = length(float2(eD - RingR, max(650.0 - abs(P.x), 0.0)));
float aa = clamp(fwidth(d), 0.01, 5.0);
float hw = 0.5 * RingWidth;
float core = (1.0 - smoothstep(hw - aa, hw + aa, d)) * saturate(RingWidth / (2.0 * aa));
// el halo TERMINA a 4 anchos: sobre negro puro, la cola exponencial (0,002 lineal = 8/255 en sRGB) dibujaba
// el contorno rectangular de la piel negra (v1, captura desde afuera)
// v4: el halo es REDONDO y cabe entero en la piel negra (z 40..450 = 205 cm alrededor del centro de la puerta).
// Recortarlo por altura (v3) lo dejaba aplastado arriba y abajo: se seguia leyendo el corte recto (visto por Beltran).
// Por eso el alcance maximo sale de la geometria: gmax = 205 - RingR - hw - 2 cm.
float gmax = max(205.0 - RingR - hw - 2.0, 1.0);
float glow = exp(-max(d - hw, 0.0) / max(RingGlowWidth, 0.1)) * (1.0 - smoothstep(0.0, min(4.0 * max(RingGlowWidth, 0.1), gmax), d - hw));
float3 c = RingColor * (core * RingCore + glow * RingGlow);
float mx = max(max(c.r, c.g), c.b);
c *= min(mx, 1.0) / max(mx, 1.0e-4);
return c;
