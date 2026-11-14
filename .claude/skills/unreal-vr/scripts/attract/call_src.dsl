;; BP_AttractCall_SC (Test_AttractingHang, 2026-11-04) - LLAMADA Y RESPUESTA. Fuente de los grafos; (G X)/(S X v) los
;; expande gen_call_dsl.py con la categoria de cada variable y escribe call_dsl.json. Un bloque ;;@ = un grafo.
;; Mecanica (Beltran 11-04, tras la investigacion: Ragnarock + SPHERES): la ameba esta lejos, en el horizonte del salar.
;; Cada golpe del hang lanza una onda sobre el espejo (un anillo del color de la nota) que viaja hasta ella. Al llegar,
;; la ameba brilla y se acerca un paso, y devuelve otra onda; cuando esa onda te alcanza, suena su respuesta (la voz:
;; otra instancia del hang, oculta y sin Tick, una octava arriba) y vibra el mando. Mas cerca, la respuesta llega antes:
;; de un eco lejano a un duo. La etapa termina cuando llega (bStageDone). Cortafuegos: Drift la acerca sola, lento.
;; El hang no se toca: se lee su LastPluck/Energy y su NoteColor. La ameba no se toca por dentro: se le escriben
;; Size y EdgeIntensity (su Tick los aplica) y se la mueve con SetActorLocation.

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|AcBoot))
(event EventTick (DeltaSeconds)
  (CallFunction|AcTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

;;@ UserConstructionScript
(fn ConstructionScript ()
  (CallFunction|AcBuild))

;;@ AcBuild
;; La reserva de anillos (RingPool), ocultos. Cada uno es SM_AttractRing_SC con M_AttractRing_SC (CPD: RA = radio,
;; ancho, alfa, suavidad; RC = color, brillo).
(fn AcBuild ()
  (Utilities|Array|Clear (G Rings))
  (for i (range (G RingPool))
    (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
    (Components|StaticMesh|SetStaticMesh c (G RingMesh))
    (Rendering|Material|SetMaterial c 0 (G RingMat))
    (Collision|SetCollisionEnabled c "NoCollision")
    (Rendering|SetCastShadow c false)
    (Transformation|SetMobility c "Movable")
    (Rendering|SetVisibility c false false)
    (Utilities|Array|Add (G Rings) c))
  (bind s (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Components|StaticMesh|SetStaticMesh s (G ShellMesh))
  (Rendering|Material|SetMaterial s 0 (G ShellMat))
  (Collision|SetCollisionEnabled s "NoCollision")
  (Rendering|SetCastShadow s false)
  (Transformation|SetMobility s "Movable")
  (Rendering|SetVisibility s false false)
  (S Shell s)
  (if (G PreviewEmbrace)
    (Transformation|SetWorldLocation s (Math|Transform|TransformLocation (Transformation|GetActorTransform) (G PreviewEye)))
    (Transformation|SetWorldScale3D s (Math|Vector|MakeVector :X (/ (G ShellRadius) 50.0) :Y (/ (G ShellRadius) 50.0) :Z (/ (G ShellRadius) 50.0)))
    (bind (r g b a) (Utilities|Struct|BreakLinearColor (G ShellColor)))
    (Rendering|Material|SetCustomPrimitiveDataVector4 s 4 (Math|Vector4|MakeVector4 r g b (G ShellGlow)))
    (Rendering|Material|SetCustomPrimitiveDataVector4 s 0 (Math|Vector4|MakeVector4 (G ShellAlpha) 0.0 (G ShellWobble) (G ShellVeins)))
    (Rendering|SetVisibility s true false)))

;;@ AcBoot
(fn AcBoot ()
  (bind n (Utilities|Array|Length (G Rings)))
  (Utilities|Array|Clear (G RAge))
  (Utilities|Array|Resize (G RAge) n)
  (Utilities|Array|Clear (G RRad))
  (Utilities|Array|Resize (G RRad) n)
  (Utilities|Array|Clear (G RHit))
  (Utilities|Array|Resize (G RHit) n)
  (Utilities|Array|Clear (G RKind))
  (Utilities|Array|Resize (G RKind) n)
  (Utilities|Array|Clear (G RVoice))
  (Utilities|Array|Resize (G RVoice) n)
  (Utilities|Array|Clear (G RVel))
  (Utilities|Array|Resize (G RVel) n)
  (Utilities|Array|Clear (G RFired))
  (Utilities|Array|Resize (G RFired) n)
  (Utilities|Array|Clear (G RAlive))
  (Utilities|Array|Resize (G RAlive) n)
  (S Progress 0.0)
  (S Shown 0.0)
  (S Pulse 0.0)
  (S NextRing 0)
  (S Calls 0)
  (S StageDone false)
  (S Embrace 0.0)
  (S Embracing false)
  (Rendering|SetVisibility (G Shell) false false)
  (S NextDebug (+ (Utilities|Time|GetGameTimeinSeconds) 2.0))
  (CallFunction|AcBootVoice)
  (CallFunction|AcBootHarp)
  (Utilities|IsValid (G Amoeba)
    (:"Is Valid"
      (S BaseEdge (Class|BPProtoSoulSC|GetEdgeIntensity (G Amoeba))))
    (:"Is Not Valid")))

;;@ AcBootVoice
;; La voz de la ameba: otra instancia de BP_Harp_SC, oculta y SIN Tick (si tickeara, montaria otro par de mandos).
;; PrimaryActorTick no se puede escribir en la instancia por MCP, y su BeginPlay lo re-enciende: por eso la voz queda
;; con este actor de prerrequisito (tickea despues) y AcTick la apaga en cada cuadro, antes de que llegue a tickear.
(fn AcBootVoice ()
  (Utilities|IsValid (G Voice)
    (:"Is Valid"
      (Actor|Tick|AddTickPrerequisiteActor (G Voice) self)
      (Actor|Tick|SetActorTickEnabled (G Voice) false)
      (Rendering|SetActorHiddenInGame (G Voice) true))
    (:"Is Not Valid")))

;;@ AcBootHarp
(fn AcBootHarp ()
  (Utilities|IsValid (G Harp)
    (:"Is Valid"
      (S Seen (Class|BPHarpSC|GetLastPluck (G Harp))))
    (:"Is Not Valid")))

;;@ AcTick
(fn AcTick (Dt)
  (CallFunction|AcBootVoice)
  (CallFunction|AcDebug)
  (CallFunction|AcAmoeba :Dt Dt)
  (bind cm (Game|GetPlayerCameraManager 0))
  (Utilities|IsValid cm
    (:"Is Valid"
      (bind eye (Camera|GetCameraLocation cm))
      (for i (range (Utilities|Array|Length (G Rings)))
        (if (Utilities|Array|Get(acopy) (G RAlive) i)
          (CallFunction|AcRingStep :I i :Dt Dt :Eye eye)))
      (CallFunction|AcEmbrace :Dt Dt :Eye eye)
      (CallFunction|AcSense))
    (:"Is Not Valid")))

;;@ AcSense
;; Una nota = una voz del hang con LastPluck mas nuevo que el visto. Su fuerza = Energy de esa voz.
(fn AcSense ()
  (Utilities|IsValid (G Harp)
    (:"Is Valid"
      (bind lp (Class|BPHarpSC|GetLastPluck (G Harp)))
      (Utilities|Array|Resize (G Seen) (Utilities|Array|Length lp))
      (for i (range (Utilities|Array|Length lp))
        (bind v (Utilities|Array|Get(acopy) lp i))
        (if (> v (Utilities|Array|Get(acopy) (G Seen) i))
          (Utilities|Array|SetArrayElem (G Seen) i v)
          (CallFunction|AcCall :V i :Vel (Utilities|Array|Get(acopy) (Class|BPHarpSC|GetEnergy (G Harp)) i)))))
    (:"Is Not Valid")))

;;@ AcCall
;; La llamada: una onda del color de la nota desde el pie del hang, sobre el espejo (RingZ sobre el piso del actor).
(fn AcCall (V Vel)
  (bind hl (Transformation|GetActorLocation :self (G Harp)))
  (CallFunction|AcRing :Kind (- 1 1) :V V :Vel Vel :Origin (Math|Vector|MakeVector :X (.x hl) :Y (.y hl) :Z (+ (.z (Transformation|GetActorLocation)) (G RingZ))) :Col (Class|BPHarpSC|NoteColor :self (G Harp) :I V)))

;;@ AcRing
;; Enciende el proximo anillo de la reserva (circular). Kind 0 = llamada (hacia la ameba), 1 = respuesta (hacia ti).
(fn AcRing (Kind V Vel Origin Col)
  (bind i (G NextRing))
  (bind c (Utilities|Array|Get(acopy) (G Rings) i))
  (Utilities|Array|SetArrayElem (G RAge) i 0.0)
  (Utilities|Array|SetArrayElem (G RRad) i 0.0)
  (Utilities|Array|SetArrayElem (G RHit) i 0.0)
  (Utilities|Array|SetArrayElem (G RKind) i Kind)
  (Utilities|Array|SetArrayElem (G RVoice) i V)
  (Utilities|Array|SetArrayElem (G RVel) i Vel)
  (Utilities|Array|SetArrayElem (G RFired) i false)
  (Utilities|Array|SetArrayElem (G RAlive) i true)
  (Transformation|SetWorldLocation c Origin)
  (bind (r g b a) (Utilities|Struct|BreakLinearColor Col))
  (Rendering|Material|SetCustomPrimitiveDataVector4 c 4 (Math|Vector4|MakeVector4 r g b (G RingGlow)))
  (Rendering|Material|SetCustomPrimitiveDataVector4 c 0 (Math|Vector4|MakeVector4 0.0 (G RingWidth) 0.0 (G RingSoft)))
  (Rendering|SetVisibility c true false)
  (S NextRing (select (>= (+ i 1) (Utilities|Array|Length (G Rings))) 0 (+ i 1))))

;;@ AcRingStep
;; Crece a WaveSpeed. Se apaga con la distancia (RingFade) y, despues de llegar, en RingAfter s. La llegada se mide en
;; el plano contra donde ESTA ahora el destino (la ameba se mueve).
(fn AcRingStep (I Dt Eye)
  (Utilities|Array|SetArrayElem (G RAge) I (+ (Utilities|Array|Get(acopy) (G RAge) I) Dt))
  (bind rad (* (Utilities|Array|Get(acopy) (G RAge) I) (G WaveSpeed)))
  (Utilities|Array|SetArrayElem (G RRad) I rad)
  (bind c (Utilities|Array|Get(acopy) (G Rings) I))
  (bind kind (Utilities|Array|Get(acopy) (G RKind) I))
  (bind tgt (select (== kind 0) (Transformation|GetActorLocation :self (G Amoeba)) Eye))
  (bind dist (Math|Vector|Distance2D(Vector) (Transformation|GetWorldLocation c) tgt))
  (bind fired (Utilities|Array|Get(acopy) (G RFired) I))
  (bind after (select fired (Math|Float|Clamp(Float) (- 1.0 (/ (- rad (Utilities|Array|Get(acopy) (G RHit) I)) (* (G WaveSpeed) (G RingAfter))))) 1.0))
  (bind alpha (* (* (select (== kind 0) (G RingAlpha) (G ReturnAlpha)) (Math|Float|Exp (/ (neg rad) (G RingFade)))) after))
  (Rendering|Material|SetCustomPrimitiveDataVector4 c 0 (Math|Vector4|MakeVector4 rad (+ (G RingWidth) (* rad (G RingWidthGrow))) alpha (G RingSoft)))
  (if (and (not fired) (>= rad dist))
    (Utilities|Array|SetArrayElem (G RFired) I true)
    (Utilities|Array|SetArrayElem (G RHit) I rad)
    (CallFunction|AcArrive :I I)
    (elif (and fired (<= after 0.0))
      (Utilities|Array|SetArrayElem (G RAlive) I false)
      (Rendering|SetVisibility c false false))))

;;@ AcArrive
;; Llamada que llega a la ameba = AcAnswer. Respuesta que llega a ti = suena la voz (y vibra el mando, lo hace Pluck).
(fn AcArrive (I)
  (bind v (Utilities|Array|Get(acopy) (G RVoice) I))
  (bind vel (Utilities|Array|Get(acopy) (G RVel) I))
  (if (== (Utilities|Array|Get(acopy) (G RKind) I) 0)
    (CallFunction|AcAnswer :V v :Vel vel)
    (else
      (Utilities|IsValid (G Voice)
        (:"Is Valid"
          (Class|BPHarpSC|Pluck :self (G Voice) :I v :Speed (* (+ (G VoiceSpeedFar) (* (- (G VoiceSpeedNear) (G VoiceSpeedFar)) (G Shown))) (+ 0.6 (* 0.4 vel))) :Right (G VoiceRight)))
        (:"Is Not Valid")))))

;;@ AcAnswer
;; La ameba contesta: brilla (Pulse), se acerca un paso (StepPerCall, mas con un golpe fuerte) y devuelve la onda.
(fn AcAnswer (V Vel)
  (S Pulse 1.0)
  (S Calls (+ (G Calls) 1))
  (S Progress (Math|Float|Min(Float) 1.0 (+ (G Progress) (* (G StepPerCall) (+ (- 1.0 (G StepVelGain)) (* (G StepVelGain) Vel))))))
  (bind al (Transformation|GetActorLocation :self (G Amoeba)))
  (CallFunction|AcRing :Kind (- 2 1) :V V :Vel Vel :Origin (Math|Vector|MakeVector :X (.x al) :Y (.y al) :Z (+ (.z (Transformation|GetActorLocation)) (G RingZ))) :Col (Class|BPHarpSC|NoteColor :self (G Harp) :I V)))

;;@ AcAmoeba
;; Shown sigue a Progress con frenada fisica (v = max(BrakeFloor, Brake*sqrt(resto))). Drift = cortafuegos. La ameba va
;; de FarPoint a NearPoint (locales del actor); en el abrazo (Embrace 0..1, smoothstep) sigue hasta EmbraceEye (el ojo) y
;; crece de AmoebaSize a EmbraceSize. Su borde brilla con Pulse.
(fn AcAmoeba (Dt)
  (S Progress (Math|Float|Min(Float) 1.0 (+ (G Progress) (* (G Drift) Dt))))
  (bind rem (Math|Float|Max(Float) (- (G Progress) (G Shown)) 0.0))
  (S Shown (+ (G Shown) (Math|Float|Min(Float) rem (* Dt (Math|Float|Max(Float) (G BrakeFloor) (* (G Brake) (Math|Float|Sqrt rem)))))))
  (S Pulse (Math|Float|Max(Float) 0.0 (- (G Pulse) (/ Dt (G GlowDecay)))))
  (Utilities|IsValid (G Amoeba)
    (:"Is Valid"
      (bind xf (Transformation|GetActorTransform))
      (bind e (* (* (G Embrace) (G Embrace)) (- 3.0 (* 2.0 (G Embrace)))))
      (Transformation|SetActorLocation :self (G Amoeba) :NewLocation (Math|Vector|Lerp(Vector) (Math|Vector|Lerp(Vector) (Math|Transform|TransformLocation xf (G FarPoint)) (Math|Transform|TransformLocation xf (G NearPoint)) (G Shown)) (G EmbraceEye) e))
      (Class|BPProtoSoulSC|SetSize :self (G Amoeba) :Size (+ (G AmoebaSize) (* (- (G EmbraceSize) (G AmoebaSize)) e)))
      (Class|BPProtoSoulSC|SetEdgeIntensity :self (G Amoeba) :EdgeIntensity (+ (G BaseEdge) (* (- (G GlowPeak) (G BaseEdge)) (* (G Pulse) (G Pulse))))))
    (:"Is Not Valid")))

;;@ AcEmbrace
;; El abrazo (Beltran 11-05: "arma el final que me envuelve"). Al llegar (Shown 1), la ameba sigue hasta el ojo y crece
;; (AcAmoeba). Como M_ProtoSoul es de una cara y desde adentro no se ve, un cascaron de dos caras (M_AttractShell_SC,
;; radio ShellRadius, centrado en el ojo) se enciende cuando el ojo queda DENTRO de la ameba: la membrana vista desde
;; adentro, que ondula y late con cada respuesta (Pulse). La etapa termina cuando el abrazo se completa.
(fn AcEmbrace (Dt Eye)
  (if (G Embracing)
    (CallFunction|AcEmbraceStep :Dt Dt)
    (elif (>= (G Shown) 0.999)
      (S Embracing true)
      (S EmbraceEye Eye)
      (Transformation|SetWorldLocation (G Shell) Eye)
      (Transformation|SetWorldScale3D (G Shell) (Math|Vector|MakeVector :X (/ (G ShellRadius) 50.0) :Y (/ (G ShellRadius) 50.0) :Z (/ (G ShellRadius) 50.0)))
      (bind (r g b a) (Utilities|Struct|BreakLinearColor (G ShellColor)))
      (Rendering|Material|SetCustomPrimitiveDataVector4 (G Shell) 4 (Math|Vector4|MakeVector4 r g b (G ShellGlow)))
      (Rendering|Material|SetCustomPrimitiveDataVector4 (G Shell) 0 (Math|Vector4|MakeVector4 0.0 0.0 (G ShellWobble) (G ShellVeins)))
      (Rendering|SetVisibility (G Shell) true false)
      (Development|PrintString "ATTRACT embrace starts" false))))

;;@ AcEmbraceStep
;; Avanza el abrazo en EmbraceTime s. El cascaron aparece segun cuanto esta el ojo dentro de la ameba (radio = 50 * Size
;; cm, SM_AlmaSphere): de -20 a +40 cm de "adentro" sube de 0 a ShellAlpha.
(fn AcEmbraceStep (Dt)
  (S Embrace (Math|Float|Min(Float) 1.0 (+ (G Embrace) (/ Dt (G EmbraceTime)))))
  (bind inside (- (* 50.0 (Class|BPProtoSoulSC|GetSize (G Amoeba))) (Math|Vector|Distance(Vector) (Transformation|GetActorLocation :self (G Amoeba)) (G EmbraceEye))))
  (Rendering|Material|SetCustomPrimitiveDataVector4 (G Shell) 0 (Math|Vector4|MakeVector4 (* (G ShellAlpha) (Math|Float|Clamp(Float) (/ (+ inside 20.0) 60.0))) (G Pulse) (G ShellWobble) (G ShellVeins)))
  (if (and (>= (G Embrace) 1.0) (not (G StageDone)))
    (S StageDone true)
    (Development|PrintString "ATTRACT stage done (embraced)" false)))

;;@ AcDebug
;; Prueba sin visor: con bDebugNotes, una nota al azar (voz 0..8, fuerza 0,3..1) cada DebugEvery s.
(fn AcDebug ()
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (if (and (G DebugNotes) (>= now (G NextDebug)))
    (S NextDebug (+ now (G DebugEvery)))
    (CallFunction|AcCall :V (Math|Random|RandomIntegerinRange 0 8) :Vel (Math|Random|RandomFloatinRange :Min 0.3 :Max 1.0))))
