;; BP_AttractStreams_SC (Test_AttractingHang, 2026-11-04) - fuente de los grafos. (G X) = getter, (S X v) = setter;
;; gen_streams_dsl.py los expande con la categoria de cada variable y escribe streams_dsl.json. Un bloque ;;@ = un grafo.
;; Mecanica (Beltran 11-04, con boceto): una ameba varios metros al frente. Cada nota del hang abre un chorro nuevo de
;; particulas pequenas que sale de un solo punto de la ameba, se acerca suave y, sin chocar, se abre en una burbuja que
;; envuelve al usuario (un campo protector). El chorro queda constante: mas notas, mas chorros, mas particulas.
;; Cada chorro = un StaticMeshComponent de SM_AttractMotes_SC con M_AttractMote_SC: TODO el movimiento lo calcula el
;; material; el BP solo escribe Custom Primitive Data (8 vectores, ver gen_mote_material.py). El hang no se toca: se lee
;; su LastPluck (una entrada por voz) y su NoteColor.

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|AsBoot))
(event EventTick (DeltaSeconds)
  (CallFunction|AsTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

;;@ UserConstructionScript
(fn ConstructionScript ()
  (CallFunction|AsBuild))

;;@ AsBuild
;; Crea MaxStreams chorros (ocultos). En el editor muestra PreviewStreams ya formados (arrancaron hace 600 s), con el ojo en
;; PreviewEye (local) y la ameba donde este, asi la forma se ajusta mirando sin Play.
(fn AsBuild ()
  (Utilities|Array|Clear (G Streams))
  (S Eye (Math|Transform|TransformLocation (Transformation|GetActorTransform) (G PreviewEye)))
  (CallFunction|AsEmitUpdate)
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (bind emitl (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (G EmitW)))
  (for i (range (G MaxStreams))
    (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
    (Components|StaticMesh|SetStaticMesh c (G MoteMesh))
    (Rendering|Material|SetMaterial c 0 (G MoteMat))
    (Collision|SetCollisionEnabled c "NoCollision")
    (Rendering|SetCastShadow c false)
    (Utilities|Array|Add (G Streams) c)
    (CallFunction|AsLook :Comp c)
    (bind hue (+ 20.0 (* 47.0 (Math|Conversions|ToFloat(Integer) i))))
    (CallFunction|AsStart :Comp c :T0 (- now 600.0) :Col (Math|Color|HSVtoRGB hue 0.55 1.0 1.0) :Seed hue)
    (CallFunction|AsPlace :Comp c :EyeL (G PreviewEye) :EmitL emitl)
    (Rendering|SetVisibility c (< i (G PreviewStreams)) false)))

;;@ AsLook
;; Las perillas compartidas de la forma y la luz (K1..K4 = CPD 16..31).
(fn AsLook (Comp)
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 16 (Math|Vector4|MakeVector4 (G Life) (G Count) (G Travel) (G Bend)))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 20 (Math|Vector4|MakeVector4 (G Spread) (G Swirl) (G Wobble) (G WobbleHz)))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 24 (Math|Vector4|MakeVector4 (G Jitter) (G ShellNoise) (G CenterDrop) (G FadeIn)))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 28 (Math|Vector4|MakeVector4 (G Size) (G MinAngle) (G FadeOut) (G Brightness))))

;;@ AsStart
;; Arranca un chorro: T0 (reloj del mundo = View.GameTime del material), semilla propia (su curva, su giro), color de la nota.
;; Seed: al azar en Play (AsAdd); fija por chorro en la vista previa (AsBuild), asi la previa no se re-sortea al tocar perillas.
(fn AsStart (Comp T0 Col Seed)
  (bind (r g b a) (Utilities|Struct|BreakLinearColor Col))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 0 (Math|Vector4|MakeVector4 T0 Seed 0.0 0.0))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 4 (Math|Vector4|MakeVector4 r g b (G ColorPow)))
  (Rendering|SetVisibility Comp true false))

;;@ AsPlace
;; Donde esta el usuario (ojo, local del actor) y de donde sale el chorro (local).
(fn AsPlace (Comp EyeL EmitL)
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 8 (Math|Vector4|MakeVector4 (.x EyeL) (.y EyeL) (.z EyeL) (G Radius)))
  (Rendering|Material|SetCustomPrimitiveDataVector4 Comp 12 (Math|Vector4|MakeVector4 (.x EmitL) (.y EmitL) (.z EmitL) (G Squash))))

;;@ AsEmitUpdate
;; El punto de emision: el borde de la ameba que mira al usuario. Sin ameba, NoAmoebaAt (local del actor).
(fn AsEmitUpdate ()
  (Utilities|IsValid (G Amoeba)
    (:"Is Valid"
      (bind al (Transformation|GetActorLocation :self (G Amoeba)))
      (S EmitW (+ al (* (Math|Vector|Normalize (- (G Eye) al)) (G EmitOffset)))))
    (:"Is Not Valid"
      (S EmitW (Math|Transform|TransformLocation (Transformation|GetActorTransform) (G NoAmoebaAt))))))

;;@ AsBoot
;; En Play arranca sin chorros: las perillas a todos, ocultos. Recuerda los golpes que ya habia en el hang.
(fn AsBoot ()
  (S Used 0)
  (for c (G Streams)
    (CallFunction|AsLook :Comp c)
    (Rendering|SetVisibility c false false))
  (S NextDebug (+ (Utilities|Time|GetGameTimeinSeconds) 2.0))
  (Utilities|IsValid (G Harp)
    (:"Is Valid"
      (S Seen (Class|BPHarpSC|GetLastPluck (G Harp))))
    (:"Is Not Valid"
      (S Harp (Actor|GetActorOfClass "/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC.BP_Harp_SC_C")))))

;;@ AsTick
(fn AsTick (Dt)
  (CallFunction|AsDebug)
  (CallFunction|AsFollow :Dt Dt)
  (Utilities|IsValid (G Harp)
    (:"Is Valid"
      (CallFunction|AsSenseHarp))
    (:"Is Not Valid")))

;;@ AsSenseHarp
;; Una nota nueva = una voz del hang con LastPluck mas nuevo que el visto: un chorro nuevo del color de esa nota.
(fn AsSenseHarp ()
  (bind lp (Class|BPHarpSC|GetLastPluck (G Harp)))
  (Utilities|Array|Resize (G Seen) (Utilities|Array|Length lp))
  (for i (range (Utilities|Array|Length lp))
    (bind v (Utilities|Array|Get(acopy) lp i))
    (if (> v (Utilities|Array|Get(acopy) (G Seen) i))
      (Utilities|Array|SetArrayElem (G Seen) i v)
      (CallFunction|AsAdd :Col (Class|BPHarpSC|NoteColor :self (G Harp) :I i)))))

;;@ AsAdd
;; Enciende el proximo chorro libre (hasta MaxStreams; despues las notas suenan sin chorro nuevo).
(fn AsAdd (Col)
  (if (< (G Used) (Utilities|Array|Length (G Streams)))
    (bind c (Utilities|Array|Get(acopy) (G Streams) (G Used)))
    (bind xf (Transformation|GetActorTransform))
    (CallFunction|AsStart :Comp c :T0 (Utilities|Time|GetGameTimeinSeconds) :Col Col :Seed (Math|Random|RandomFloatinRange :Min 0.0 :Max 997.0))
    (CallFunction|AsPlace :Comp c :EyeL (Math|Transform|InverseTransformLocation xf (G Eye)) :EmitL (Math|Transform|InverseTransformLocation xf (G EmitW)))
    (S Used (+ (G Used) 1))))

;;@ AsFollow
;; La burbuja sigue a la cabeza con retardo (Follow, 1/s); un salto grande (primer cuadro, recentrado) va directo.
(fn AsFollow (Dt)
  (bind cm (Game|GetPlayerCameraManager 0))
  (Utilities|IsValid cm
    (:"Is Valid"
      (bind cam (Camera|GetCameraLocation cm))
      (S Eye (select (> (Math|Vector|Distance(Vector) (G Eye) cam) 300.0) cam (Math|Interpolation|VInterpTo (G Eye) cam Dt (G Follow))))
      (CallFunction|AsEmitUpdate)
      (bind xf (Transformation|GetActorTransform))
      (bind eyel (Math|Transform|InverseTransformLocation xf (G Eye)))
      (bind emitl (Math|Transform|InverseTransformLocation xf (G EmitW)))
      (for i (range (G Used))
        (CallFunction|AsPlace :Comp (Utilities|Array|Get(acopy) (G Streams) i) :EyeL eyel :EmitL emitl)))
    (:"Is Not Valid")))

;;@ AsDebug
;; Prueba sin visor: con bDebugNotes, una nota de color al azar cada DebugEvery s.
(fn AsDebug ()
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (if (and (G DebugNotes) (>= now (G NextDebug)))
    (S NextDebug (+ now (G DebugEvery)))
    (CallFunction|AsAdd :Col (Math|Color|HSVtoRGB (Math|Random|RandomFloatinRange :Min 0.0 :Max 360.0) 0.55 1.0 1.0))))
