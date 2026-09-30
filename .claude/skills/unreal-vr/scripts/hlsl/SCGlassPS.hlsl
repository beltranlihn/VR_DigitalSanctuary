// SCGlassPS v1 - M_SCGlass_SC (unlit, TRANSLUCIDO, una cara): la lamina lechosa del HUD (blender-3d/assets/hud.md).
// Emision tenue + un poco mas en el canto de la vista (fresnel); la opacidad la pone el parametro Opacity.
// Entradas: N (VertexNormalWS), V (CameraVector), Color, Base (0,10), Rim (0,25).
float f = 1.0 - saturate(dot(normalize(N), normalize(V)));
return Color * (Base + Rim * f);
