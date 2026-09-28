// @uses LinToSRGB,SRGBToLin
// @inputs SA,Glow,Extras,BG
// @outputs return:Float3
// HAZ (Additive, unlit): el color de la luz del medio (Glow) con caída suave a lo ancho y a lo
// largo, un brillo que ondula despacio y menos intensidad a lo lejos (absorción). ShaftAmount = Extras.y.
// La suma aditiva se hace en el espacio CODIFICADO, como en el prototipo (three.js suma valores ya
// codificados en un RGBA8 no-sRGB): en el Quest el hardware mezcla en LINEAL y codifica después, y así
// el haz salía 9-12 veces más tenue que en el prototipo aprobado (revisión MAT-1, medido). Contra el
// fondo conocido (BG = el medio en esa dirección, del VS): s = enc(BG) + enc(luz) y se devuelve lo que,
// sumado en lineal al fondo, da exactamente s. Delante de un velo o una partícula el error es chico.
LVLib L;
float across = 1.0 - SA.x * SA.x;
across *= across;
// estrías que se desplazan a lo ancho (BG.a = su fase, envuelta en el VS)
float stripes = 0.6 + 0.4 * sin(SA.x * 5.5 + BG.a + SA.y * 2.0);
float along = pow(max(sin(3.14159265 * saturate(SA.y)), 0.0), 1.5);
float a = max(Extras.y, 0.0) * across * stripes * along * SA.w * (1.0 - 0.7 * saturate(SA.z)) * 0.18;
float3 s = saturate(L.LinToSRGB(BG.rgb) + L.LinToSRGB(Glow.rgb * a));
return max(L.SRGBToLin(s) - BG.rgb, 0.0);
