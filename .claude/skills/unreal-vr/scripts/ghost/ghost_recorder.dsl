;; ghost_recorder.dsl - BP_GhostRecorder_SC v2: GRABADOR de los fantasmas (herramienta del estudio L_GhostRec_SC).
;; 2026-10-01. Plan: docs/PLAN-FANTASMAS-V2-2026-10-01.md §5. Variables y parametros: ghost_spec.json.
;; Una ESTACION por instruccion: el fantasma de esa instruccion (Ghosts[i], con su Take) + las piezas de referencia con
;; el tag = Id de la toma (copias del arte real). Solo se ve la estacion elegida.
;; Controles por MIRADA (dwell): las manos quedan libres para el gesto. Botones: 0 PREV · 1 NEXT · 2 REC · 3 OK · 4 REDO.
;; Estados: 0 listo · 1 cuenta (CountTime, numeros EN LA ESTACION) · 2 grabando DemoTime s · 3 vista previa (OK / REDO).
;; Mientras cuenta y graba, el fantasma de la estacion muestra EN TUS MANOS lo que va a sostener (LiveSet).
;; Ancla de la toma: la cabeza (tomas de cabeza: Breath, Heart) o el fantasma de la estacion (las demas).
;; Captura 30 Hz fija; 34 floats por cuadro (ver ghost_player.dsl). Gatillo y grip por IA_Hand_IndexCurl/Grasp_*.
;; Reglas del parser: ver ghost_player.dsl. Nunca un literal como argumento de una funcion PROPIA.

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (Utilities|Time|SetTimerbyFunctionName self "RcBoot" 0.6 false))

(event EventTick (DeltaSeconds)
  (if (Variables|Z-Rec|GetBooted)
    (CallFunction|RcTick self (Math|Float|Min(Float) DeltaSeconds 0.0333))))

;; ===== GRAFO: RcBoot
(fn RcBoot ()
  (bind _self self)
  (Input|EnableInput :PlayerController (Game|GetPlayerController 0))
  (CallFunction|RcEnsure _self)
  (CallFunction|RcFrame _self)
  (Variables|Z-Rec|SetUiFrame (Variables|Z-Rec|GetHeadXf))
  (CallFunction|RcLayout _self)
  (Variables|Z-Rec|SetIdx 0)
  (Variables|Z-Rec|SetState 0)
  (Variables|Z-Rec|SetBooted true)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcEnsure
;; Textos y botones (en runtime: el grabador no tiene vista previa en el editor). Tamanos y rotulos con nodos NATIVOS
;; (un literal pasado a una funcion propia se pierde).
(fn RcEnsure ()
  (bind _self self)
  (CallFunction|RcMakeText _self)
  (Variables|Z-Rec|SetTitleC (Variables|Z-Rec|GetNewText))
  (Rendering|Components|TextRender|SetWorldSize (Variables|Z-Rec|GetTitleC) 3.2)
  (CallFunction|RcMakeText _self)
  (Variables|Z-Rec|SetInfoC (Variables|Z-Rec|GetNewText))
  (Rendering|Components|TextRender|SetWorldSize (Variables|Z-Rec|GetInfoC) 2.2)
  (CallFunction|RcMakeText _self)
  (Variables|Z-Rec|SetBigC (Variables|Z-Rec|GetNewText))
  (Rendering|Components|TextRender|SetWorldSize (Variables|Z-Rec|GetBigC) (Variables|Rec|GetBigSize))
  (CallFunction|RcMakeButtons _self)
  (CallFunction|RcLabels _self)
  (CallFunction|RcAcceptInit _self))

;; ===== GRAFO: RcMakeButtons
(fn RcMakeButtons ()
  (for _i (range 5)
    (CallFunction|RcMakeButton self)))

;; ===== GRAFO: RcMakeButton
(fn RcMakeButton ()
  (bind _self self)
  (CallFunction|RcMakeMesh _self (Variables|Rec|GetButtonMesh))
  (Utilities|Array|Add (Variables|Z-Rec|GetBtns) (Variables|Z-Rec|GetNewComp))
  (CallFunction|RcMakeText _self)
  (Rendering|Components|TextRender|SetWorldSize (Variables|Z-Rec|GetNewText) 1.8)
  (Utilities|Array|Add (Variables|Z-Rec|GetBtnTxt) (Variables|Z-Rec|GetNewText))
  (Utilities|Array|Add (Variables|Z-Rec|GetDwell) 0.0)
  (Utilities|Array|Add (Variables|Z-Rec|GetBtnOn) false))

;; ===== GRAFO: RcLabels
(fn RcLabels ()
  (bind _bt (Variables|Z-Rec|GetBtnTxt))
  (Rendering|Components|TextRender|SetText (Utilities|Array|Get(acopy) _bt 0) (Utilities|Text|ToText(String) "<"))
  (Rendering|Components|TextRender|SetText (Utilities|Array|Get(acopy) _bt 1) (Utilities|Text|ToText(String) ">"))
  (Rendering|Components|TextRender|SetText (Utilities|Array|Get(acopy) _bt 2) (Utilities|Text|ToText(String) "REC"))
  (Rendering|Components|TextRender|SetText (Utilities|Array|Get(acopy) _bt 3) (Utilities|Text|ToText(String) "OK"))
  (Rendering|Components|TextRender|SetText (Utilities|Array|Get(acopy) _bt 4) (Utilities|Text|ToText(String) "REDO")))

;; ===== GRAFO: RcAcceptInit
(fn RcAcceptInit ()
  (Utilities|Array|Clear (Variables|Z-Rec|GetAccepted))
  (for _g (Variables|Rec|GetGhosts)
    (Utilities|Array|Add (Variables|Z-Rec|GetAccepted) false)))

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
(fn RcMakeText ()
  (bind _c (Game|AddComponentbyClass :Class "/Script/Engine.TextRenderComponent"))
  (bind _tr (Utilities|Casting|CastToTextRenderComponent _c))
  (Rendering|Components|TextRender|SetTextMaterial _tr (Variables|Rec|GetTextMat))
  (Rendering|Components|TextRender|SetHorizontalAlignment _tr "EHTA_Center")
  (Rendering|Components|TextRender|SetVerticalAlignment _tr "EVRTA_TextCenter")
  (Collision|SetCollisionEnabled _tr "NoCollision")
  (Variables|Z-Rec|SetNewText _tr))

;; ===== GRAFO: RcFrame
;; Marco de la cabeza AHORA: posicion de la camara + yaw del pawn.
(fn RcFrame ()
  (bind _cam (Game|GetPlayerCameraManager 0))
  (bind _yaw (.yaw (Transformation|GetActorRotation (Game|GetPlayerPawn 0))))
  (Variables|Z-Rec|SetHeadXf (Math|Transform|MakeTransform :Location (Camera|GetCameraLocation _cam) :Rotation (Math|Rotator|MakeRotator :Yaw _yaw))))

;; ===== GRAFO: RcLayout
;; UI a UiDist al frente y UiUp por ENCIMA de la mirada de trabajo (asi no se dispara durante un gesto).
(fn RcLayout ()
  (bind _self self)
  (bind _d (Variables|Rec|GetUiDist))
  (bind _u (Variables|Rec|GetUiUp))
  (CallFunction|RcPlaceText _self (Variables|Z-Rec|GetTitleC) (Math|Vector|MakeVector _d 0.0 (+ _u 16.0)))
  (CallFunction|RcPlaceText _self (Variables|Z-Rec|GetInfoC) (Math|Vector|MakeVector _d 0.0 (+ _u 10.0)))
  (CallFunction|RcPlaceBig _self)
  (CallFunction|RcPlaceBtns _self))

;; ===== GRAFO: RcPlaceBtns
(fn RcPlaceBtns ()
  (for _i (range 5)
    (CallFunction|RcPlaceBtn self _i)))

;; ===== GRAFO: RcPlaceBtn
;; < y > a los costados, REC al centro, OK y REDO entre medio (aparecen en estados distintos).
(fn RcPlaceBtn (I)
  (bind _self self)
  (bind _d (Variables|Rec|GetUiDist))
  (bind _u (Variables|Rec|GetUiUp))
  (bind _y (select (== I 0) -30.0 (select (== I 1) 30.0 (select (== I 3) -14.0 (select (== I 4) 14.0 0.0)))))
  (bind _p (Math|Vector|MakeVector _d _y _u))
  (Transformation|SetWorldTransform (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I) (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation (Variables|Z-Rec|GetUiFrame) _p) :Scale (Math|Vector|MakeVector 0.05 0.05 0.05)))
  (CallFunction|RcPlaceText _self (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnTxt) I) (- _p (Math|Vector|MakeVector 0.0 0.0 5.5))))

;; ===== GRAFO: RcPlaceText
;; P en espacio de la UI (x al frente, y a la derecha, z arriba); el texto mira al usuario (yaw + 180).
(fn RcPlaceText (Tc P)
  (bind _a (Variables|Z-Rec|GetUiFrame))
  (Transformation|SetWorldTransform Tc (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation _a P) :Rotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (.rotation _a)) 180.0)))))

;; ===== GRAFO: RcPlaceBig
;; El numero grande: mientras cuenta y graba va EN LA ESTACION (donde se hace el gesto), mirando a la camara; si no,
;; en la UI (ahi dice "OK?").
(fn RcPlaceBig ()
  (bind _s (Variables|Z-Rec|GetState))
  (if (or (== _s 1) (== _s 2))
    (CallFunction|RcBigAtStation self)
    (else (CallFunction|RcPlaceText self (Variables|Z-Rec|GetBigC) (Math|Vector|MakeVector (Variables|Rec|GetUiDist) 0.0 (- (Variables|Rec|GetUiUp) 2.0))))))

;; ===== GRAFO: RcBigAtStation
(fn RcBigAtStation ()
  (bind _an (Variables|Z-Rec|GetAnchor))
  (bind _p (Math|Transform|TransformLocation _an (select (Variables|Z-Rec|GetHeadTake) (Variables|Rec|GetCountOffHead) (Variables|Rec|GetCountOffLevel))))
  (bind _cl (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)))
  (Transformation|SetWorldTransform (Variables|Z-Rec|GetBigC) (Math|Transform|MakeTransform :Location _p :Rotation (Math|Rotator|MakeRotator :Yaw (.yaw (Math|Rotator|FindLookatRotation _p _cl))))))   ;;?

;; ===== GRAFO: RcTick
(fn RcTick (Dt)
  (bind _self self)
  (bind _s (Variables|Z-Rec|GetState))
  (CallFunction|RcRead _self)
  (CallFunction|RcDebug _self)
  (CallFunction|RcGaze _self Dt)
  (CallFunction|RcLive _self)
  (if (== _s 1)
    (CallFunction|RcCountdown _self Dt)
    (elif (== _s 2)
      (CallFunction|RcRecording _self Dt))))

;; ===== GRAFO: RcRead
;; Poses de los mandos en MUNDO (no depende de la clase del pawn) y gatillo/grip 0-1. Sin visor, bValid false y 0.
(fn RcRead ()
  (bind _gr (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Right" :ControllerPoseType "Grip"))
  (bind _gl (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Left" :ControllerPoseType "Grip"))
  (bind _ar (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Right" :ControllerPoseType "Aim"))
  (bind _al (Input|XRTracking|GetMotionControllerState :XRSpaceType "UnrealWorldSpace" :Hand "Left" :ControllerPoseType "Aim"))
  (bind (_v1 _d1 _a1 _s1 _h1 _t1 _p1 _l1 _q1) (Utilities|Struct|BreakXRMotionControllerState _gr))   ;; 9 salidas (gotcha 559)
  (bind (_v2 _d2 _a2 _s2 _h2 _t2 _p2 _l2 _q2) (Utilities|Struct|BreakXRMotionControllerState _gl))
  (bind (_v3 _d3 _a3 _s3 _h3 _t3 _p3 _l3 _q3) (Utilities|Struct|BreakXRMotionControllerState _ar))
  (bind (_v4 _d4 _a4 _s4 _h4 _t4 _p4 _l4 _q4) (Utilities|Struct|BreakXRMotionControllerState _al))
  (Variables|Z-Rec|SetGR (Math|Transform|MakeTransform :Location _l1 :Rotation (Math|Conversions|ToRotator(Quat) _q1)))
  (Variables|Z-Rec|SetGL (Math|Transform|MakeTransform :Location _l2 :Rotation (Math|Conversions|ToRotator(Quat) _q2)))
  (Variables|Z-Rec|SetAR (Math|Transform|MakeTransform :Location _l3 :Rotation (Math|Conversions|ToRotator(Quat) _q3)))
  (Variables|Z-Rec|SetAL (Math|Transform|MakeTransform :Location _l4 :Rotation (Math|Conversions|ToRotator(Quat) _q4)))
  (Variables|Z-Rec|SetTR (Input|EnhancedActionValues|IA_Hand_IndexCurl_Right))
  (Variables|Z-Rec|SetTL (Input|EnhancedActionValues|IA_Hand_IndexCurl_Left))
  (Variables|Z-Rec|SetPR (Input|EnhancedActionValues|IA_Hand_Grasp_Right))
  (Variables|Z-Rec|SetPL (Input|EnhancedActionValues|IA_Hand_Grasp_Left)))

;; ===== GRAFO: RcLive
;; Cuenta y grabacion: el fantasma de la estacion muestra en las manos lo que va a sostener (sensor, SAVE, paleta, haz).
(fn RcLive ()
  (bind _s (Variables|Z-Rec|GetState))
  (if (or (== _s 1) (== _s 2))
    (Class|BPGhostPlayerSC|LiveSet :self (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) (Variables|Z-Rec|GetIdx)) :Gr (Variables|Z-Rec|GetGR) :Gl (Variables|Z-Rec|GetGL) :Ar (Variables|Z-Rec|GetAR) :Al (Variables|Z-Rec|GetAL) :Tr (Variables|Z-Rec|GetTR) :Tl (Variables|Z-Rec|GetTL))))

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
  (bind _cf (Math|Vector|GetForwardVector (Camera|GetCameraRotation _cam)))
  (bind _b (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I))
  (bind _dir (Math|Vector|Normalize (- (Transformation|GetWorldLocation _b) _cl)))
  (bind _on (and (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnOn) I) (>= (Math|Vector|DotProduct _dir _cf) (Math|Trig|Cos(Degrees) (Variables|Rec|GetGazeDeg)))))
  (bind _w (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetDwell) I))
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetDwell) I (select _on (+ _w Dt) (Math|Float|Max(Float) 0.0 (- _w (* 2.0 Dt)))) true)
  (bind _k (Math|Float|Clamp(Float) (/ (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetDwell) I) (Math|Float|Max(Float) 0.1 (Variables|Rec|GetDwellTime)))))
  (Transformation|SetRelativeScale3D _b (Math|Vector|MakeVector (* 0.05 (+ 1.0 (* 0.8 _k))) (* 0.05 (+ 1.0 (* 0.8 _k))) (* 0.05 (+ 1.0 (* 0.8 _k)))))
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
  (bind _n (Math|Integer|Max(Integer) 1 (Utilities|Array|Length (Variables|Rec|GetGhosts))))
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
;; REC (o REDO): el ancla se toma AHORA, el fantasma pasa a EN VIVO y empieza la cuenta en la estacion.
(fn RcCountStart ()
  (bind _self self)
  (bind _g (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) (Variables|Z-Rec|GetIdx)))
  (CallFunction|RcAnchor _self)
  (Class|BPGhostPlayerSC|LiveStart :self _g)
  (Variables|Z-Rec|SetState 1)
  (Variables|Z-Rec|SetT 0.0)
  (Variables|Z-Rec|SetLastCount 99)
  (CallFunction|RcShow _self)
  (CallFunction|RcPlaceBig _self))

;; ===== GRAFO: RcAnchor
(fn RcAnchor ()
  (bind _self self)
  (bind _g (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) (Variables|Z-Rec|GetIdx)))
  (Variables|Z-Rec|SetHeadTake (Class|BPGhostTakeSC|GetHeadAnchor (Class|BPGhostPlayerSC|GetTake _g)))
  (CallFunction|RcFrame _self)
  (Variables|Z-Rec|SetAnchor (select (Variables|Z-Rec|GetHeadTake) (Variables|Z-Rec|GetHeadXf) (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation _g) :Rotation (Transformation|GetActorRotation _g)))))

;; ===== GRAFO: RcCountdown
;; Numero = CountTime redondeado - segundos enteros pasados (3, 2, 1). Un tic por numero; al llegar a CountTime, YA.
(fn RcCountdown (Dt)
  (bind _self self)
  (Variables|Z-Rec|SetT (+ (Variables|Z-Rec|GetT) Dt))
  (bind _c (- (Math|Float|Round (Variables|Rec|GetCountTime)) (Math|Float|Floor (Variables|Z-Rec|GetT))))
  (if (>= (Variables|Z-Rec|GetT) (Variables|Rec|GetCountTime))
    (CallFunction|RcRecStart _self)
    (elif (!= _c (Variables|Z-Rec|GetLastCount))
      (Variables|Z-Rec|SetLastCount _c)
      (CallFunction|RcSound _self (Variables|Rec|GetTickSound))
      (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) (Utilities|String|ToString(Integer) _c))))))

;; ===== GRAFO: RcRecStart
;; El "YA": bip distinto y la grabacion empieza en este cuadro.
(fn RcRecStart ()
  (bind _self self)
  (Utilities|Array|Clear (Variables|Z-Rec|GetTake))
  (Variables|Z-Rec|SetN 0)
  (Variables|Z-Rec|SetT 0.0)
  (Variables|Z-Rec|SetNextS 0.0)
  (Variables|Z-Rec|SetLastCount 99)
  (Variables|Z-Rec|SetState 2)
  (CallFunction|RcSound _self (Variables|Rec|GetGoSound))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) "REC")))

;; ===== GRAFO: RcRecording
(fn RcRecording (Dt)
  (bind _self self)
  (Variables|Z-Rec|SetT (+ (Variables|Z-Rec|GetT) Dt))
  (CallFunction|RcSampleLoop _self)
  (CallFunction|RcRecLeft _self)
  (CallFunction|RcRecEndCheck _self))

;; ===== GRAFO: RcRecLeft
;; Durante la grabacion el numero muestra los segundos que quedan.
(fn RcRecLeft ()
  (bind _left (- (Math|Float|Round (Variables|Z-Rec|GetDemoTime)) (Math|Float|Floor (Variables|Z-Rec|GetT))))
  (if (!= _left (Variables|Z-Rec|GetLastCount))
    (Variables|Z-Rec|SetLastCount _left)
    (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) (Utilities|String|Append "REC " (Utilities|String|ToString(Integer) _left))))))

;; ===== GRAFO: RcSampleLoop
;; 30 Hz fijo: toma todas las muestras que el tiempo ya paso (un tiron duplica la pose, no corre el reloj).
(fn RcSampleLoop ()
  (while (and (<= (Variables|Z-Rec|GetNextS) (Variables|Z-Rec|GetT)) (< (Variables|Z-Rec|GetN) 900))
    (CallFunction|RcCapture self)
    (Variables|Z-Rec|SetNextS (+ (Variables|Z-Rec|GetNextS) (/ 1.0 (Math|Float|Max(Float) 1.0 (Variables|Rec|GetRecHz)))))))

;; ===== GRAFO: RcRecEndCheck
(fn RcRecEndCheck ()
  (if (>= (Variables|Z-Rec|GetT) (Variables|Z-Rec|GetDemoTime))
    (CallFunction|RcRecEnd self)))

;; ===== GRAFO: RcRecEnd
(fn RcRecEnd ()
  (bind _self self)
  (bind _g (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) (Variables|Z-Rec|GetIdx)))
  (Variables|Z-Rec|SetState 3)
  (CallFunction|RcSound _self (Variables|Rec|GetEndSound))
  (Class|BPGhostPlayerSC|LiveStop :self _g)
  (Class|BPGhostPlayerSC|PreviewData :self _g :D (Variables|Z-Rec|GetTake) :N (Variables|Z-Rec|GetN))
  (CallFunction|RcShow _self)
  (CallFunction|RcPlaceBig _self))

;; ===== GRAFO: RcCapture
;; 34 floats por cuadro, en ESPACIO DEL ANCLA (orden en ghost_player.dsl).
(fn RcCapture ()
  (bind _self self)
  (bind _cam (Game|GetPlayerCameraManager 0))
  (CallFunction|RcPushPose _self (.location (Variables|Z-Rec|GetGR)) (.rotation (Variables|Z-Rec|GetGR)))
  (CallFunction|RcPushPose _self (.location (Variables|Z-Rec|GetGL)) (.rotation (Variables|Z-Rec|GetGL)))
  (CallFunction|RcPushRot _self (.rotation (Variables|Z-Rec|GetAR)))
  (CallFunction|RcPushRot _self (.rotation (Variables|Z-Rec|GetAL)))
  (CallFunction|RcPushF _self (Variables|Z-Rec|GetTR))
  (CallFunction|RcPushF _self (Variables|Z-Rec|GetTL))
  (CallFunction|RcPushF _self (Variables|Z-Rec|GetPR))
  (CallFunction|RcPushF _self (Variables|Z-Rec|GetPL))
  (CallFunction|RcPushPose _self (Camera|GetCameraLocation _cam) (Camera|GetCameraRotation _cam))
  (CallFunction|RcPushLoc _self (.location (Variables|Z-Rec|GetAR)))
  (CallFunction|RcPushLoc _self (.location (Variables|Z-Rec|GetAL)))
  (Variables|Z-Rec|SetN (+ (Variables|Z-Rec|GetN) 1)))

;; ===== GRAFO: RcPushPose
;; Posicion y rotacion en MUNDO -> espacio del ancla -> 6 floats (x y z pitch yaw roll).
(fn RcPushPose (P R)
  (bind _self self)
  (CallFunction|RcPushLoc _self P)
  (CallFunction|RcPushRot _self R))

;; ===== GRAFO: RcPushLoc
(fn RcPushLoc (P)
  (bind _lp (Math|Transform|InverseTransformLocation (Variables|Z-Rec|GetAnchor) P))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.x _lp))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.y _lp))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.z _lp)))

;; ===== GRAFO: RcPushRot
(fn RcPushRot (R)
  (bind _lr (Math|Transform|InverseTransformRotation (Variables|Z-Rec|GetAnchor) R))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.pitch _lr))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.yaw _lr))
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (.roll _lr)))

;; ===== GRAFO: RcPushF
(fn RcPushF (V)
  (Utilities|Array|Add (Variables|Z-Rec|GetTake) (Math|Float|Clamp(Float) V)))

;; ===== GRAFO: RcAccept
;; Escribe la toma DIRECTO en el DA del fantasma (en PIE es el mismo objeto que en el editor: sobrevive al Stop).
;; Despues ghost_dump.py lo marca y lo guarda con ruta explicita.
(fn RcAccept ()
  (bind _self self)
  (bind _g (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) (Variables|Z-Rec|GetIdx)))
  (bind _da (Class|BPGhostPlayerSC|GetTake _g))
  (Class|BPGhostTakeSC|SetData :self _da :Data (Variables|Z-Rec|GetTake))
  (Class|BPGhostTakeSC|SetFrames :self _da :Frames (Variables|Z-Rec|GetN))
  (Class|BPGhostTakeSC|SetHz :self _da :Hz (Variables|Rec|GetRecHz))
  (Class|BPGhostTakeSC|SetStride :self _da :Stride 34)
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetAccepted) (Variables|Z-Rec|GetIdx) true true)
  (CallFunction|RcSound _self (Variables|Rec|GetOkSound))
  (Class|BPGhostPlayerSC|Stop :self _g)
  (Variables|Z-Rec|SetState 0)
  (CallFunction|RcShow _self))

;; ===== GRAFO: RcShow
;; Textos, botones por estado, la estacion elegida y la duracion de su toma.
(fn RcShow ()
  (bind _self self)
  (bind _s (Variables|Z-Rec|GetState))
  (bind _i (Variables|Z-Rec|GetIdx))
  (bind _da (Class|BPGhostPlayerSC|GetTake (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) _i)))
  (Variables|Z-Rec|SetDemoTime (Math|Float|Max(Float) 1.0 (Class|BPGhostTakeSC|GetDemoTime _da)))
  (bind _ok (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetAccepted) _i))
  (bind _has (> (Class|BPGhostTakeSC|GetFrames _da) 1))
  (bind _t (Utilities|String|Append (Utilities|String|ToString(Name) (Class|BPGhostTakeSC|GetId _da)) (select _ok "  [OK]" (select _has "  (ya tiene toma)" ""))))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetTitleC) (Utilities|Text|ToText(String) _t))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetInfoC) (Utilities|Text|ToText(String) (Utilities|String|Append (Class|BPGhostTakeSC|GetText _da) (Utilities|String|Append "   ·   " (Utilities|String|Append (Utilities|String|ToString(Integer) (Math|Float|Round (Variables|Z-Rec|GetDemoTime))) " s")))))
  (Rendering|Components|TextRender|SetText (Variables|Z-Rec|GetBigC) (Utilities|Text|ToText(String) (select (== _s 3) "OK?" "")))
  (CallFunction|RcStations _self)
  (CallFunction|RcBtns _self))

;; ===== GRAFO: RcBtns
(fn RcBtns ()
  (bind _s (Variables|Z-Rec|GetState))
  (for _i (range 5)
    (CallFunction|RcBtn self _i (select (< _i 3) (== _s 0) (== _s 3)))))

;; ===== GRAFO: RcBtn
(fn RcBtn (I On)
  (bind _b (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtns) I))
  (bind _tx (Utilities|Array|Get(acopy) (Variables|Z-Rec|GetBtnTxt) I))
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetBtnOn) I On true)
  (Utilities|Array|SetArrayElem (Variables|Z-Rec|GetDwell) I 0.0 true)
  (Rendering|SetVisibility _b On)
  (Rendering|SetVisibility _tx On))

;; ===== GRAFO: RcStations
;; Solo la estacion elegida: sus piezas de referencia (tag = Id de la toma) se ven; las de las demas, no.
(fn RcStations ()
  (for _i (range (Utilities|Array|Length (Variables|Rec|GetGhosts)))
    (CallFunction|RcStationOne self _i)))

;; ===== GRAFO: RcStationOne
(fn RcStationOne (I)
  (bind _da (Class|BPGhostPlayerSC|GetTake (Utilities|Array|Get(acopy) (Variables|Rec|GetGhosts) I)))
  (bind _arr (Utilities|GetAllActorswithTag (Class|BPGhostTakeSC|GetId _da)))   ;;?
  (bind _hide (!= I (Variables|Z-Rec|GetIdx)))
  (for _a _arr
    (Rendering|SetActorHiddenInGame :self _a :bNewHidden _hide)))

;; ===== GRAFO: RcSound
(fn RcSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid" (Audio|PlaySound2D Snd (Variables|Rec|GetSfxVol)))
    (:"Is Not Valid")))

;; ===== GRAFO: RcDebug
;; Gancho de PRUEBA sin visor: DebugPress (instance-editable, -1) "aprieta" un boton desde el MCP (set_properties en PIE).
;; Primero RcPress y DESPUES el reset (un bind de un getter puro se reevalua en cada uso).
(fn RcDebug ()
  (if (>= (Variables|Rec|GetDebugPress) 0)
    (CallFunction|RcPress self (Variables|Rec|GetDebugPress))
    (Variables|Rec|SetDebugPress -1)))
