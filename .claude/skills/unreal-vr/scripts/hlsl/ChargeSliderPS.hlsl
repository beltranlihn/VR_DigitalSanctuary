// ChargeSliderPS v1 - M_SCChargeSlider_SC (unlit, ADITIVO): el slider de carga del timbre y del SAVE MELODY. Es
// TRANSPARENTE: solo se ve lo cargado (Beltran). UV.x = fraccion del recorrido (angular en el timbre, del perimetro en el
// SAVE), 0..1. Progreso efectivo = Progress*(1+2E) con borde suave [0, 2E]: en 0 no asoma nada y en 1 cierra la costura.
// Entradas: UV (TexCoord 0), Progress, Color, Level.
float E = 0.004;
float pe = Progress * (1.0 + 2.0 * E);
float lit = smoothstep(0.0, 2.0 * E, pe - UV.x);
return Color * (lit * Level);
