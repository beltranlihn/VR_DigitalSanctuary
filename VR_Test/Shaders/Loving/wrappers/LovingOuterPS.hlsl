// @uses OuterFilm,Caustic,WaterLight,WaterGain
// @inputs Nrm,V,Ld,OuterCol,OuterSh,OuterLook,LV5,Wp,Caus,Phase
// @outputs return:Float3,Alpha:Float1
// ENVOLTURA EXTERIOR (AlphaComposite): Emissive = return (ya premultiplicado), Opacity = Alpha.
// Una sola capa: solo CARAS DE FRENTE (material de un lado), dibujada DESPUES de todo lo de la
// celula (sort 40). OuterCol = (OuterColor, OuterOpacity) lo empuja el BP; OuterSh y OuterLook son
// defaults del material. Ld = la misma luz que el nucleo y las bolas (espacio local).
// LUZ DEL AGUA (F5, 2026-09-28): la gelatina es la superficie que el ojo ve PRIMERO (16,6 % del ojo contra
// ~1-2 % del nucleo) y vela lo de adentro (la luz del nucleo llega al ojo al ~67 %). Su parte es
// WaterLightShell (LV5.w, x WaterLight): Beltran decide MIRANDO si la red va tambien en la gelatina (se lee
// mas; aparece dos veces, en la gelatina y 10-15 cm mas abajo en el nucleo) o solo adentro (0), sin reinyectar.
// LV5 <- el MISMO VectorParameter LV5 que ya alimenta a Custom_0 · Wp <- Absolute World Position (con
// offsets) · Caus, Phase <- CollectionParameter de MPC_Fluid_SC. Entradas NUEVAS al final.
// LV5.z = 0 (o LV5.w = 0) -> xw = 0 -> OuterFilm no toca el cuerpo: bit a bit lo de antes. La llamada a
// OuterFilm conserva la forma de antes (normalize en los argumentos): asi el DXIL con la perilla en 0 sale
// IDENTICO al aprobado.
LVLib L;
float xw = 0.0;
[branch] if (min(LV5.z, LV5.w) > 0.0)
{
    float T = ResolvedView.GameTime;
    if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
    xw = L.WaterLight(Wp.xyz, normalize(Nrm).z, Caus, Phase, T, LV5.z * LV5.w);
}
float a;
float3 c = L.OuterFilm(normalize(Nrm), normalize(V), normalize(Ld), OuterCol, OuterSh, OuterLook, xw, Parameters.SvPosition.xy, a);
Alpha = a;
return c;
