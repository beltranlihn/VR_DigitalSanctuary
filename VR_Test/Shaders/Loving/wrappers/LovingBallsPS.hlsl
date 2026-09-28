// @uses SS,Hash,Shape,GroupScale,Calm,BallsLayout,Smin,Sph,Balls3,SeqShade,Caustic,WaterLight,WaterGain
// @inputs Rel,Aoc,GI,LV0,LV1,LV2,LV3,LV5,V,Ld,Alb,Sky,Gnd,Side,Term,Wp,Caus,Phase
// @outputs return:Float3
// Normal POR PIXEL con UNA evaluacion: el gradiente analitico EXACTO del smin (Balls3). Se
// comparo con el gradiente de 4 taps del secuenciador y se quedo este (exacto, 1 evaluacion
// contra 4, y robusto en half). Las bolas se recalculan aca con la MISMA BallsLayout (el indice
// del grupo es entero: exacto en half); por eso el material sigue en MFPM_Full_MaterialExpressionOnly.
// Sombreado = SeqShade, el de las esferas del secuenciador (2026-09-28). Los PINES conservan los
// nombres de la arcilla para no tocar el arreglo de entradas del nodo (vaciarlo dispara una
// compilacion fallida que otras sesiones ven); lo que cambio es su SIGNIFICADO y el nombre del
// parametro que los alimenta:
//   Alb  <- ShadeHigh      (color iluminado, brillo)
//   Sky  <- ShadeLow       (color de sombra, contraste: 0,5 = half-lambert del raymarch)
//   Gnd  <- ShadowFill     (relleno de la sombra, tinte: 0 = sin relleno)
//   Side <- ShadeFloorRim  (piso de luminancia, borde, potencia del borde, -)
//   Term <- ShadeAO        (pliegue entre bolas, oclusion hacia el nucleo, -, -)
//   Ld   <- LightDir en MUNDO -> Transform (vector, World -> Local) del grafo, igual que V.
// ColorTemp (LV1.w) corre los dos colores hacia un violeta mas calido (como antes el albedo).
// LUZ DEL AGUA (F5, 2026-09-28): LV5.z = perilla WaterLight (LV5 ya entraba) · Wp <- Absolute World Position
// (con offsets) · Caus, Phase <- CollectionParameter de MPC_Fluid_SC (entradas NUEVAS al final). Este material
// es MFPM_Full: Wp y la fase llegan en float (sin los saltos de half del nucleo). LV5.z = 0 -> la rama no
// corre -> el SeqShade de siempre, bit a bit.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
float4 LV2g = float4(LV2.x * L.GroupScale(GI.w, LV5), LV2.yzw);   // tamano propio del grupo (SizeVariation)
L.Shape(LV0, LV1, LV2g, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float3 toC = normalize(LV0.xyz - GI.xyz + float3(1.0e-4, 0.0, 0.0));
float4 B0, B1, B2;
L.BallsLayout(GI.w, rb, toC, L.SS(0.3, 0.6, saturate(LV1.x)), LV2.z, T, LV3.w, LV1, B0, B1, B2);
float3 g; float cr;
L.Balls3(Rel, B0, B1, B2, kBall, g, cr);
// rsqrt con piso en vez de normalize: g es un lerp de dos normales y en un punto patologico
// (dos bolas opuestas, h = 0,5) podria anularse; normalize(0) = NaN y el pixel sale negro.
float3 N  = g * rsqrt(max(dot(g, g), 1.0e-8));
// Oclusion: el pliegue entre bolas (cr = 4h(1-h), 1 en la costura) y la cara que mira al nucleo
// (Aoc.x = 1 - 0,8 occ, calculado en el vertex). Las dos BAJAN s: el pliegue toma el color de
// sombra y su relleno (violeta), no un gris multiplicado como en la arcilla.
float ao = (1.0 - saturate(Term.y) * (1.0 - Aoc.x)) * (1.0 - saturate(Term.x) * cr);
float3 wt = lerp(float3(1.0, 1.0, 1.0), float3(1.1, 0.93, 1.0), saturate(LV1.w));
float4 Hi = float4(Alb.rgb * wt, Alb.a);
float4 Lo = float4(Sky.rgb * wt, Sky.a);
float3 Vv = V * rsqrt(max(dot(V, V), 1.0e-8));
float3 Lv = normalize(Ld + float3(0.0, 0.0, 1.0e-4));   // LightDir en 0 no da NaN (misma guarda que el secuenciador)
float3 c  = L.SeqShade(N, Vv, Lv, Hi, Lo, Gnd, Side, ao);
[branch] if (LV5.z > 0.0) { c = L.WaterGain(c, L.WaterLight(Wp.xyz, N.z, Caus, Phase, T, LV5.z)); }
return c;
