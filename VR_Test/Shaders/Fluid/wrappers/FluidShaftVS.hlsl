// @uses AbsorbAt,ShaftTable,FluidColor
// @inputs LocalPos,Crn,Along,Idx,CamL,Absorb,Extras,FTop,FMid,FBot,Glow
// @outputs return:Float3,SA:Float4,BG:Float4
// HACES DESDE ARRIBA (F3): 8 haces en UNA malla (SM_FluidShafts8_SC: una tira de 9 filas por haz). Crn = UV0 (x: 0/1 a lo ancho) · Along = UV1.x (0 arriba -> 1 abajo) · Idx =
// UV2.x (qué haz). Cada tira gira alrededor de SU EJE para mirar a la cámara (por ojo, CamL) y se
// abre hacia abajo. Fijos en el espacio del actor (lejos: 14-40 m); no los lleva la corriente.
// Extras.y = ShaftAmount (0 = sin área: costo de relleno cero). SA = (x, a lo largo, absorción, brillo).
// LUZ REFRACTADA POR UNA SUPERFICIE QUE NO SE VE (2026-09-28): el punto de entrada de cada haz deriva despacio
// (~1,2 m), el eje ondula apenas, el ancho respira y cada haz se enciende y se apaga a destiempo (el foco de las
// olas); por dentro, estrías que se desplazan a lo ancho (fase envuelta en BG.a, calculada aquí en fp32).
// Los anchos se compensan (sqrt(60/ancho)): un haz ancho es más tenue por píxel. Ritmos CONSTANTES x T.
// No se usa BP_LightShaft_SC: trae pulso y respiración (esta etapa solo tiene EEG).
// BG = el medio (FluidColor) en la dirección ojo -> vértice: el PS lo usa para sumar la luz en el espacio
// CODIFICADO como el prototipo (revisión MAT-1). Por vértice alcanza: 9 filas por haz y el degradado es suave.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float i = floor(Idx.x + 0.5);
float y = saturate(Along.x);
float x = Crn.x * 2.0 - 1.0;
float4 A;
float wid, ph;
L.ShaftTable(i, A, wid, ph);
A.xy += 120.0 * float2(sin(T * 0.071 + ph), cos(T * 0.053 + 1.3 * ph));
float3 ax = normalize(float3(-0.3034, 0.09481, -0.94813) + 0.05 * float3(sin(T * 0.091 + 2.0 * ph), cos(T * 0.113 + 0.7 * ph), 0.0));
float w = wid * (0.85 + 0.15 * sin(T * 0.13 + 2.1 * ph));
float3 C = A.xyz + ax * (y * A.w);
float3 side = normalize(cross(ax, C - CamL.xyz) + float3(0.0, 0.0, 1.0e-4));
float3 P = C + side * (x * w * (0.55 + 0.45 * y));
float s = 0.5 + 0.5 * sin(T * 0.043 + 1.3 * ph) * sin(T * 0.029 + 2.7 * ph + 1.0);
float inten = lerp(0.15, 1.0, s * s * (3.0 - 2.0 * s));
float shim = 0.75 + 0.25 * sin(T * 0.45 + ph + y * 5.0);
SA = float4(x, y, L.AbsorbAt(length(P - CamL.xyz), Absorb), shim * inten * sqrt(60.0 / max(wid, 10.0)));
float3 toP = P - CamL.xyz;
BG = float4(L.FluidColor(toP / max(length(toP), 1.0), FTop, FMid, FBot, Glow, Absorb), 6.2831853 * frac((T * 0.08 + ph) / 6.2831853));
if (!(Extras.y > 0.0)) { P = C; }
float3 off = P - LocalPos.xyz;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 20000.0) / max(ol, 1.0e-4));
