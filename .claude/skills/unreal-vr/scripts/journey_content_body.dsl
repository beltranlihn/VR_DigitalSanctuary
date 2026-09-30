;; journey_content_body.dsl - CUERPOS de BP_JourneyContent_SC. Diseno y API: journey_content.dsl. Tracker: blueprints/BP_JourneyContent_SC.md.
;; ESTADO 2026-09-30 (turno Drawing T2): ESCRITO en el editor y verificado (captura + PIE Build + PIE SetTip, 0 errores).
;;   Este archivo = lo que hay en el editor, salvo los ";;?" (los nombres reales los aplica VR_Test/Saved/ClaudeScripts/
;;   journey/split_journey.py con su tabla rep{}). JcLighten, JcBreathOne y JcBreathGlow van aca tal como quedaron en el editor.
;;   La variable Gain del BP se BORRO (no la usaba ningun grafo): el brillo es el parametro Gain del MATERIAL (1,6).
;; ";;?" = nombre de nodo a confirmar con find_node_types antes de escribir.
;; Cards = componente SCS ProceduralMeshComponent (BP nuevo, sin instancias: sin el problema de la plantilla; y el Construction
;; Script no puede AddComponentByClass). Arrays de las tarjetas en el CDO:
;;   TipKeys (Name[6]) = calm, heart, breath, melody, soul, drawing
;;   TipNames (String[6]) = CALM, HEART RATE, BREATH, YOUR MELODY, YOUR SOUL, YOUR DRAWING
;;   TipStage (int[6]) = 2, 1, 0, 3, -1, 4 · TipTexts (String[6]) = los de RES_ITEMS (journey_content.dsl).
;; Wrappers por CIRUGIA (el DSL elige el overload de MPC; gotcha de SaveProgress): create_node con declaring_class
;;   /Script/Engine.MaterialInstanceDynamic -> JcSetTex(M: MID, T: Texture) y JcSetFade(M: MID, V: float).
;; Reglas del parser: if/for/switch/IsValid/cast AL FINAL de su lista; impuros nunca inline como dato (bind primero);
;; CallFunction propia con self explicito.
;;
;; ===== PASOS DEL TURNO (en orden; un execute_tool_script con try/except por paso grande) =====
;; 1. Nombres: find_node_types para cada ";;?" (Canvas|*, Rendering|*RenderTarget*, CreateDynamicMaterialInstance, String
;;    Concatenate/Len/ParseIntoArray, MakeCanvasUVTri, LinearColorLerp, GetActorOfClass, CastToBP_ResultsArt_SC,
;;    Class|BPResultsArtSC|GetK*, Class|BPBioHub|*). Reemplazar en este archivo (sed) antes de pegar.
;; 2. Material M_JourneyCard_SC (/Game/SoulCharger/Mechanics/Results/): Unlit, BLEND_Additive, TwoSided.
;;    TextureSampleParameter2D "Card" (default /Engine/EngineResources/Black, sampler Color) · Scalar "Fade" 1 · "Gain" 1 ·
;;    "Gamma" 1 (Emissive = pow(Card.rgb, Gamma) * Fade * Gain; Gamma para calibrar sRGB/lineal del RT sin tocar colores).
;;    ✅ Quedo: Gain 1,6 (calibrado con la captura). El pin del Power se llama "Exp" (no "Exponent"): ese error se ESCAPA
;;    del try/except del execute_tool_script y deja el material a medias -> se termino con un segundo script.
;; 3. BP: create(/Game/SoulCharger/Mechanics/Results, BP_JourneyContent_SC, Actor) · componente SCS "Cards"
;;    (ProceduralMeshComponent, sin colision, sin sombra, TranslucencySortPriority 1).
;; 4. Variables. Journey (instance editable): BreathScores float[] [0,62 0,83 1 0,71] · Minutes 0 · (Gain 1: BORRADA) ·
;;    StageColors LinearColor[5] · Cream · Grey · FontPx 24 · bPreviewInEditor false · ClickSound (SoundBase, VR_click1) ·
;;    ClickVol 1 · TipKeys Name[6] · TipNames String[6] · TipStage int[6] · TipTexts String[6].
;;    Z-Journey: RTs (TextureRenderTarget2D[]) · MIDs (MaterialInstanceDynamic[]) · SerCalm, SerHeart, Ser (float[]) ·
;;    SerStage, BandA, BandB, QT (int[]) · QV, QN (Vector[]) · QUV, Pts (Vector2D[]) · Tris (CanvasUVTri[]) ·
;;    StLo StHi StSum Gx0 Gx1 Gyt Gyb Glo Ghi TipK WrapY MinShown (float) · StN (int) · TipKey TipWant (Name) ·
;;    WrapLine (String) · Words (String[]).
;;    Compilar -> defaults en el CDO (arrays incluidos) -> compilar.
;; 5. Funciones (grafos vacios) + params (object params: C = /Script/Engine.Canvas; Hub = BP_BioHub_C; Art = Actor;
;;    M = MaterialInstanceDynamic; T = Texture). Wrappers JcSetTex / JcSetFade por cirugia. Escribir de las hojas hacia
;;    arriba; compilar por tandas.
;; 6. EventGraph: borrar los 3 eventos fantasma del BP nuevo y escribir el EventTick. Construction Script.
;; 7. Verificar en /Game/SoulCharger/Mechanics/Results/Test_Results (lo crea Mesh 3D: panel + PlayerStart; lo comparten
;;    Narrativa y Secuencer; confirmado por Narrativa 2026-09-30): bPreviewInEditor en el CDO (temporal) + colocar el BP
;;    colgado del BP_ResultsArt_SC (AttachToActor, identidad) -> CaptureViewport del editor (las tarjetas se ven sin PIE) ->
;;    calibrar FontPx, Gamma, posiciones. K del marco confirmados: KTitle/KCalm/KHeart/KBreath/KMelody/KTip (0..1).
;;    Fuente: Roboto esta noche (Michroma queda para que Beltran decida: es una descarga).
;;    PIE: Build + SetTip ciclando (log sin errores). Volver bPreviewInEditor a false. Guardar con rutas explicitas.

(fn JcQuad (S Zc W H)
  (bind _hw (* W 0.5))
  (bind _hh (* H 0.5))
  (Utilities|Array|Clear (Variables|Z-Journey|GetQV))
  (Utilities|Array|Clear (Variables|Z-Journey|GetQT))
  (Utilities|Array|Clear (Variables|Z-Journey|GetQN))
  (Utilities|Array|Clear (Variables|Z-Journey|GetQUV))
  (Utilities|Array|Add (Variables|Z-Journey|GetQV) (Math|Vector|MakeVector 0.6 _hw (+ Zc _hh)))
  (Utilities|Array|Add (Variables|Z-Journey|GetQV) (Math|Vector|MakeVector 0.6 (neg _hw) (+ Zc _hh)))
  (Utilities|Array|Add (Variables|Z-Journey|GetQV) (Math|Vector|MakeVector 0.6 (neg _hw) (- Zc _hh)))
  (Utilities|Array|Add (Variables|Z-Journey|GetQV) (Math|Vector|MakeVector 0.6 _hw (- Zc _hh)))
  (Utilities|Array|Add (Variables|Z-Journey|GetQUV) (Math|Vector2D|MakeVector2D 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQUV) (Math|Vector2D|MakeVector2D 1.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQUV) (Math|Vector2D|MakeVector2D 1.0 1.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQUV) (Math|Vector2D|MakeVector2D 0.0 1.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQN) (Math|Vector|MakeVector 1.0 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQN) (Math|Vector|MakeVector 1.0 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQN) (Math|Vector|MakeVector 1.0 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQN) (Math|Vector|MakeVector 1.0 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 0)
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 1)
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 2)
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 0)
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 2)
  (Utilities|Array|Add (Variables|Z-Journey|GetQT) 3)
  (Components|ProceduralMesh|CreateMeshSection (Variables|Default|GetCards) S (Variables|Z-Journey|GetQV) (Variables|Z-Journey|GetQT) (Variables|Z-Journey|GetQN) (Variables|Z-Journey|GetQUV)))

;; 🔴 SIN mips (2026-09-30, turno en la Obra). Con bAutoGenerateMipMaps true el Canvas dibuja SOLO el mip 0: los demas
;;   quedan como al crear el RT (negros). A 1,9 m el cuadro ocupa ~520 px para un RT de 1030 -> se lee el mip 1 -> las 6
;;   tarjetas NEGRAS ("ventanas vacias"). En el editor se veia porque las capturas eran de cerca (mip 0). Gotcha 546.
(fn JcTarget (S Wpx Hpx)
  (bind _rt (Rendering|CreateRenderTarget2D :Width Wpx :Height Hpx :Format "RTF_RGBA8" :ClearColor (Math|Color|MakeLinearColor 0.0 0.0 0.0 0.0) :bAutoGenerateMipMaps false))   ;;?
  (bind _mid (Rendering|Material|CreateDynamicMaterialInstance (Variables|Default|GetCards) :ElementIndex S :SourceMaterial "/Game/SoulCharger/Mechanics/Results/M_JourneyCard_SC.M_JourneyCard_SC"))   ;;?
  (Utilities|Array|Add (Variables|Z-Journey|GetRTs) _rt)
  (Utilities|Array|Add (Variables|Z-Journey|GetMIDs) _mid)
  (CallFunction|JcSetTex self _mid _rt)
  (CallFunction|JcSetFade self _mid 1.0))

(fn JcEnsure ()
  (bind _self self)
  (if (< (Utilities|Array|Length (Variables|Z-Journey|GetRTs)) 6)
    (Components|ProceduralMesh|ClearAllMeshSections (Variables|Default|GetCards))
    (Utilities|Array|Clear (Variables|Z-Journey|GetRTs))
    (Utilities|Array|Clear (Variables|Z-Journey|GetMIDs))
    (CallFunction|JcQuad _self 0 43.25 103.0 9.5)
    (CallFunction|JcQuad _self 1 26.0 103.0 21.0)
    (CallFunction|JcQuad _self 2 3.0 103.0 21.0)
    (CallFunction|JcQuad _self 3 -18.0 103.0 17.0)
    (CallFunction|JcQuad _self 4 -38.0 103.0 19.0)
    (CallFunction|JcQuad _self 5 62.5 92.0 17.0)
    (CallFunction|JcTarget _self 0 1030 95)
    (CallFunction|JcTarget _self 1 1030 210)
    (CallFunction|JcTarget _self 2 1030 210)
    (CallFunction|JcTarget _self 3 1030 170)
    (CallFunction|JcTarget _self 4 1030 190)
    (CallFunction|JcTarget _self 5 920 170)))

;; ---------------- datos
(fn JcData ()
  (bind _hub (Utilities|GetActorOfClass "/Game/SoulCharger/Core/Signals/BP_BioHub.BP_BioHub_C"))   ;;? (puede ser Actor|GetActorofClass)
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerCalm))
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerHeart))
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerStage))
  (Utilities|IsValid _hub
    (:"Is Valid" (CallFunction|JcFromHub self _hub))
    (:"Is Not Valid" (CallFunction|JcSample self))))

(fn JcFromHub (Hub)
  (bind _n (Math|Integer|Min(Integer) (+ (Class|BPBioHub|GetCurrentBin Hub) 1) 180))
  (Variables|Z-Journey|SetMinShown (select (> (Variables|Journey|GetMinutes) 0.0) (Variables|Journey|GetMinutes) (/ (* (Math|Conversions|ToFloat(Integer) _n) (Class|BPBioHub|GetBinSeconds Hub)) 60.0)))
  (if (< _n 20)
    (CallFunction|JcSample self)
    (else
      (for _i (range _n)
        (bind _hc (Class|BPBioHub|BinHasCalm Hub _i))
        (bind _vc (Class|BPBioHub|GetCalmBinAvg Hub _i))
        (bind _hh (Class|BPBioHub|BinHasHeart Hub _i))
        (bind _vh (Class|BPBioHub|GetHeartBinAvg Hub _i))
        (Utilities|Array|Add (Variables|Z-Journey|GetSerCalm) (select _hc _vc -1.0))
        (Utilities|Array|Add (Variables|Z-Journey|GetSerHeart) (select _hh _vh -1.0))
        (Utilities|Array|Add (Variables|Z-Journey|GetSerStage) (Utilities|Array|Get(acopy) (Class|BPBioHub|GetBinStage Hub) _i))))))

;; muestras de la web (resSeries + RES_SPANS), 180 casillas
(fn JcSample ()
  (Variables|Z-Journey|SetMinShown (select (> (Variables|Journey|GetMinutes) 0.0) (Variables|Journey|GetMinutes) 14.0))
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerCalm))
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerHeart))
  (Utilities|Array|Clear (Variables|Z-Journey|GetSerStage))
  (for _i (range 180)
    (CallFunction|JcSampleOne self _i)))

(fn JcSampleOne (I)
  (bind _t (/ (Math|Conversions|ToFloat(Integer) I) 179.0))
  (bind _s1 (Math|Float|Clamp(Float) (* _t 1.1)))
  (bind _sm1 (* _s1 (* _s1 (- 3.0 (* 2.0 _s1)))))
  (bind _st (* _t (* _t (- 3.0 (* 2.0 _t)))))
  (bind _a1 (Math|Float|Clamp(Float) (/ (- _t 0.44) 0.05)))
  (bind _b1 (Math|Float|Clamp(Float) (/ (- _t 0.57) 0.05)))
  (bind _bumpA (* (* _a1 (* _a1 (- 3.0 (* 2.0 _a1)))) (- 1.0 (* _b1 (* _b1 (- 3.0 (* 2.0 _b1)))))))
  (bind _a2 (Math|Float|Clamp(Float) (/ (- _t 0.62) 0.05)))
  (bind _b2 (Math|Float|Clamp(Float) (/ (- _t 0.75) 0.05)))
  (bind _bumpB (* (* _a2 (* _a2 (- 3.0 (* 2.0 _a2)))) (- 1.0 (* _b2 (* _b2 (- 3.0 (* 2.0 _b2)))))))
  (Utilities|Array|Add (Variables|Z-Journey|GetSerCalm) (Math|Float|Clamp(Float) (+ (+ (+ 0.3 (* 0.38 _sm1)) (* (* 0.09 (Math|Trig|Sin(Radians) (+ (* _t 19.0) 1.0))) (- 1.0 (* 0.5 _t)))) (+ (* 0.045 (Math|Trig|Sin(Radians) (+ (* _t 57.0) 2.0))) (- (* 0.14 _bumpA) (* 0.08 _bumpB))))))
  (Utilities|Array|Add (Variables|Z-Journey|GetSerHeart) (+ (- 83.0 (* 17.0 _st)) (+ (+ (* 4.5 (Math|Trig|Sin(Radians) (+ (* _t 14.0) 0.5))) (* 2.0 (Math|Trig|Sin(Radians) (* _t 41.0)))) (- (* 5.0 _bumpB) (* 3.0 _bumpA)))))
  (Utilities|Array|Add (Variables|Z-Journey|GetSerStage) (select (< _t 0.10) -1 (select (< _t 0.28) 0 (select (< _t 0.44) 1 (select (< _t 0.62) 2 (select (< _t 0.80) 3 (select (< _t 0.97) 4 -1))))))))

;; ---------------- estadisticas (saltando huecos = -1)
(fn JcStats (Heart)
  (Variables|Z-Journey|SetStLo 1000000.0)
  (Variables|Z-Journey|SetStHi -1000000.0)
  (Variables|Z-Journey|SetStSum 0.0)
  (Variables|Z-Journey|SetStN 0)
  (for _v (select Heart (Variables|Z-Journey|GetSerHeart) (Variables|Z-Journey|GetSerCalm))
    (CallFunction|JcStatOne self _v)))

(fn JcStatOne (V)
  (if (>= V 0.0)
    (Variables|Z-Journey|SetStLo (Math|Float|Min(Float) (Variables|Z-Journey|GetStLo) V))
    (Variables|Z-Journey|SetStHi (Math|Float|Max(Float) (Variables|Z-Journey|GetStHi) V))
    (Variables|Z-Journey|SetStSum (+ (Variables|Z-Journey|GetStSum) V))
    (Variables|Z-Journey|SetStN (+ (Variables|Z-Journey|GetStN) 1))))

;; ---------------- primitivas de dibujo (Px = alto de la fuente en px; Align 0 izq, 1 der, 2 centro)
(fn JcText (C Txt X Top Px Col Align)
  (bind _sc (/ Px (Variables|Journey|GetFontPx)))
  (bind _w (.x (Canvas|TextSize C :RenderFont "/Engine/EngineFonts/Roboto.Roboto" :RenderText Txt :Scale (Math|Vector2D|MakeVector2D _sc _sc))))   ;;?
  (Canvas|DrawText C :RenderFont "/Engine/EngineFonts/Roboto.Roboto" :RenderText Txt :ScreenPosition (Math|Vector2D|MakeVector2D (select (== Align 1) (- X _w) (select (== Align 2) (- X (* 0.5 _w)) X)) Top) :Scale (Math|Vector2D|MakeVector2D _sc _sc) :RenderColor Col))   ;;?

(fn JcRect (C X Y W H Col)
  (Canvas|DrawTexture C :ScreenPosition (Math|Vector2D|MakeVector2D X Y) :ScreenSize (Math|Vector2D|MakeVector2D W H) :CoordinatePosition (Math|Vector2D|MakeVector2D 0.0 0.0) :CoordinateSize (Math|Vector2D|MakeVector2D 1.0 1.0) :RenderColor Col :BlendMode "BLEND_Additive"))   ;;?

(fn JcDash (C X0 X1 Y Th Col)
  (for _k (range (Math|Float|Truncate (/ (- X1 X0) 14.0)))   ;;? Truncate
    (Canvas|DrawLine C :ScreenPositionA (Math|Vector2D|MakeVector2D (+ X0 (* 14.0 (Math|Conversions|ToFloat(Integer) _k))) Y) :ScreenPositionB (Math|Vector2D|MakeVector2D (Math|Float|Min(Float) X1 (+ X0 (+ 7.0 (* 14.0 (Math|Conversions|ToFloat(Integer) _k))))) Y) :Thickness Th :RenderColor Col)))

(fn JcRing (C X Y R Th Col)
  (for _k (range 48)
    (Canvas|DrawLine C :ScreenPositionA (Math|Vector2D|MakeVector2D (+ X (* R (Math|Trig|Cos(Degrees) (* 7.5 (Math|Conversions|ToFloat(Integer) _k))))) (+ Y (* R (Math|Trig|Sin(Degrees) (* 7.5 (Math|Conversions|ToFloat(Integer) _k)))))) :ScreenPositionB (Math|Vector2D|MakeVector2D (+ X (* R (Math|Trig|Cos(Degrees) (* 7.5 (+ 1.0 (Math|Conversions|ToFloat(Integer) _k)))))) (+ Y (* R (Math|Trig|Sin(Degrees) (* 7.5 (+ 1.0 (Math|Conversions|ToFloat(Integer) _k))))))) :Thickness Th :RenderColor Col)))

(fn JcDisc (C X Y R Col)
  (Canvas|DrawPolygon C :ScreenPosition (Math|Vector2D|MakeVector2D X Y) :Radius (Math|Vector2D|MakeVector2D R R) :NumberOfSides 48 :RenderColor Col))   ;;?

;; lighten(col, k) de la web: mezcla con blanco EN sRGB. Aproximacion en lineal (suficiente a este tamano):
;; lerp(col, 1, k) sobre el lineal, con k un poco mas bajo (k*0,8). Calibrar con la captura.
;; Antes de escribirla: add_struct_function_param(graph JcLighten, "Out", /Script/CoreUObject.LinearColor, input_param false).
;; 🔴 El escritor por tandas la SALTEO: la funcion con parametro de salida ya trae 2 nodos (entrada + return) y el script la
;;   tomo por "ya escrita" -> devolvia NEGRO y los anillos llenos salian oscuros. Se escribio a mano (esta version).
;;   Un "grafo vacio" con salida tiene 2 nodos, no 1: contar nodos de cuerpo, no nodos totales.
(fn JcLighten (Col K)
  (return (Math|Color|Lerp(LinearColor) Col (Utilities|Struct|MakeLinearColor 1.0 1.0 1.0 1.0) (* K 0.8))))

;; ---------------- una tarjeta: Begin/End en la misma funcion; el cuerpo en JcPaint (el Context no sale de aca)
(fn JcCard (S)
  (bind _rt (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetRTs) S))
  (Rendering|ClearRenderTarget2D :TextureRenderTarget _rt :ClearColor (Math|Color|MakeLinearColor 0.0 0.0 0.0 0.0))   ;;?
  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget _rt))   ;;?
  (CallFunction|JcPaint self _cv (.x _sz) (.y _sz) S)
  (Rendering|EndDrawCanvastoRenderTarget :Context _ctx))   ;;?

(fn JcPaint (C W H S)
  (switch int S
    (:0 (CallFunction|JcTitle self C W H))
    (:1 (CallFunction|JcGraph self C W H false))
    (:2 (CallFunction|JcGraph self C W H true))
    (:3 (CallFunction|JcBreath self C W H))
    (:4 (CallFunction|JcMelody self C W H))
    (:5 (CallFunction|JcTipDraw self C W H))
    (:Default)))

;; ---------------- tarjetas. Colores: StageColors[i] (lineal) · Cream · Grey. Web: base del texto -> top = base - 0,8*px.
(fn JcTitle (C W H)
  (bind _mins (Math|Conversions|ToString(Integer) (Math|Float|Round (Variables|Z-Journey|GetMinShown))))
  (bind _line (Utilities|String|Concatenate _mins " min  ·  5 stages  ·  5 lights"))   ;;? Concatenate / Append
  (CallFunction|JcText self C "YOUR JOURNEY THROUGH SOUL CHARGER" (* 0.5 W) 21.0 29.0 (Variables|Journey|GetCream) 2)
  (CallFunction|JcText self C _line (* 0.5 W) 60.0 18.0 (* (Variables|Journey|GetCream) 0.6) 2))

;; Grafico: JcGraph arma la escala y los textos; JcGraphBody dibuja (Y(v) inline con las G*)
(fn JcGraph (C W H Heart)
  (CallFunction|JcStats self Heart)
  (bind _col (Utilities|Array|Get(acopy) (Variables|Journey|GetStageColors) (select Heart 1 2)))
  (bind _lo (Variables|Z-Journey|GetStLo))
  (bind _hi (Variables|Z-Journey|GetStHi))
  (bind _avg (/ (Variables|Z-Journey|GetStSum) (Math|Float|Max(Float) 1.0 (Math|Conversions|ToFloat(Integer) (Variables|Z-Journey|GetStN)))))
  (bind _k (select Heart 1.0 100.0))
  (bind _pad (Math|Float|Max(Float) (* (- _hi _lo) 0.12) (select Heart 1.0 0.01)))
  (bind _yb (- H 42.0))
  (bind _yhi (- _yb (* (- _yb 66.0) (/ (- _hi (- _lo _pad)) (- (+ _hi _pad) (- _lo _pad))))))
  (bind _ylo (- _yb (* (- _yb 66.0) (/ (- _lo (- _lo _pad)) (- (+ _hi _pad) (- _lo _pad))))))
  (bind _meta (Utilities|String|Concatenate "average " (Utilities|String|Concatenate (Math|Conversions|ToString(Integer) (Math|Float|Round (* _avg _k))) (select Heart " bpm" " / 100"))))   ;;?
  (Variables|Z-Journey|SetGx0 104.0)
  (Variables|Z-Journey|SetGx1 (- W 26.0))
  (Variables|Z-Journey|SetGyt 66.0)
  (Variables|Z-Journey|SetGyb _yb)
  (Variables|Z-Journey|SetGlo (- _lo _pad))
  (Variables|Z-Journey|SetGhi (+ _hi _pad))
  (CallFunction|JcText self C (select Heart "HEART RATE" "CALM") 26.0 24.0 20.0 _col 0)
  (CallFunction|JcText self C _meta (- W 26.0) 25.0 19.0 (* (Variables|Journey|GetCream) 0.72) 1)
  (CallFunction|JcDash self C 104.0 (- W 26.0) _yhi 1.6 (* (Variables|Journey|GetGrey) 0.28))
  (CallFunction|JcDash self C 104.0 (- W 26.0) _ylo 1.6 (* (Variables|Journey|GetGrey) 0.28))
  (CallFunction|JcText self C (Math|Conversions|ToString(Integer) (Math|Float|Round (* _hi _k))) 88.0 (- _yhi 10.5) 21.0 (* (Variables|Journey|GetCream) 0.9) 1)
  (CallFunction|JcText self C (Math|Conversions|ToString(Integer) (Math|Float|Round (* _lo _k))) 88.0 (- _ylo 10.5) 21.0 (* (Variables|Journey|GetCream) 0.9) 1)
  (CallFunction|JcGraphBody self C W H Heart _col))

(fn JcGraphBody (C W H Heart Col)
  (bind _self self)
  (bind _lite (CallFunction|JcLighten _self Col 0.45))
  (CallFunction|JcPts _self Heart)
  (CallFunction|JcAreaTris _self Col)
  (Canvas|DrawTriangles C :Triangles (Variables|Z-Journey|GetTris))   ;;? (K2_DrawTriangle; RenderTexture None = color de vertice)
  (CallFunction|JcLine _self C (* Col 0.4) 11.0)
  (CallFunction|JcLine _self C _lite 4.0)
  (CallFunction|JcBand _self C W H)
  (CallFunction|JcText _self C "start" 26.0 (- H 26.0) 15.0 (* (Variables|Journey|GetCream) 0.5) 0)
  (CallFunction|JcText _self C "end" (- W 6.0) (- H 40.0) 15.0 (* (Variables|Journey|GetCream) 0.5) 1))

;; Pts: una casilla con dato -> (X(i), Y(v suavizado)); suavizado = promedio de los vecinos validos (i-1, i, i+1).
(fn JcPts (Heart)
  (Utilities|Array|Clear (Variables|Z-Journey|GetPts))
  (Variables|Z-Journey|SetSer (select Heart (Variables|Z-Journey|GetSerHeart) (Variables|Z-Journey|GetSerCalm)))
  (for _i (range (Utilities|Array|Length (Variables|Z-Journey|GetSer)))
    (CallFunction|JcPtOne self _i)))

(fn JcPtOne (I)
  (bind _d (Variables|Z-Journey|GetSer))
  (bind _n (Utilities|Array|Length _d))
  (bind _v (Utilities|Array|Get(acopy) _d I))
  (bind _vp (Utilities|Array|Get(acopy) _d (Math|Integer|Max(Integer) 0 (- I 1))))
  (bind _vn (Utilities|Array|Get(acopy) _d (Math|Integer|Min(Integer) (- _n 1) (+ I 1))))
  (bind _wp (select (>= _vp 0.0) 1.0 0.0))
  (bind _wn (select (>= _vn 0.0) 1.0 0.0))
  (bind _vs (/ (+ _v (+ (* _vp _wp) (* _vn _wn))) (+ 1.0 (+ _wp _wn))))
  (bind _x (+ (Variables|Z-Journey|GetGx0) (* (- (Variables|Z-Journey|GetGx1) (Variables|Z-Journey|GetGx0)) (/ (Math|Conversions|ToFloat(Integer) I) (Math|Float|Max(Float) 1.0 (Math|Conversions|ToFloat(Integer) (- _n 1)))))))
  (bind _y (- (Variables|Z-Journey|GetGyb) (* (- (Variables|Z-Journey|GetGyb) (Variables|Z-Journey|GetGyt)) (/ (- _vs (Variables|Z-Journey|GetGlo)) (- (Variables|Z-Journey|GetGhi) (Variables|Z-Journey|GetGlo))))))
  (if (>= _v 0.0)
    (Utilities|Array|Add (Variables|Z-Journey|GetPts) (Math|Vector2D|MakeVector2D _x _y))))

;; Area: dos triangulos por par de puntos, del trazo al piso (Gyb). Arriba Col*0,33 (el 0x55 de la web), abajo 0.
(fn JcAreaTris (Col)
  (Utilities|Array|Clear (Variables|Z-Journey|GetTris))
  (for _i (range (- (Utilities|Array|Length (Variables|Z-Journey|GetPts)) 1))
    (CallFunction|JcTriPair self _i (* Col 0.33))))

(fn JcTriPair (I Top)
  (bind _a (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetPts) I))
  (bind _b (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetPts) (+ I 1)))
  (bind _yb (Variables|Z-Journey|GetGyb))
  (bind _z (Math|Color|MakeLinearColor 0.0 0.0 0.0 0.0))
  (Utilities|Array|Add (Variables|Z-Journey|GetTris) (Utilities|Struct|MakeCanvasUVTri :V0_Pos _a :V0_Color Top :V1_Pos _b :V1_Color Top :V2_Pos (Math|Vector2D|MakeVector2D (.x _b) _yb) :V2_Color _z))   ;;?
  (Utilities|Array|Add (Variables|Z-Journey|GetTris) (Utilities|Struct|MakeCanvasUVTri :V0_Pos _a :V0_Color Top :V1_Pos (Math|Vector2D|MakeVector2D (.x _b) _yb) :V1_Color _z :V2_Pos (Math|Vector2D|MakeVector2D (.x _a) _yb) :V2_Color _z)))

(fn JcLine (C Col Th)
  (for _i (range (- (Utilities|Array|Length (Variables|Z-Journey|GetPts)) 1))
    (Canvas|DrawLine C :ScreenPositionA (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetPts) _i) :ScreenPositionB (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetPts) (+ _i 1)) :Thickness Th :RenderColor Col)))

;; Banda de etapas: UN recorrido de SerStage anota primera (BandA) y ultima (BandB) casilla de cada etapa (Blueprint no tiene
;; FindLast); despues un rect por etapa (yb = H-22, alto 6), color*0,85, 2 px de margen por lado.
(fn JcBand (C W H)
  (bind _self self)
  (CallFunction|JcBandReset _self)
  (CallFunction|JcBandScan _self)
  (CallFunction|JcBandDraw _self C W H))

(fn JcBandReset ()
  (Utilities|Array|Clear (Variables|Z-Journey|GetBandA))
  (Utilities|Array|Clear (Variables|Z-Journey|GetBandB))
  (for _s (range 5)
    (Utilities|Array|Add (Variables|Z-Journey|GetBandA) -1)
    (Utilities|Array|Add (Variables|Z-Journey|GetBandB) -1)))

(fn JcBandScan ()
  (for _i (range (Utilities|Array|Length (Variables|Z-Journey|GetSerStage)))
    (CallFunction|JcBandMark self _i (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetSerStage) _i))))

(fn JcBandMark (I S)
  (if (and (>= S 0) (< S 5))
    (Utilities|Array|SetArrayElem (Variables|Z-Journey|GetBandA) S (select (< (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetBandA) S) 0) I (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetBandA) S)))
    (Utilities|Array|SetArrayElem (Variables|Z-Journey|GetBandB) S I)))

(fn JcBandDraw (C W H)
  (for _s (range 5)
    (CallFunction|JcBandOne self C W H _s)))

(fn JcBandOne (C W H S)
  (bind _n (Math|Conversions|ToFloat(Integer) (Math|Integer|Max(Integer) 1 (Utilities|Array|Length (Variables|Z-Journey|GetSerStage)))))
  (bind _first (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetBandA) S))
  (bind _last (Utilities|Array|Get(acopy) (Variables|Z-Journey|GetBandB) S))
  (bind _x0 (Variables|Z-Journey|GetGx0))
  (bind _x1 (Variables|Z-Journey|GetGx1))
  (bind _a (/ (Math|Conversions|ToFloat(Integer) _first) _n))
  (bind _b (/ (Math|Conversions|ToFloat(Integer) (+ _last 1)) _n))
  (if (>= _first 0)
    (CallFunction|JcRect self C (+ _x0 (+ (* (- _x1 _x0) _a) 2.0)) (- H 22.0) (- (* (- _x1 _x0) (- _b _a)) 4.0) 6.0 (* (Utilities|Array|Get(acopy) (Variables|Journey|GetStageColors) S) 0.85))))

;; Respiracion
(fn JcBreath (C W H)
  (bind _col (Utilities|Array|Get(acopy) (Variables|Journey|GetStageColors) 0))
  (bind _n (Utilities|Array|Length (Variables|Journey|GetBreathScores)))
  (bind _meta (Utilities|String|Concatenate (Math|Conversions|ToString(Integer) _n) " cycles  ·  inhale, hold, exhale"))   ;;?
  (CallFunction|JcText self C "BREATH" 26.0 24.0 20.0 _col 0)
  (CallFunction|JcText self C _meta (- W 26.0) 25.0 19.0 (* (Variables|Journey|GetCream) 0.72) 1)
  (for _i (range _n)
    (CallFunction|JcBreathOne self C W H _i _n _col)))

(fn JcBreathOne (C W H I N Col)
  (bind _self self)
  (bind _s (Utilities|Array|Get(acopy) (Variables|Journey|GetBreathScores) I))
  (bind _x1 (- W 70.0))
  (bind _cy (* H 0.6))
  ;; 🔴 _d protegido: `select` evalua LAS DOS ramas y el bind de _x se re-evalua en cada uso (4) -> con N = 1 salian
  ;;    4 "Divide by zero" por cuadro de Build (la corrida larga de la Obra, 2026-09-30).
  (bind _d (Math|Float|Max(Float) 1.0 (Math|Conversions|ToFloat(Integer) (- N 1))))
  (bind _R (Math|Float|Min(Float) 46.0 (* (/ (- _x1 70.0) _d) 0.36)))
  (bind _x (select (> N 1) (+ 70.0 (* (- _x1 70.0) (/ (Math|Conversions|ToFloat(Integer) I) _d))) (* 0.5 W)))
  (bind _full (>= _s 0.95))
  (bind _r (select _full (- _R 2.5) (Math|Float|Max(Float) 4.0 (* _s (- _R 9.0)))))
  (bind _lite (CallFunction|JcLighten _self Col 0.5))
  (bind _core (CallFunction|JcLighten _self Col 0.75))
  (CallFunction|JcBreathGlow _self C _x _cy _R _r Col _full)
  (CallFunction|JcDisc _self C _x _cy _r Col)
  (CallFunction|JcDisc _self C (- _x (* 0.25 _r)) (- _cy (* 0.3 _r)) (* 0.6 _r) (* _core 0.45))
  (CallFunction|JcRing _self C _x _cy _R (select _full 4.5 3.2) (select _full _lite (* Col 0.8))))

;; 🔴 El brillo del anillo perfecto va PRIMERO. El Canvas sobre un RT no suma: cada dibujo PISA lo que hay debajo (el
;;   material es aditivo, pero el RT no). En la version anterior el disco de brillo (* Col 0.18) se dibujaba al final y
;;   tapaba el anillo y el nucleo -> el ciclo perfecto se veia MAS apagado que los otros. Orden: brillo -> disco -> nucleo -> anillo.
(fn JcBreathGlow (C X Y R Rd Col Full)
  (bind _self self)
  (if Full
    (CallFunction|JcDisc _self C X Y (* Rd 1.18) (* Col 0.18))
    (CallFunction|JcRing _self C X Y (+ R 9.0) 8.0 (* Col 0.1))
    (CallFunction|JcRing _self C X Y (+ R 4.0) 6.0 (* Col 0.22))))

;; Melodia: cabecera + "playing" con una corchea dibujada (Roboto no trae el glifo)
(fn JcMelody (C W H)
  (bind _col (Utilities|Array|Get(acopy) (Variables|Journey|GetStageColors) 3))
  (bind _cr (* (Variables|Journey|GetCream) 0.72))
  (bind _xm (- W 26.0))
  (CallFunction|JcText self C "YOUR MELODY" 26.0 24.0 20.0 _col 0)
  (CallFunction|JcText self C "playing" _xm 25.0 19.0 _cr 1)
  (CallFunction|JcDisc self C (- _xm 96.0) 37.0 4.5 _cr)
  (Canvas|DrawLine C :ScreenPositionA (Math|Vector2D|MakeVector2D (- _xm 91.8) 37.0) :ScreenPositionB (Math|Vector2D|MakeVector2D (- _xm 91.8) 21.0) :Thickness 1.8 :RenderColor _cr)
  (Canvas|DrawLine C :ScreenPositionA (Math|Vector2D|MakeVector2D (- _xm 91.8) 21.0) :ScreenPositionB (Math|Vector2D|MakeVector2D (- _xm 85.0) 26.0) :Thickness 1.8 :RenderColor _cr))

;; Tip: marca de color + nombre + texto con corte por palabras (JcWrapLoop: el for va ultimo; JcWrapFlush: el ultimo renglon)
(fn JcTipDraw (C W H)
  (bind _i (Utilities|Array|FindItem (Variables|Journey|GetTipKeys) (Variables|Z-Journey|GetTipKey)))
  (if (>= _i 0)
    (CallFunction|JcTipBody self C W H _i)))

(fn JcTipBody (C W H I)
  (bind _self self)
  (bind _stg (Utilities|Array|Get(acopy) (Variables|Journey|GetTipStage) I))
  (bind _col (select (>= _stg 0) (Utilities|Array|Get(acopy) (Variables|Journey|GetStageColors) (Math|Integer|Max(Integer) 0 _stg)) (Variables|Journey|GetCream)))
  (CallFunction|JcRect _self C 34.0 30.0 5.0 (- H 60.0) _col)
  (CallFunction|JcText _self C (Utilities|Array|Get(acopy) (Variables|Journey|GetTipNames) I) 60.0 35.0 19.0 _col 0)
  (Variables|Z-Journey|SetWrapLine "")
  (Variables|Z-Journey|SetWrapY 68.0)
  (Variables|Z-Journey|SetWords (Utilities|String|ParseIntoArray (Utilities|Array|Get(acopy) (Variables|Journey|GetTipTexts) I) " " true))   ;;?
  (CallFunction|JcWrapLoop _self C W)
  (CallFunction|JcWrapFlush _self C))

(fn JcWrapLoop (C W)
  (for _wd (Variables|Z-Journey|GetWords)
    (CallFunction|JcWrapWord self C W _wd)))

(fn JcWrapWord (C W Wd)
  (bind _line (Variables|Z-Journey|GetWrapLine))
  (bind _try (select (== (Utilities|String|Len _line) 0) Wd (Utilities|String|Concatenate _line (Utilities|String|Concatenate " " Wd))))   ;;? Len
  (bind _sc (/ 23.0 (Variables|Journey|GetFontPx)))
  (bind _tw (.x (Canvas|TextSize C :RenderFont "/Engine/EngineFonts/Roboto.Roboto" :RenderText _try :Scale (Math|Vector2D|MakeVector2D _sc _sc))))
  (if (and (> _tw (- W 96.0)) (> (Utilities|String|Len _line) 0))
    (CallFunction|JcText self C _line 60.0 (Variables|Z-Journey|GetWrapY) 23.0 (Variables|Journey|GetCream) 0)
    (Variables|Z-Journey|SetWrapY (+ (Variables|Z-Journey|GetWrapY) 31.0))
    (Variables|Z-Journey|SetWrapLine Wd)
    (else
      (Variables|Z-Journey|SetWrapLine _try))))

(fn JcWrapFlush (C)
  (if (> (Utilities|String|Len (Variables|Z-Journey|GetWrapLine)) 0)
    (CallFunction|JcText self C (Variables|Z-Journey|GetWrapLine) 60.0 (Variables|Z-Journey|GetWrapY) 23.0 (Variables|Journey|GetCream) 0)))

;; ---------------- API y reloj
(fn Build ()
  (bind _self self)
  (CallFunction|JcEnsure _self)
  (CallFunction|JcData _self)
  (Variables|Z-Journey|SetTipKey "None")
  (Variables|Z-Journey|SetTipWant "None")
  (Variables|Z-Journey|SetTipK 0.0)
  (CallFunction|JcCard _self 0)
  (CallFunction|JcCard _self 1)
  (CallFunction|JcCard _self 2)
  (CallFunction|JcCard _self 3)
  (CallFunction|JcCard _self 4)
  (CallFunction|JcCard _self 5)
  (Actor|Tick|SetActorTickEnabled _self true))

(fn SetTip (Key)
  (if (!= Key (Variables|Z-Journey|GetTipWant))
    (Variables|Z-Journey|SetTipWant Key)
    (CallFunction|JcTipSound self Key)))

(fn JcTipSound (Key)
  (if (!= Key "None")
    (Audio|PlaySound2D (Variables|Journey|GetClickSound) (Variables|Journey|GetClickVol))))

;; Un arreglo VACIO no borra: queda lo que habia (la muestra del CDO). "Sin datos: muestras de la web" (diseno).
(fn SetBreathScores (Scores)
  (if (> (Utilities|Array|Length Scores) 0)
    (Variables|Journey|SetBreathScores Scores)))

(fn SetMinutes (M)
  (Variables|Journey|SetMinutes M))

;; el texto: se funde, cambia y vuelve (6/s bajando, 5/s subiendo, como la web)
(fn JcTipStep (Dt)
  (if (!= (Variables|Z-Journey|GetTipWant) (Variables|Z-Journey|GetTipKey))
    (Variables|Z-Journey|SetTipK (Math|Float|Max(Float) 0.0 (- (Variables|Z-Journey|GetTipK) (* Dt 6.0))))
    (CallFunction|JcTipSwap self)
    (else
      (Variables|Z-Journey|SetTipK (Math|Float|Min(Float) 1.0 (+ (Variables|Z-Journey|GetTipK) (* Dt 5.0)))))))

(fn JcTipSwap ()
  (if (<= (Variables|Z-Journey|GetTipK) 0.0)
    (Variables|Z-Journey|SetTipKey (Variables|Z-Journey|GetTipWant))
    (CallFunction|JcCard self 5)))

;; fundidos: los K del marco (Mesh 3D) -> Fade de cada seccion; el tip ademas * smooth(TipK)
(fn JcFadeStep ()
  (bind _art (Actor|GetAttachParentActor))
  (bind _tk (Variables|Z-Journey|GetTipK))
  (bind _ts (* _tk (* _tk (- 3.0 (* 2.0 _tk)))))
  (bind _m (Variables|Z-Journey|GetMIDs))
  (if (>= (Utilities|Array|Length _m) 6)
    (CallFunction|JcFadeFrom self _art _ts)))

;; Art = el padre (BP_ResultsArt_SC de Mesh 3D). Sin marco (test suelto): todo a 1 y el tip con Ts.
;; Nombres de los K: CONFIRMAR con find_node_types("Class|BPResultsArtSC|GetK") en el turno.
(fn JcFadeFrom (Art Ts)
  (bind _ra (Utilities|Casting|CastToBP_ResultsArt_SC :Object Art)
    (:then
      (CallFunction|JcFadeK self (Class|BPResultsArtSC|GetKTitle _ra) (Class|BPResultsArtSC|GetKCalm _ra) (Class|BPResultsArtSC|GetKHeart _ra) (Class|BPResultsArtSC|GetKBreath _ra) (Class|BPResultsArtSC|GetKMelody _ra) (* (Class|BPResultsArtSC|GetKTip _ra) Ts)))
    (:CastFailed
      (CallFunction|JcFadeK self 1.0 1.0 1.0 1.0 1.0 Ts))))

(fn JcFadeK (KT KC KH KB KM KTip)
  (bind _m (Variables|Z-Journey|GetMIDs))
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 0) KT)
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 1) KC)
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 2) KH)
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 3) KB)
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 4) KM)
  (CallFunction|JcSetFade self (Utilities|Array|Get(acopy) _m 5) KTip))

(event EventTick (DeltaSeconds)
  (CallFunction|JcFadeStep self)
  (CallFunction|JcTipStep self (Math|Float|Min(Float) DeltaSeconds 0.0333)))

(fn ConstructionScript ()
  (if (Variables|Journey|GetPreviewInEditor)
    (CallFunction|Build)))
