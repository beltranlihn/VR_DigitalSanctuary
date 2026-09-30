// SCLightPS v1 - M_SCLight_SC (unlit, opaco): las cintas de luz de la familia (ranura del timbre y del SAVE, aros y punta
// del sensor). Glow = brillo de reposo del objeto (el BP lo sube al apretar); AppearGlow = 0..1 de la aparicion 'luz primero'
// (el BPC_AppearLuz_SC lo lleva de 0 a 1 en el relevo y le da la exhalacion final).
// Entradas: Color, Glow, AppearGlow.
return Color * (Glow * AppearGlow);
