// HallGlassInsidePS v1 - M_Hall_Glass_SC. 1 = la camara esta DENTRO del hall (radio < 720 cm alrededor del eje), 0 = afuera.
// Pedido de Beltran (2026-09-29): desde adentro el vidrio se ve amarillo calido como el interior aunque afuera sea
// negro; al integrarlo en la narrativa, InsideColor transiciona al color de la etapa a la que se sale.
// Entrada: C (CameraPositionWS). El hall esta en el origen del mundo en Test_Hall (si se mueve, restar su posicion).
return saturate((720.0 - length(C.xy)) / 30.0);
