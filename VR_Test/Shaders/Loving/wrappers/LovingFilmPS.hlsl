// @uses Film
// @inputs Nrm,Misc,Misc2,V,LV3,FilmCol,FilmK,FilmSky,FilmGnd,FilmRim,FilmFade
// @outputs return:Float3,Alpha:Float1
// PELICULA (AlphaComposite): Emissive = return (ya premultiplicado), Opacity = Alpha.
// La usan el brazo, el puente y la membrana del nucleo (mismo pixel shader, misma apariencia).
// FilmFade = (medio ancho del relevo con la membrana del nucleo, radio de revelado, ancho del
// menisco, medio ancho del recorte). keepC apaga la pelicula del brazo DENTRO de la membrana del
// nucleo; es SIMETRICO alrededor de 0 (a mitad justo en la union) para que el relevo coincida con
// el hueco de la membrana, que se abre con el mismo smoothstep(-w, w) sobre Misc.z. keepR la
// apaga donde el anillo colapsa o donde queda dentro del solido del vecino (brazo <-> puente,
// membrana del nucleo <-> raiz del brazo).
// pb = linea de Plateau (union brazo/membrana del nucleo + union brazo/puente). Va con abs():
// desde que el nucleo tiene membrana, la raiz del brazo asoma entre el nucleo opaco y esa
// membrana; con max(dC,0) todo ese tramo valia pb = 1 y se veia como un parche blanco.
// El termino del contacto va ademas * keepC: sin eso quedaba un collar brillante DENTRO de la
// membrana (pb 0,56 a dC = -0,5 con la pelicula ya apagada) y la costura del nucleo salia 1,5x
// mas brillante que las otras. Asi cada pelicula aporta la mitad en la union, como brazo/puente.
// LV3.y = MembraneOpacity (perilla del BP): escala la sigma de la pelicula.
LVLib L;
float3 N  = normalize(Nrm);
float3 Vv = normalize(V);
float keepC = smoothstep(-max(FilmFade.x, 0.01), max(FilmFade.x, 0.01), Misc2.x);
float keepR = saturate(Misc.y / max(FilmFade.y, 0.01)) * smoothstep(-FilmFade.w, FilmFade.w, Misc.z);
float pb = exp2(-abs(Misc2.x) / max(FilmFade.z, 0.01)) * keepC
         + exp2(-abs(Misc.z) / max(FilmFade.z, 0.01)) * step(Misc.z, 1.0e3);
float4 Col = FilmCol;
Col.a *= max(LV3.y, 0.0);
float a;
float3 c = L.Film(N, Vv, Misc.x, keepC, keepR, pb, Col, FilmK, FilmSky, FilmGnd, FilmRim, Parameters.SvPosition.xy, a);
Alpha = a;
return c;
