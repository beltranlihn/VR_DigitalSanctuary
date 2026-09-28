// @uses
// @inputs Crn,VC
// @outputs return:Float3,Alpha:Float1
// VELO (Translucent, unlit): dos gaussianas corridas (una mancha irregular, no un disco). Es la capa
// de más RELLENO de todo el fluido: VeilAmount 0 la apaga sin costo.
float2 uv = Crn.xy * 2.0 - 1.0;
float r2 = dot(uv, uv);
float2 o = uv - float2(0.35, -0.2);
float m = max(exp(-r2 * 2.6) + 0.6 * exp(-dot(o, o) * 5.0) - 0.08, 0.0);
Alpha = saturate(VC.a * m * 0.14);
return VC.rgb;
