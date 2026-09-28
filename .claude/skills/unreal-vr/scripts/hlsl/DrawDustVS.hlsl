// DrawDustVS - M_DrawDust_SC, VERTEX SHADER -> WPO (mundo; SIN Transform). Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// Cada mota vive en una caja que se repite alrededor de la camara (campo infinito), deriva con el
// avance, sube y ondula. Quad orientado a la camara, nunca menor a 1,5 px.
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawDustVS"  OutputType CMOT_Float3
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float3 = desplazamiento en mundo (destino - posicion original).
// ENTRADAS (11, en este orden):
//   1  UV0         float2  TexCoord 0  |  esquina del quad (0..1)
//   2  UV1         float2  TexCoord 1  |  semilla x, y (0..1); la guarda SM_DrawDust_SC, igual en las 4 esquinas
//   3  UV2         float2  TexCoord 2  |  semilla z, w (0..1)
//   4  CamWS       float3  CameraPositionWS  |  camara (cm); el nivel esta cerca del origen (gotcha 398)
//   5  VtxRel      float3  WorldPosition - CameraPositionWS (nodos, LWC)  |  posicion original del vertice relativa a la camara
//   6  Advance     float   ScalarParameter Advance  |  5 cm/s (el mismo del mar)
//   7  DustFollow  float   ScalarParameter DustFollow  |  1 (cuanto sigue al avance)
//   8  DustRise    float   ScalarParameter DustRise  |  0.6 cm/s
//   9  DustWobble  float   ScalarParameter DustWobble  |  8 cm
//  10  DustBox     float   ScalarParameter DustBox  |  1400 cm (volumen que se repite alrededor de los ojos)
//  11  DustSize    float   ScalarParameter DustSize  |  0.9 cm (diametro de una mota)
// TIEMPO: View.GameTime adentro (fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.
// --------------------------------------------------------------------------------------------------------
float T = View.GameTime;
float3 Seed = float3(UV1.x, UV1.y, UV2.x);   // la semilla va en las UV: la posicion de la malla solo da bounds
float SeedW = UV2.y;
float3 drift = float3(-Advance * DustFollow, 0.0, DustRise) * T;
float3 wob = DustWobble * float3(sin(T * 0.21 + SeedW * 6.28), sin(T * 0.17 + SeedW * 9.1), sin(T * 0.13 + SeedW * 4.3));
float3 boxOff = float3(0.0, 0.0, -0.25 * DustBox);
float3 f = frac((Seed * DustBox + drift - (CamWS + boxOff)) / DustBox);
float3 pr = boxOff + (f - 0.5) * DustBox + wob;      // centro de la mota, relativo a la camara
float dist = max(length(pr), 1.0);
float projScale = 0.5 * View.ViewSizeAndInvSize.y * ResolvedView.ViewToClip[1][1];
float px = DustSize * projScale / dist;             // diametro en pixeles
float px2 = max(px, 1.5);                           // nunca menos de 1,5 px...
float half_ = 0.5 * DustSize * px2 / max(px, 0.0001);   // ...agrandando el quad
float2 Cn = UV0 * 2.0 - 1.0;
float3 Rt = ResolvedView.ViewToTranslatedWorld[0].xyz;
float3 Up = ResolvedView.ViewToTranslatedWorld[1].xyz;
return pr + (Rt * Cn.x + Up * Cn.y) * half_ - VtxRel;   // WPO = destino - posicion original
