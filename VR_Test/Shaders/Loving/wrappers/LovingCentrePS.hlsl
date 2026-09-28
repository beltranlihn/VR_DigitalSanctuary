// @uses SeqShade,Caustic,WaterLight,WaterGain
// @inputs Nrm,V,Ld,Alb,Sky,Gnd,Side,Term,LV5,Wp,Caus,Phase
// @outputs return:Float3
// NUCLEO: el MISMO sombreado que las bolas (SeqShade), con los mismos nombres y significados de
// parametros (ver LovingBallsPS): Alb <- ShadeHigh, Sky <- ShadeLow, Gnd <- ShadowFill,
// Side <- ShadeFloorRim, Term <- ShadeAO (no aplica al nucleo: no tiene pliegues ni otro nucleo
// enfrente; el pin queda conectado para no tocar el arreglo de entradas). Ld = LightDir en MUNDO
// pasada a local por el Transform del grafo, igual que en las bolas: una sola luz para toda la celula.
// La normal llega del vertex (analitica, CentreVS). Vale mientras la ondulacion de la ameba tenga
// longitud de onda >= ~8 separaciones de vertice: la ameba V4 es un polinomio de grado 10 (lambda
// minima 34 grados = 16 separaciones de la icoesfera de 10242 de SM_LovingCentre_SC; el 99 % de la
// energia en l <= 6, >= 28 grados). Con SM_LovingIco_SC (2562, 8 separaciones: el limite) ahorraria
// ~0,14 ms de vertices, pero con el contraste 0,7 del nucleo el sombreado erra p99 1,2 niveles sRGB y
// hasta 3,6 (con 10242: 0,3 / 1,5): un facetado tenue posible en el elemento que mas se mira. Queda en
// 10242; el cambio de malla es un A/B de visor (sin tocar codigo). Si el nucleo se deforma mas fino,
// pasar la normal al pixel como en las bolas (la leccion de la esfera plana).
// ShadeLow.a (contraste) del NUCLEO = 0,70, no el 0,444 de las bolas: con 0,444 el relieve de los
// pseudopodos caia 40 % (rms de luma 0,047 -> 0,028) y la ameba se leia solo por la silueta.
// LUZ DEL AGUA (F5, 2026-09-28): LV5 <- VectorParameter LV5 (lo empuja PushGlobals; .z = perilla WaterLight)
// · Wp <- Absolute World Position (con offsets de material: la superficie deformada) · Caus, Phase <-
// CollectionParameter de MPC_Fluid_SC. Con LV5.z = 0 la rama no corre: el pixel es el SeqShade de siempre,
// bit a bit. Entradas NUEVAS al final: las ocho de antes conservan su orden.
// 🔴 Este material recibe las entradas en HALF: la normal interpolada se renormaliza con piso.
LVLib L;
float3 N  = Nrm * rsqrt(max(dot(Nrm, Nrm), 1.0e-4));
float3 Vv = V * rsqrt(max(dot(V, V), 1.0e-4));
float3 Lv = normalize(Ld + float3(0.0, 0.0, 1.0e-3));
float3 c  = L.SeqShade(N, Vv, Lv, Alb, Sky, Gnd, Side, 1.0);
[branch] if (LV5.z > 0.0)
{
    float T = ResolvedView.GameTime;
    if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
    c = L.WaterGain(c, L.WaterLight(Wp.xyz, N.z, Caus, Phase, T, LV5.z));
}
return c;
