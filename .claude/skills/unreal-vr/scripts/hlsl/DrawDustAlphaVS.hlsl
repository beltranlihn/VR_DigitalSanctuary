// DrawDustAlphaVS - M_DrawDust_SC, VERTEX SHADER -> VertexInterpolator_0 -> A del PS. Generado por gen_draw_sea_hlsl.py: NO editar a mano.
// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3).
// Misma cuenta de posicion que DrawDustVS (funcion separada en Unreal).
// --------------------------------------------------------------------------------------------------------
// NODO  MaterialExpressionCustom  Description "DrawDustAlphaVS"  OutputType CMOT_Float1
//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.
// SALIDA float = alpha de la mota (0..1).
// ENTRADAS (13, en este orden):
//   1  UV1         float2  TexCoord 1  |  semilla x, y (0..1); la guarda SM_DrawDust_SC, igual en las 4 esquinas
//   2  UV2         float2  TexCoord 2  |  semilla z, w (0..1)
//   3  CamWS       float3  CameraPositionWS  |  camara (cm); el nivel esta cerca del origen (gotcha 398)
//   4  Advance     float   ScalarParameter Advance  |  5 cm/s (el mismo del mar)
//   5  DustFollow  float   ScalarParameter DustFollow  |  1 (cuanto sigue al avance)
//   6  DustRise    float   ScalarParameter DustRise  |  0.6 cm/s
//   7  DustWobble  float   ScalarParameter DustWobble  |  8 cm
//   8  DustBox     float   ScalarParameter DustBox  |  1400 cm (volumen que se repite alrededor de los ojos)
//   9  DustSize    float   ScalarParameter DustSize  |  0.9 cm (diametro de una mota)
//  10  DustNear    float   ScalarParameter DustNear  |  35 cm (se apaga cerca de la cara)
//  11  FogStart    float   ScalarParameter FogStart  |  500 cm (la misma niebla del mar)
//  12  FogDensity  float   ScalarParameter FogDensity  |  0.00017 /cm
//  13  SeaZ        float   ScalarParameter SeaZ  |  Z de mundo de la superficie (la escribe el BP = Z del actor)
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
float3 e3 = 1.0 - abs(f - 0.5) * 2.0;                  // 0 en el borde de la caja: ahi se apaga
float edge = smoothstep(0.0, 0.18, min(min(e3.x, e3.y), e3.z));
float fog = 1.0 - exp(-max(dist - FogStart, 0.0) * FogDensity);
float nearF = smoothstep(DustNear, DustNear * 3.0, dist);
float tw = 0.65 + 0.35 * sin(T * 0.6 + SeedW * 31.0);
float above = step(SeaZ, CamWS.z + pr.z);
return edge * nearF * (1.0 - fog) * tw * above * min(1.0, (px * px) / (px2 * px2));   // energia conservada bajo 1,5 px
