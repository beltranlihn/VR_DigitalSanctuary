// @uses
// @inputs DustUV,DustCol
// @outputs return:Float3,Alpha:Float1
// PARTICULA (AlphaComposite): un punto suave, premultiplicado. DustUV = (esquina x, y, opacidad).
float2 c = DustUV.xy;
float  m = saturate(1.0 - dot(c, c));
m *= m;
float  a = saturate(m * DustUV.z);
Alpha = a;
return DustCol.rgb * a;
