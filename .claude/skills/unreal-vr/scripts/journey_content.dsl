;; journey_content.dsl - BP_JourneyContent_SC: el CONTENIDO del cuadro de resultados del final (2026-09-30, noche).
;; Encargo de Narrativa (director de la noche, delegado por Beltran). El MARCO es de Mesh 3D: BP_ResultsArt_SC
;; (/Game/SoulCharger/Mechanics/Results/): cara +X, arriba +Z; ventanas (centro z, alto) = calm (+26, 21) · heart (+3, 21) ·
;; breath (-18, 17) · melody (-38, 19), 103 cm de ancho; franja de titulo z +43,25 (alto 9,5); cajita del texto z +62,5,
;; 92 x 17 cm; floats KTitle/KCalm/KHeart/KBreath/KMelody/KTip para fundir.
;; CONFIRMADO por Mesh 3D (via Narrativa, 2026-09-30): pivote = CENTRO del panel (raiz = centro de Rim/Glass/Trace);
;; WinCalm z +26 · WinHeart +3 · WinBreath -18 · WinMelody -38 · Tip +62,5; cara +X, arriba +Z. Test_Results: panel a 2 m,
;; centro a ~122 cm del piso.
;; Diseno de referencia (APROBADO, copiar tal cual en estetica): web/prototipo-narrativo/world.js, seccion RESULTADOS
;; (drawGraphCard, drawBreathCard, drawMelodyCard, drawResHeader, drawResTip; RES_ITEMS; STAGES[i].color).
;;
;; ARQUITECTURA (barata en Quest: se dibuja UNA vez, nada por cuadro salvo 6 escalares de fundido):
;; - Actor BP_JourneyContent_SC, se cuelga del BP_ResultsArt_SC (AttachToActor, transform identidad). Un
;;   ProceduralMeshComponent "Cards" (runtime, AddComponentByClass) con 6 SECCIONES = 6 quads en el plano YZ a x = +0,6 cm
;;   (delante de las ventanas): 0 titulo · 1 calm · 2 heart · 3 breath · 4 melody · 5 tip.
;; - Una TextureRenderTarget2D por seccion (CreateRenderTarget2D RGBA8, mips automaticos, ClearColor negro), 10 px/cm:
;;   titulo 1030x95 · calm 1030x210 · heart 1030x210 · breath 1030x170 · melody 1030x190 · tip 920x170 (~4 MB + mips).
;;   => 1 px = 1 mm del panel: las coordenadas de la web (en mm, "26 * mm") se copian TAL CUAL.
;; - Material M_JourneyCard_SC: Unlit, ADDITIVE, TwoSided. Emissive = Tex(Card).rgb * Fade * Gain. Sin alfa: el Canvas -> RT
;;   no deja un alfa confiable, y el fondo oscuro ya lo pone el vidrio del marco de Mesh 3D. Colores PREMULTIPLICADOS por el
;;   alfa de la web (rgba(236,232,224,.28) -> color * 0,28). Una MID por seccion (param Card = su RT, Fade).
;;   TranslucencySortPriority del componente = 1 (va despues del vidrio del marco).
;; - Fuente: Michroma NO esta en el proyecto ni en la maquina (la web la baja de Google Fonts). Se usa la del motor
;;   /Engine/EngineFonts/Roboto (pedido de Narrativa). Quicksand (Core/Font) es la alternativa del proyecto.
;;   Importar Michroma = descargar un archivo -> solo con OK de Beltran.
;;
;; API (publica):
;;   Build()                      -> asegura malla/RT/MID, lee datos, dibuja las 5 tarjetas fijas y limpia la del tip.
;;   SetTip(Key: Name)            -> calm/heart/breath/melody/soul/drawing o None. Crossfade: se apaga (0,17 s), se redibuja,
;;                                   vuelve (0,2 s), con curva; VR_click1 al cambiar (el mismo de la paleta del dibujo).
;;   SetBreathScores(Scores: float[]) y SetMinutes(M: float) -> los pone el director (Breath publica CycleScores; asi este
;;                                   BP no depende de un asset que todavia no existe). Sin datos: muestras de la web.
;; Datos de la calma y el latido: BP_BioHub (Core/Signals/, persistente): CurrentBin, BinHasCalm(i)/GetCalmBinAvg(i),
;;   BinHasHeart(i)/GetHeartBinAvg(i), BinStage (int[180]). Sin datos (CurrentBin < 20): la serie de muestra de la web
;;   (resSeries). Huecos (BinHas* false): se saltan (el trazo une los vecinos: "un hueco callado, no roto").
;; Fundidos: Tick copia los K del marco (GetAttachParentActor -> cast BP_ResultsArt_SC) a los Fade de cada seccion, solo si
;;   cambiaron; el tip ademas por TipK. Paso con Dt = min(DeltaTime, 1/30) (regla 4 de la obra).
;; bPreviewInEditor: el Construction Script llama Build -> se ve en el viewport del editor (Beltran autora mirando; y yo
;;   verifico con CaptureViewport sin PIE).
;;
;; VERIFICAR EN EL TURNO (find_node_types / get_node_type_pins), antes de escribir:
;;   Rendering|CreateRenderTarget2D (pines Width, Height, Format, ClearColor, bAutoGenerateMips)
;;   Rendering|BeginDrawCanvastoRenderTarget (salidas Canvas, Size, Context) · Rendering|EndDrawCanvastoRenderTarget (Context)
;;   Rendering|ClearRenderTarget2D · Canvas: DrawLine (K2_DrawLine), DrawText (K2_DrawText), DrawPolygon (K2_DrawPolygon),
;;   DrawTexture (K2_DrawTexture, con textura None = cuadro solido), DrawTriangles (K2_DrawTriangle + MakeCanvasUVTri),
;;   TextSize (K2_TextSize) · Rendering|Material|SetTextureParameterValue (MID) · Audio|PlaySound2D.
;;   Tamano de Roboto a escala 1: medir TextSize("H") en el PIE y fijar FontPx (hoy se asume 24 px -> Scale = px/24).
;;
;; COLORES (sRGB de la web -> lineal, para FLinearColor del Canvas; CALIBRAR a ojo con CaptureViewport: si salen lavados,
;; el RT guarda sRGB y hay que pasar los colores sin linealizar):
;;   Entering #5d7fe0 (0,109 0,212 0,745) · Recognizing #e0566b (0,745 0,093 0,147) · Loving #9a6ee6 (0,323 0,155 0,791)
;;   Attracting #e8a04e (0,807 0,352 0,076) · Surrounding #4fc28f (0,078 0,539 0,275)
;;   Crema #f1ece2 (0,879 0,839 0,761) · gris de guias (236,232,224) = (0,839 0,807 0,745) * alfa.
;;   RES_ITEMS: calm = Loving · heart = Recognizing · breath = Entering · melody = Attracting · soul = crema · drawing = Surrounding.
;;   lighten(c, k) = lerp(c, 1, k) en sRGB -> hacerlo en sRGB y despues linealizar (funcion JcLighten).
;;
;; ===== Layout de las tarjetas (px = mm) =====
;; Grafico (drawGraphCard): nombre (color etapa) Roboto 20 en (26, base 40); meta derecha "average NN / 100" o "average NN bpm"
;;   Roboto 19 al 72 %, alineado a W-26. Area x0=104, x1=W-26, yTop=66, yBot=H-42. pad = (hi-lo)*0,12 (o 1).
;;   Guias punteadas en hi y lo: trazos 7 on / 7 off, grosor 1,6, gris * 0,28. Valores hi/lo a la izquierda (alineados a
;;   x0-16, centrados en Y), Roboto 21 al 90 %. Calma se muestra *100; latido redondeado.
;;   Area bajo la curva: triangulos con color de vertice arriba col*0,33 -> abajo 0 (gradiente, como el 0x55->0x00).
;;   Linea: pasada ancha 11 px col*0,4 + pasada fina 4 px lighten(col,0,45). Suavizado: promedio de 3 vecinos.
;;   Banda de etapas en yb=H-22, alto 6: por etapa i, de a=primer casilla con BinStage==i a b=ultima (normalizado a N); sin
;;   datos: RES_SPANS [[.10,.28],[.28,.44],[.44,.62],[.62,.80],[.80,.97]]. Color de la etapa * 0,85. Margen 2 px por lado.
;;   "start" (26, yb+3) y "end" (derecha W-6, yb-12): Roboto 15 al 50 %.
;; Respiracion (drawBreathCard): nombre + meta "N cycles · inhale, hold, exhale". n anillos, x0=70, x1=W-70, cy=H*0,6,
;;   R=min(46, (x1-x0)/(n-1)*0,36). Perfecto (s>=0,95): anillo 4,5 px lighten(col,.5) + halo (3 anillos mas anchos y tenues)
;;   y disco R-2,5. Si no: anillo 3,2 px col*0,8 y disco max(4, s*(R-9)). Disco: col + un disco interior mas claro
;;   (lighten .75) corrido (-0,25r, -0,3r) de radio 0,6r (el degradado radial de la web, en dos capas).
;; Melodia: nombre "YOUR MELODY" + meta "playing" con una corchea dibujada (disco + plica + bandera: Roboto no trae el glifo).
;; Titulo: "YOUR JOURNEY THROUGH SOUL CHARGER" Roboto 29 centrado (base 44), crema; "NN min  ·  5 stages  ·  5 lights"
;;   Roboto 18 al 60 % centrado (base 74). NN = Minutes (o CurrentBin*BinSeconds/60, o 14 de muestra).
;; Tip: marca de color (x 34, y 30, 5 x H-60) · nombre en su color Roboto 19 (60, base 50) · texto crema Roboto 23 desde
;;   (60, base 86), renglones de 31, ancho maximo W-96, corte por palabras con TextSize.
;;   Textos (RES_ITEMS, ingles, TAL CUAL de la web):
;;   calm:    "The calm of your mind across the whole journey, read from your brain activity every few seconds. The higher the line, the quieter your mind was."
;;   heart:   "Your heartbeat from the first step to the last: your average pulse every few seconds. Notice where it slowed down."
;;   breath:  "One ring for each breathing cycle you followed in Entering. The more the light fills its ring, the closer you were to the rhythm: inhale, hold, exhale."
;;   melody:  "The melody you composed in Attracting, playing again. Every sphere you placed is one of its notes."
;;   soul:    "Your soul, fully charged: five lights, one for each stage you lived."
;;   drawing: "What you created in Surrounding, with your own hands."
;; (Base del texto -> posicion superior del Canvas: top = base - 0,78 * px de la fuente. Ajustar con la captura.)
;;
;; ===== Variables =====
;; Z-Journey (internas): Cards (ProceduralMeshComponent) · RTs (TextureRenderTarget2D[6]) · MIDs (MaterialInstanceDynamic[6])
;;   · SerCalm, SerHeart (float[]) · SerStage (int[]) · StLo, StHi, StAvg (float) · Pts (Vector2D[]) · Tris (CanvasUVTri[])
;;   · TipKey, TipWant (Name) · TipK (float) · KCache (float[6]) · Lines (String[]) · Words (String[]).
;; Journey (instance editable): BreathScores (float[], def [0,62 0,83 1 0,71]) · Minutes (float, 0 = calcular) · Gain (1,0)
;;   · StageColors (LinearColor[5], los de arriba) · Cream (LinearColor) · FontPx (24) · bPreviewInEditor (false) · ClickSound
;;   (/Game/NeuralCanvas/Sound/VR_click1) · ClickVol (1,0).
;;
;; ===== Funciones (orden de escritura: hojas primero) =====
;; JcEnsure        crea Cards (6 quads), RTs (CreateRenderTarget2D), MIDs (CreateDynamicMaterialInstance de M_JourneyCard_SC
;;                 con Card = RT), SetMaterial por seccion. Idempotente (IsValid Cards).
;; JcQuad(S, Zc, W, H) agrega la seccion S: 4 vertices en x=0,6; y = +-W/2; z = Zc +- H/2; UV (0,0) arriba-IZQUIERDA VISTA DESDE
;;                 +X (= y = +W/2: mirando hacia -X, la derecha del que mira es -Y) -> U = (W/2 - y)/W, V = (Zc + H/2 - z)/H.
;; JcData          lee el BioHub (GetActorOfClass BP_BioHub) o arma las muestras; SerStage; Minutes.
;; JcStats(Heart)  StLo/StHi/StAvg de la serie (saltando huecos).
;; JcText(C, Txt, X, TopY, Px, Col, AlignRight) -> DrawText con Scale = Px/FontPx; si AlignRight, X -= TextSize.X * escala.
;; JcDash(C, X0, X1, Y, Col)  guias punteadas.
;; JcRing(C, X, Y, R, Th, Col)  circulo de 48 segmentos (DrawLine en loop).
;; JcGraph(Heart)  Begin -> Clear -> cabecera/meta -> guias -> valores -> area (Tris) -> linea (2 pasadas) -> banda -> End.
;; JcBreath / JcMelody / JcTitle / JcTip(Key)  idem.
;; Build           JcEnsure -> JcData -> JcTitle -> JcGraph(false) -> JcGraph(true) -> JcBreath -> JcMelody -> tip limpio.
;; SetTip(Key)     TipWant = Key; SetActorTickEnabled true.
;; JcTipStep(Dt)   si TipWant != TipKey: TipK -= Dt*6; al llegar a 0: TipKey = TipWant, JcTip(TipKey) (si no es None) y
;;                 PlaySound2D(ClickSound). Si no: TipK += Dt*5 (tope 1). Fade del tip = KTip * smooth(TipK).
;; JcFadeStep      copia KTitle..KMelody del marco a los Fade (solo si cambiaron).
;; EventTick       Dt = min(DeltaSeconds, 1/30) -> JcFadeStep -> JcTipStep(Dt).
;; ConstructionScript  si bPreviewInEditor -> Build (preview en el editor).
