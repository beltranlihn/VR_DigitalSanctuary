// @uses
// @inputs Crn,ColA,Bok
// @outputs return:Float3,Alpha:Float1
// PARTÍCULA (Translucent): punto suave; las muy cercanas (Bok -> 1) son un disco fuera de foco.
float2 uv = Crn.xy * 2.0 - 1.0;
float m = saturate(1.0 - dot(uv, uv));
float s = lerp(m * m, smoothstep(0.0, 0.3, m) * 0.55, Bok.x);
Alpha = saturate(ColA.a * s);
return ColA.rgb;
