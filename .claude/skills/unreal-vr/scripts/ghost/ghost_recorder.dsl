;; ghost_recorder.dsl - BP_GhostRecorder_SC: GRABADOR de los fantasmas (herramienta, tag TestOnly). 2026-09-30, Drawing.
;; Plan: docs/PLAN-FANTASMAS-2026-09-30.md §4. Variables y parametros: ghost_spec.json.
;; Controles por MIRADA (dwell): el input del proyecto es fragil y las manos quedan libres para el gesto.
;; Estados: 0 listo (◀ ▶ REC) · 1 cuenta 3-2-1 · 2 grabando DemoTimes[Idx] s · 3 vista previa (OK / REDO).
;; Botones: 0 PREV · 1 NEXT · 2 REC · 3 OK · 4 REDO.
;; Captura (30 Hz fijo, con while para no perder cuadros si hay tiron): GetMotionControllerState en UnrealWorldSpace
;; (grip y aim de cada mano: no depende de la clase del pawn), camara del PlayerCameraManager, gatillo y grip por
;; IA_Hand_IndexCurl_* / IA_Hand_Grasp_* (IMC_Hands esta en los contextos por defecto). Todo al espacio del ANCLA.

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (Utilities|Time|SetTimerbyFunctionName self "RcBoot" 0.6 false))

(event EventTick (DeltaSeconds)
  (if (Variables|Z-Rec|GetBooted)
    (CallFunction|RcTick self (Math|Float|Min(Float) DeltaSeconds 0.0333))))

;; ===== GRAFO: RcBoot
(fn RcBoot ()
  (bind _self self)
  (Input|EnableInput :PlayerController (Game|GetPlayerController 0))   ;;?
  (CallFunction|RcEnsure _self)
  (CallFunction|RcFrame _self)
  (CallFunction|RcLayout _self)
  (Variables|Z-Rec|SetIdx 0)
  (Variables|Z-Rec|SetState 0)
  (Variables|Z-Rec|SetBooted true)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcEnsure
(fn RcEnsure ()
  (bind _self self)
  (CallFunction|RcMakeText _self 3.2)
  (Variables|Z-Rec|SetTitleC (Variables|Z-Rec|GetNewText))
  (CallFunction|RcMakeText _self 2.2)
  (Variables|Z-Rec|SetInfoC (Variables|Z-Rec|GetNewText))
  (CallFunction|RcMakeText _self 9.0)
  (Variables|Z-Rec|SetBigC (Variables|Z-Rec|GetNewText))
  (CallFunction|RcMakeMesh _self (Variables|Rec|GetMarkerMesh))
  (Variables|Z-Rec|SetMarker (Variables|Z-Rec|GetNewComp))
  (for _i (range 5)
    (CallFunction|RcMakeButton _self)))

;; ===== GRAFO: RcMakeButton
(fn RcMakeButton ()
  (bind _self self)
  (CallFunction|RcMakeMesh _self (Variables|Rec|GetButtonMesh))
  (Utilities|Array|Add (Variables|Z-Rec|GetBtns) (Variables|Z-Rec|GetNewComp))
  (CallFunction|RcMakeText _self 1.8)
  (Utilities|Array|Add (Variables|Z-Rec|GetBtnTxt) (Variables|Z-Rec|GetNewText))
  (Utilities|Array|Add (Variables|Z-Rec|GetDwell) 0.0)
  (Utilities|Array|Add (Variables|Z-Rec|GetBtnOn) false))

;; ===== GRAFO: RcMakeMesh
(fn RcMakeMesh (M)
  (bind _c (Game|AddComponentbyClass :Class "/Script/Engine.StaticMeshComponent"))
  (bind _sm (Utilities|Casting|CastToStaticMeshComponent _c))
  (Components|StaticMesh|SetStaticMesh _sm M)
  (Rendering|Material|SetMaterial _sm 0 (Variables|Rec|GetUiMat))
  (Collision|SetCollisionEnabled _sm "NoCollision")
  (Rendering|SetCastShadow _sm false)
  (Rendering|Material|SetVectorParameterValueonMaterials _sm "Color" (Math|Conversions|ToVector(LinearColor) (Variables|Rec|GetUiColor)))
  (Rendering|Material|SetScalarParameterValueonMaterials _sm "Opacity" 0.5)
  (Variables|Z-Rec|SetNewComp _sm))

;; ===== GRAFO: RcMakeText
(fn RcMakeText (Size)
  (bind _c (Game|AddComponentbyClass :Class "/Script/Engine.TextRenderComponent"))
  (bind _tr (Utilities|Casting|CastToTextRenderComponent _c))
  (Rendering|Components|TextRender|SetTextMaterial _tr (Variables|Rec|GetTextMat))
  (Rendering|Components|TextRender|SetWorldSize _tr Size)   ;;?
  (Rendering|Components|TextRender|SetHorizontalAlignment _tr "EHTA_Center")   ;;?
  (Rendering|Components|TextRender|SetVerticalAlignment _tr "EVRTA_TextCenter")   ;;?
  (Collision|SetCollisionEnabled _tr "NoCollision")
  (Variables|Z-Rec|SetNewText _tr))

;; ===== GRAFO: RcFrame
;; Marco de la cabeza AHORA: posicion de la camara + yaw del pawn. Se usa para la UI, el marcador y el ANCLA.
(fn RcFrame ()
  (bind _cam (Game|GetPlayerCameraManager 0))
  (bind _yaw (.yaw (Transformation|GetActorRotation (Game|GetPlayerPawn 0))))
  (Variables|Z-Rec|SetAnchor (Math|Transform|MakeTransform :Location (Camera|GetCameraLocation _cam) :Rotation (Math|Rotator|MakeRotator :Yaw _yaw))))

;; ===== GRAFO: RcLayout
;; UI a UiDist al frente y UiUp por ENCIMA de la mirada de trabajo (asi no se dispara durante un gesto).
(fn RcLayout ()
  (bind _self self)
  (bind _a (Variables|Z-Rec|GetAnchor))
  (bind _d (Variables|Rec|GetUiDist))
  (bind _u (Variables|Rec|GetUiUp))
  (CallFunction|RcPlaceText _self (Variables|Z-Rec|GetTitleC) (Math|Vector|MakeVector _d 0.0 (+ _u 16.0)))
  (CallFunction|RcPlaceText _self (Variables|Z-Rec|GetInfoC) (Math|Vector|MakeVector _d 0.0 (+ _u 10.0)))
  (CallFunction|RcPlaceText _self (Variables|Z-Rec|GetBigC) (Math|Vector|MakeVector _d 0.0 (- _u 2.0)))
  (CallFunction|RcPlaceBtn _self 0 (Math|Vector|MakeVector _d -30.0 _u))
  (CallFunction|RcPlaceBtn _self 1 (Math|Vector|MakeVector _d 30.0 _u))
  (CallFunction|RcPlaceBtn _self 2 (Math|Vector|MakeVector _d 0.0 _u))
  (CallFunction|RcPlaceBtn _self 3 (Math|Vector|MakeVector _d -14.0 _u))
  (CallFunction|RcPlaceBtn _self 4 (Math|Vector|MakeVector _d 14.0 _u)))

;; ===== GRAFO: RcPlaceText
;; P en espacio del ancla (x al frente, y a la derecha, z arriba); el texto mira al usuario (yaw + 180).
(fn RcPlaceText (Tc P)
  (bind _a (Variables|Z-Rec|GetAnchor))
  (Transformation|SetWorldTransform Tc (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation _a P) :Rotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (.rotation _a)) 180.0)))))

;; ===== GRAFO: RcPlaceBtn
(fn RcPlaceBtn (I P)
  (bind _self self)
  (bind _a (Variables|Z-Rec|GetAnchor))
  (Transformation|SetWorldTransform (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I) (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation _a P) :Scale (Math|Vector|MakeVector 0.05 0.05 0.05)))
  (CallFunction|RcPlaceText _self (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnTxt) I) (- P (Math|Vector|MakeVector 0.0 0.0 5.5))))

;; ===== GRAFO: RcTick
(fn RcTick (Dt)
  (bind _self self)
  (bind _s (Variables|Z-Rec|GetState))
  (CallFunction|RcDebug _self)
  (CallFunction|RcGaze _self Dt)
  (if (== _s 1)
    (CallFunction|RcCountdown _self Dt)
    (elif (== _s 2)
      (CallFunction|RcRecording _self Dt))))

;; ===== GRAFO: RcGaze
(fn RcGaze (Dt)
  (for _i (range 5)
    (CallFunction|RcGazeOne self _i Dt)))

;; ===== GRAFO: RcGazeOne
;; Cono de GazeDeg alrededor del frente de la camara. Llena en DwellTime, se vacia al doble de rapido.
(fn RcGazeOne (I Dt)
  (bind _self self)
  (bind _cam (Game|GetPlayerCameraManager 0))
  (bind _cl (Camera|GetCameraLocation _cam))
  (bind _cf (Math|Vector|GetForwardVector (Camera|GetCameraRotation _cam)))   ;;?
  (bind _b (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I))
  (bind _dir (Math|Vector|Normalize (- (Transformation|GetWorldLocation _b) _cl)))   ;;?
  (bind _on (and (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnOn) I) (>= (Math|Vector|DotProduct _dir _cf) (Math|Trig|Cos(Degrees) (Variables|Rec|GetGazeDeg)))))   ;;? Dot
  (bind _w (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetDwell) I))
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetDwell) I (select _on (+ _w Dt) (Math|Float|Max(Float) 0.0 (- _w (* 2.0 Dt)))) true)
  (bind _k (Math|Float|Clamp(Float) (/ (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetDwell) I) (Math|Float|Max(Float) 0.1 (Variables|Rec|GetDwellTime)))))
  (Transformation|SetRelativeScale3D _b (Math|Vector|MakeVector (* 0.05 (+ 1.0 (* 0.8 _k))) (* 0.05 (+ 1.0 (* 0.8 _k))) (* 0.05 (+ 1.0 (* 0.8 _k)))))   ;;?
  (Rendering|Material|SetScalarParameterValueonMaterials _b "Opacity" (+ 0.35 (* 0.65 _k)))
  (if (>= _k 1.0)
    (CallFunction|RcDwellReset _self)
    (CallFunction|RcPress _self I)))

;; ===== GRAFO: RcDwellReset
(fn RcDwellReset ()
  (for _i (range 5)
    (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetDwell) _i 0.0 true)))

;; ===== GRAFO: RcPress
(fn RcPress (I)
  (bind _self self)
  (bind _n (Math|Integer|Max(Integer) 1 (Utilities|Array|Length (Variables|Rec|GetTakes))))
  (CallFunction|RcSound _self (Variables|Rec|GetTickSound))
  (switch int I
    (:0
      (Variables|Z-Rec|SetIdx (Math|Integer|%(Integer) (+ (Variables|Z-Rec|GetIdx) (- _n 1)) _n))
      (CallFunction|RcShow _self))
    (:1
      (Variables|Z-Rec|SetIdx (Math|Integer|%(Integer) (+ (Variables|Z-Rec|GetIdx) 1) _n))
      (CallFunction|RcShow _self))
    (:2 (CallFunction|RcCountStart _self))
    (:Default
      (if (== I 3)
        (CallFunction|RcAccept _self)
        (else (CallFunction|RcCountStart _self))))))

;; ===== GRAFO: RcCountStart
;; El ancla se toma AHORA (la cabeza no se mueve durante 3-2-1) y el marcador queda en su lugar para la toma.
(fn RcCountStart ()
  (bind _self self)
  (CallFunction|RcPlayerStop _self)
  (CallFunction|RcFrame _self)
  (Variables|Z-Rec|SetState 1)
  (Variables|Z-Rec|SetT 0.0)
  (Variables|Z-Rec|SetLastCount 4)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcCountdown
(fn RcCountdown (Dt)
  (bind _self self)
  (Variables|Z-Rec|SetT (+ (Variables|Z-Rec|GetT) Dt))
  (bind _c (- 3 (Math|Float|Floor (Variables|Z-Rec|GetT))))
  (if (>= (Variables|Z-Rec|GetT) 3.0)
    (CallFunction|RcRecStart _self)
    (elif (!= _c (Variables|Z-Rec|GetLastCount))
      (Variables|Z-Rec|SetLastCount _c)
      (CallFunction|RcSound _self (Variables|Rec|GetTickSound))
      (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) (Utilities|String|ToString(Integer) _c))))))   ;;?

;; ===== GRAFO: RcRecStart
(fn RcRecStart ()
  (bind _self self)
  (Utilities|Array|Clear (Variables|Z-Rec|GetTake))
  (Variables|Z-Rec|SetN 0)
  (Variables|Z-Rec|SetT 0.0)
  (Variables|Z-Rec|SetNextS 0.0)
  (Variables|Z-Rec|SetState 2)
  (CallFunction|RcSound _self (Variables|Rec|GetGoSound))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) "REC")))   ;;?

;; ===== GRAFO: RcRecording
(fn RcRecording (Dt)
  (bind _self self)
  (Variables|Z-Rec|SetT (+ (Variables|Z-Rec|GetT) Dt))
  (CallFunction|RcSampleLoop _self)
  (CallFunction|RcRecEndCheck _self))

;; ===== GRAFO: RcSampleLoop
;; 30 Hz fijo: toma todas las muestras que el tiempo ya paso (un tiron duplica la pose, no corre el reloj).
(fn RcSampleLoop ()
  (while (and (<= (Variables|Z-Rec|GetNextS) (Variables|Z-Rec|GetT)) (< (Variables|Z-Rec|GetN) 900))
    (CallFunction|RcCapture self)
    (Variables|Z-Rec|SetNextS (+ (Variables|Z-Rec|GetNextS) (/ 1.0 (Math|Float|Max(Float) 1.0 (Variables|Rec|GetRecHz)))))))

;; ===== GRAFO: RcRecEndCheck
(fn RcRecEndCheck ()
  (if (>= (Variables|Z-Rec|GetT) (Utilities|Array|Get(acopy) (Variables|Rec|GetDemoTimes) (Variables|Z-Rec|GetIdx)))
    (CallFunction|RcRecEnd self)))

;; ===== GRAFO: RcRecEnd
(fn RcRecEnd ()
  (bind _self self)
  (Variables|Z-Rec|SetState 3)
  (CallFunction|RcSound _self (Variables|Rec|GetEndSound))
  (CallFunction|RcPreview _self)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcCapture
;; 28 floats por cuadro, en ESPACIO DEL ANCLA (ver ghost_player.dsl). Sin visor, las poses salen en 0 (bValid false).
(fn RcCapture ()
  (bind _self self)
  (bind _gr (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Right" :ControllerPoseType "Grip"))
  (bind _gl (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Left" :ControllerPoseType "Grip"))
  (bind _ar (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Right" :ControllerPoseType "Aim"))
  (bind _al (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Left" :ControllerPoseType "Aim"))
  (bind (_v1 _d1 _a1 _s1 _h1 _t1 _p1 _l1 _q1) (Utilities|Struct|BreakXRMotionControllerState _gr))   ;; 9 salidas (get_node_type_pins 09-30): bValid DeviceName ApplicationInstanceID XRSpaceType Hand TrackingStatus PoseType Location Rotation(Quat)
  (bind (_v2 _d2 _a2 _s2 _h2 _t2 _p2 _l2 _q2) (Utilities|Struct|BreakXRMotionControllerState _gl))
  (bind (_v3 _d3 _a3 _s3 _h3 _t3 _p3 _l3 _q3) (Utilities|Struct|BreakXRMotionControllerState _ar))
  (bind (_v4 _d4 _a4 _s4 _h4 _t4 _p4 _l4 _q4) (Utilities|Struct|BreakXRMotionControllerState _al))
  (bind _cam (Game|GetPlayerCameraManager 0))
  (CallFunction|RcPushPose _self _l1 (Math|Conversions|ToRotator(Quat) _q1))   ;;? quat -> rotator
  (CallFunction|RcPushPose _self _l2 (Math|Conversions|ToRotator(Quat) _q2))
  (CallFunction|RcPushRot _self (Math|Conversions|ToRotator(Quat) _q3))
  (CallFunction|RcPushRot _self (Math|Conversions|ToRotator(Quat) _q4))
  (CallFunction|RcPushF _self (Input|EnhancedActionValues|IA_Hand_IndexCurl_Right))   ;;?
  (CallFunction|RcPushF _self (Input|EnhancedActionValues|IA_Hand_IndexCurl_Left))
  (CallFunction|RcPushF _self (Input|EnhancedActionValues|IA_Hand_Grasp_Right))
  (CallFunction|RcPushF _self (Input|EnhancedActionValues|IA_Hand_Grasp_Left))
  (CallFunction|RcPushPose _self (Camera|GetCameraLocation _cam) (Camera|GetCameraRotation _cam))
  (Variables|Z-Rec|SetN (+ (Variables|Z-Rec|GetN) 1)))

;; ===== GRAFO: RcPushPose
;; Posicion y rotacion en MUNDO -> espacio del ancla -> 6 floats (x y z pitch yaw roll).
(fn RcPushPose (P R)
  (bind _self self)
  (bind _a (Variables|Z-Rec|GetAnchor))
  (bind _lp (Math|Transform|InverseTransformLocation _a P))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.x _lp))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.y _lp))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.z _lp))
  (CallFunction|RcPushRot _self R))

;; ===== GRAFO: RcPushRot
(fn RcPushRot (R)
  (bind _lr (Math|Transform|InverseTransformRotation (Variables|Z-Rec|GetAnchor) R))   ;;?
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.pitch _lr))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.yaw _lr))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.roll _lr)))

;; ===== GRAFO: RcPushF
(fn RcPushF (V)
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (Math|Float|Clamp(Float) V)))

;; ===== GRAFO: RcPreview
;; La toma recien grabada, en el reproductor de la escena, con el aspecto final. Banderas del DA del gesto.
(fn RcPreview ()
  (bind _p (Variables|Rec|GetPlayer))
  (bind _da (Utilities|Array|Get(acopy) (Variables|Rec|GetTakes) (Variables|Z-Rec|GetIdx)))
  (Utilities|IsValid _p
    (:"Is Valid"
      (Class|BPGhostPlayerSC|PreviewData :self _p :D (Variables|Z-Rec|GetTake) :N (Variables|Z-Rec|GetN) :UR (Class|BPGhostTakeSC|GetUseRight _da) :UL (Class|BPGhostTakeSC|GetUseLeft _da) :BR (Class|BPGhostTakeSC|GetBeamRight _da) :BL (Class|BPGhostTakeSC|GetBeamLeft _da) :Txt (Class|BPGhostTakeSC|GetText _da) :Col (Variables|Rec|GetPreviewColor)))   ;;? funcion de otro BP
    (:"Is Not Valid")))

;; ===== GRAFO: RcPlayerStop
(fn RcPlayerStop ()
  (bind _p (Variables|Rec|GetPlayer))
  (Utilities|IsValid _p
    (:"Is Valid" (Class|BPGhostPlayerSC|Stop :self _p))   ;;?
    (:"Is Not Valid")))

;; ===== GRAFO: RcAccept
;; Escribe la toma DIRECTO en el DA (en PIE es el mismo objeto que en el editor: sobrevive al Stop).
;; Despues ghost_dump.py lo marca y lo guarda con ruta explicita.
(fn RcAccept ()
  (bind _self self)
  (bind _da (Utilities|Array|Get(acopy) (Variables|Rec|GetTakes) (Variables|Z-Rec|GetIdx)))
  (Class|BPGhostTakeSC|SetData :self _da :Data (Variables|Z-Rec|GetTake))
  (Class|BPGhostTakeSC|SetFrames :self _da :Frames (Variables|Z-Rec|GetN))
  (Class|BPGhostTakeSC|SetHz :self _da :Hz (Variables|Rec|GetRecHz))
  (Class|BPGhostTakeSC|SetStride :self _da :Stride 28)
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetAccepted) (Variables|Z-Rec|GetIdx) true true)
  (CallFunction|RcSound _self (Variables|Rec|GetOkSound))
  (CallFunction|RcPlayerStop _self)
  (Variables|Z-Rec|SetIdx (Math|Integer|%(Integer) (+ (Variables|Z-Rec|GetIdx) 1) (Math|Integer|Max(Integer) 1 (Utilities|Array|Length (Variables|Rec|GetTakes)))))
  (Variables|Z-Rec|SetState 0)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcShow
;; Textos, botones visibles por estado y el marcador de referencia del gesto.
(fn RcShow ()
  (bind _self self)
  (bind _s (Variables|Z-Rec|GetState))
  (bind _i (Variables|Z-Rec|GetIdx))
  (bind _da (Utilities|Array|Get(acopy) (Variables|Rec|GetTakes) _i))
  (bind _ok (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetAccepted) _i))
  (bind _t (Utilities|String|Append (Utilities|String|ToString(Name) (Class|BPGhostTakeSC|GetId _da)) (select _ok "  [OK]" "")))   ;;? Name -> String
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetTitleC) (Utilities|Text|ToText(String) _t))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetInfoC) (Utilities|Text|ToText(String) (Utilities|String|Append (Class|BPGhostTakeSC|GetText _da) (Utilities|String|Append "   ·   " (Utilities|String|Append (Utilities|String|ToString(Integer) (Math|Float|Round (Utilities|Array|Get(acopy) (Variables|Rec|GetDemoTimes) _i))) " s")))))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) (select (== _s 3) "OK?" "")))
  (CallFunction|RcBtn _self 0 (== _s 0) "<")
  (CallFunction|RcBtn _self 1 (== _s 0) ">")
  (CallFunction|RcBtn _self 2 (== _s 0) "REC")
  (CallFunction|RcBtn _self 3 (== _s 3) "OK")
  (CallFunction|RcBtn _self 4 (== _s 3) "REDO")
  (CallFunction|RcMarker _self))

;; ===== GRAFO: RcBtn
(fn RcBtn (I On Label)
  (bind _b (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I))
  (bind _tx (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnTxt) I))
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetBtnOn) I On true)
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetDwell) I 0.0 true)
  (Rendering|SetVisibility _b On)
  (Rendering|SetVisibility _tx On)
  (Rendering|Components|TextRender|SetText _tx (Utilities|Text|ToText(String) Label)))

;; ===== GRAFO: RcMarker
;; Esfera translucida donde en la obra esta el objeto del gesto (sensor, timbre, mesa...). Tamano 0 = sin marcador.
(fn RcMarker ()
  (bind _i (Variables|Z-Rec|GetIdx))
  (bind _sz (Utilities|Array|Get(acopy) (Variables|Rec|GetMarkerSize) _i))
  (bind _m (Variables|Z-Rec|GetMarker))
  (Transformation|SetWorldTransform _m (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation (Variables|Z-Rec|GetAnchor) (Utilities|Array|Get(acopy) (Variables|Rec|GetMarkerPos) _i)) :Scale (Math|Vector|MakeVector (/ _sz 50.0) (/ _sz 50.0) (/ _sz 50.0))))
  (Rendering|SetVisibility _m (and (Variables|Rec|GetShowMarkers) (> _sz 0.0))))

;; ===== GRAFO: RcSound
(fn RcSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid" (Audio|PlaySound2D Snd (Variables|Rec|GetSfxVol)))
    (:"Is Not Valid")))

;; ===== GRAFO: RcDebug
;; Gancho de PRUEBA sin visor: DebugPress (instance-editable, -1) "aprieta" un boton desde el MCP (set_properties en PIE).
;; 🔴 Primero RcPress (el parametro I se copia al llamar) y DESPUES el reset: un `bind` de un getter puro se reevalua
;; en cada uso, y resetear antes le pasaba -1 a RcPress (siempre caia en REC). Medido en PIE 2026-09-30.
(fn RcDebug ()
  (if (>= (Variables|Rec|GetDebugPress) 0)
    (CallFunction|RcPress self (Variables|Rec|GetDebugPress))
    (Variables|Rec|SetDebugPress -1)))
