;; ghost_player.dsl - BP_GhostPlayer_SC v2: el FANTASMA de una instruccion (2026-10-01).
;; Plan: docs/PLAN-FANTASMAS-V2-2026-10-01.md. Variables, componentes y parametros: ghost_spec.json (make_spec.py).
;; v1 (2026-09-30) quedo en git (80a03c9). Cambios de fondo: un fantasma COLOCADO por instruccion (su toma en `Take`),
;; componentes FIJOS del Blueprint (el Construction Script no puede AddComponentByClass), ecos = instancias de un ISM
;; (opacidad por instancia en PerInstanceCustomData[0]), vista previa en el editor (Construction Script), ancla en el
;; nivel o en la cabeza, modo EN VIVO para el grabador.
;;
;; Reglas del parser (dsl.md + gotchas): if/for/while/switch/IsValid AL FINAL de su lista; CallFunction propia con self
;; PRIMERO y argumentos CABLEADOS (un literal a una funcion propia se pierde: dsl.md §4); bool bX se lee GetX.
;; ";;?" = nombre de nodo a confirmar con ghost_nodecheck.py en el turno.
;;
;; Datos (DA BP_GhostTake_SC): Data float[] stride 34 por cuadro, en ESPACIO DEL ANCLA:
;; 0-5 grip R (x y z pitch yaw roll) · 6-11 grip L · 12-14 aim R (pitch yaw roll) · 15-17 aim L ·
;; 18 gatillo R · 19 gatillo L · 20 grip R · 21 grip L · 22-27 cabeza · 28-30 aim R (x y z) · 31-33 aim L (x y z).
;; (v1 era stride 28, sin la posicion del aim: el haz y la punta del pincel salen del AIM, no del grip.)
;; Que sostiene cada mano (HoldR/HoldL): 0 nada · 1 mano · 2 mando · 3 sensor · 4 mando + SAVE · 5 mando + paleta.
;; Extra: 0 nada · 1 esfera (se reconstruye del haz) · 2 trazo (se reconstruye de la punta).
;; Estados: 0 quieto · 1 aparece (Fade 0->1, ya se mueve) · 2 bucle · 3 pausa entre bucles · 4 se va (Fade 1->0).
;; Por mano H (0 der, 1 izq; con espejo la H fisica muestra la otra mano reflejada):
;;   Kind[H] · BodyRel[H] (grip -> malla) · PropRel[H] · BeamOn[H] · CurXf[H] · Placed[H] · Hist[H*4+k] · HistN[H].
;; Instancias del ISM del cuerpo: 0 = pose actual · 1..4 = ecos (edad 1..4); en la vista previa 1..N = cebolla.

;; ===== GRAFO: EventGraph
;; Lo que dejo el Construction Script (vista previa) se borra al dar Play. La toma se lee y se cocina aca (el negro de
;; la carga), asi Play no tiene tirones.
(event EventBeginPlay
  (bind _self self)
  (CallFunction|GhReset _self)
  (Rendering|SetActorHiddenInGame true)
  (CallFunction|GhFollowInit _self)
  (CallFunction|GhLoad _self)
  (CallFunction|GhBakeIf _self)
  (if (Variables|Ghost|GetAutoPlay)
    (Utilities|Time|SetTimerbyFunctionName _self "GhAutoPlay" (Variables|Ghost|GetAutoPlayDelay) false)))

(event EventTick (DeltaSeconds)
  (CallFunction|GhTick self (Math|Float|Min(Float) DeltaSeconds 0.0333)))

;; ===== GRAFO: ConstructionScript
;; Vista previa en el editor: el recorrido (puntos), la cebolla y la pose en PreviewTime. Sin toma: un rotulo.
(fn ConstructionScript ()
  (bind _self self)
  (CallFunction|GhReset _self)
  (CallFunction|GhLoad _self)
  (if (and (Variables|Z-Ghost|GetFound) (Variables|Ghost|GetPreview))
    (CallFunction|GhPreview _self)
    (else (CallFunction|GhNoTake _self))))

;; ===== GRAFO: Play
;; Play(Mirror): Mirror = usuario zurdo. Sin toma no hace nada y lo avisa en el log.
(fn Play (Mirror)
  (bind _self self)
  (Variables|Z-Ghost|SetMirrorOn Mirror)
  (CallFunction|GhLoadIfNeeded _self)
  (CallFunction|GhPlayNow _self))

;; ===== GRAFO: Stop
(fn Stop ()
  (bind _s (Variables|Z-Ghost|GetState))
  (if (and (> _s 0) (< _s 4))
    (Variables|Z-Ghost|SetState 4)
    (Variables|Z-Ghost|SetPlaying false)
    (CallFunction|GhSound self (Variables|Ghost|GetVanishSound))))

;; ===== GRAFO: Reanchor
(fn Reanchor ()
  (bind _self self)
  (CallFunction|GhAnchor _self (Variables|Z-Ghost|GetPlaying))
  (CallFunction|GhLayer _self))

;; ===== GRAFO: PreviewData
;; Para el grabador: la toma recien grabada (en memoria), con lo que sostiene cada mano segun el DA.
(fn PreviewData (D N)
  (Utilities|IsValid (Variables|Ghost|GetTake)
    (:"Is Valid" (CallFunction|GhPreviewGo self D N))
    (:"Is Not Valid")))

;; ===== GRAFO: GhPreviewGo
(fn GhPreviewGo (D N)
  (bind _self self)
  (CallFunction|GhLoadMeta _self)
  (Variables|Z-Ghost|SetData D)
  (Variables|Z-Ghost|SetFrames N)
  (Variables|Z-Ghost|SetFound (>= N 2))
  (Variables|Z-Ghost|SetMirrorOn false)
  (CallFunction|GhBake _self)
  (CallFunction|GhPlayNow _self))

;; ===== GRAFO: LiveStart
;; Para el grabador: lo que va a sostener el fantasma, en las manos de quien graba (sin ecos). El grabador lo mueve con
;; LiveSet en cada cuadro.
(fn LiveStart ()
  (Utilities|IsValid (Variables|Ghost|GetTake)
    (:"Is Valid" (CallFunction|GhLiveGo self))
    (:"Is Not Valid")))

;; ===== GRAFO: GhLiveGo
(fn GhLiveGo ()
  (bind _self self)
  (CallFunction|GhLoadMeta _self)
  (Variables|Z-Ghost|SetMirrorOn false)
  (Variables|Z-Ghost|SetInstN 1)
  (Variables|Z-Ghost|SetInstPreview false)
  (CallFunction|GhSetup _self)
  (Variables|Z-Ghost|SetLive true)
  (CallFunction|GhLiveAlpha _self)
  (Rendering|SetActorHiddenInGame false))

;; ===== GRAFO: LiveSet
;; Poses en MUNDO del grip y del aim (transforms) de cada mano, y los gatillos 0-1.
(fn LiveSet (Gr Gl Ar Al Tr Tl)
  (Variables|Z-Ghost|SetLiveGR Gr)
  (Variables|Z-Ghost|SetLiveGL Gl)
  (Variables|Z-Ghost|SetLiveAR Ar)
  (Variables|Z-Ghost|SetLiveAL Al)
  (Variables|Z-Ghost|SetLiveTR Tr)
  (Variables|Z-Ghost|SetLiveTL Tl)
  (if (Variables|Z-Ghost|GetLive)
    (CallFunction|GhLiveHands self)))

;; ===== GRAFO: GhLiveHands
(fn GhLiveHands ()
  (for _h (range 2)
    (CallFunction|GhLivePlace self _h)))

;; ===== GRAFO: GhLivePlace
(fn GhLivePlace (H)
  (bind _left (== H 1))
  (if (> (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 0)
    (Variables|Z-Ghost|SetPoseXf (select _left (Variables|Z-Ghost|GetLiveGL) (Variables|Z-Ghost|GetLiveGR)))
    (Variables|Z-Ghost|SetPoseAim (.rotation (select _left (Variables|Z-Ghost|GetLiveAL) (Variables|Z-Ghost|GetLiveAR))))
    (Variables|Z-Ghost|SetPoseAimLoc (.location (select _left (Variables|Z-Ghost|GetLiveAL) (Variables|Z-Ghost|GetLiveAR))))
    (Variables|Z-Ghost|SetPoseTrig (select _left (Variables|Z-Ghost|GetLiveTL) (Variables|Z-Ghost|GetLiveTR)))
    (CallFunction|GhPlace self H)))

;; ===== GRAFO: LiveStop
(fn LiveStop ()
  (CallFunction|GhReset self)
  (Rendering|SetActorHiddenInGame true))

;; ===== GRAFO: GhLiveAlpha
;; En vivo se ve lo que la mano SOSTIENE (sensor, SAVE, paleta) y el haz; el cuerpo del mando o de la mano no, porque
;; ya esta la mano real del que graba.
(fn GhLiveAlpha ()
  (for _h (range 2)
    (CallFunction|GhLiveHandAlpha self _h)))

;; ===== GRAFO: GhLiveHandAlpha
(fn GhLiveHandAlpha (H)
  (bind _self self)
  (bind _left (== H 1))
  (bind _k (Variables|Ghost|GetLiveOpacity))
  (bind _kind (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H))
  (CallFunction|GhOp _self (select _left (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)) (select (== _kind 3) _k 0.0))
  (CallFunction|GhOp _self (select _left (Variables|Default|GetHandL) (Variables|Default|GetHandR)) (* _k 0.0))
  (CallFunction|GhOp _self (select _left (Variables|Default|GetTrigL) (Variables|Default|GetTrigR)) (* _k 0.0))
  (CallFunction|GhOp _self (select _left (Variables|Default|GetPropL) (Variables|Default|GetPropR)) _k)
  (CallFunction|GhOp _self (select _left (Variables|Default|GetBeamL) (Variables|Default|GetBeamR)) (* _k 0.6)))

;; ===== GRAFO: GhLoad
(fn GhLoad ()
  (Variables|Z-Ghost|SetFound false)
  (Variables|Z-Ghost|SetBaked false)
  (Utilities|IsValid (Variables|Ghost|GetTake)
    (:"Is Valid" (CallFunction|GhLoadTk self))
    (:"Is Not Valid")))

;; ===== GRAFO: GhLoadTk
(fn GhLoadTk ()
  (bind _t (Variables|Ghost|GetTake))
  (CallFunction|GhLoadMeta self)
  (Variables|Z-Ghost|SetData (Class|BPGhostTakeSC|GetData _t))
  (Variables|Z-Ghost|SetFrames (Class|BPGhostTakeSC|GetFrames _t))
  (Variables|Z-Ghost|SetFound (>= (Variables|Z-Ghost|GetFrames) 2)))

;; ===== GRAFO: GhLoadMeta
(fn GhLoadMeta ()
  (bind _t (Variables|Ghost|GetTake))
  (Variables|Z-Ghost|SetHz (Math|Float|Max(Float) 1.0 (Class|BPGhostTakeSC|GetHz _t)))
  (Variables|Z-Ghost|SetStride (Math|Integer|Max(Integer) 28 (Class|BPGhostTakeSC|GetStride _t)))
  (Variables|Z-Ghost|SetLineText (Class|BPGhostTakeSC|GetText _t))
  (Variables|Z-Ghost|SetExtra (Class|BPGhostTakeSC|GetExtra _t))
  (Variables|Z-Ghost|SetHeadAnchor (Class|BPGhostTakeSC|GetHeadAnchor _t)))

;; ===== GRAFO: GhLoadIfNeeded
(fn GhLoadIfNeeded ()
  (if (not (Variables|Z-Ghost|GetFound))
    (CallFunction|GhLoad self)))

;; ===== GRAFO: GhBakeIf
(fn GhBakeIf ()
  (if (and (Variables|Z-Ghost|GetFound) (not (Variables|Z-Ghost|GetBaked)))
    (CallFunction|GhBake self)))

;; ===== GRAFO: GhPlayNow
(fn GhPlayNow ()
  (bind _self self)
  (if (not (Variables|Z-Ghost|GetFound))
    (Development|PrintString "GHOST: este fantasma no tiene toma (o esta vacia)")
    (else
      (Variables|Z-Ghost|SetInstN 5)
      (Variables|Z-Ghost|SetInstPreview false)
      (CallFunction|GhFollowApply _self)
      (CallFunction|GhSetup _self)
      (CallFunction|GhAnchor _self (Variables|Z-Ghost|GetFound))
      (CallFunction|GhBakeIf _self)
      (CallFunction|GhStart _self))))

;; ===== GRAFO: GhReset
;; Todo invisible SIN SetVisibility (desde el Construction Script no apaga: gotcha "SetVisibility desde el CS"):
;; los ISM sin instancias y los demas a escala 0. Sirve igual en el editor y en el juego.
(fn GhReset ()
  (bind _self self)
  (CallFunction|GhCollect _self)
  (Components|InstancedStaticMesh|ClearInstances (Variables|Default|GetBodyR))   ;;?
  (Components|InstancedStaticMesh|ClearInstances (Variables|Default|GetBodyL))
  (Components|InstancedStaticMesh|ClearInstances (Variables|Default|GetStroke))
  (Components|InstancedStaticMesh|ClearInstances (Variables|Default|GetPath))
  (Variables|Z-Ghost|SetStrokeShown 0)
  (Variables|Z-Ghost|SetState 0)
  (Variables|Z-Ghost|SetPlaying false)
  (Variables|Z-Ghost|SetLive false)
  (Actor|Tick|SetActorTickEnabled _self false)
  (for _c (Variables|Z-Ghost|GetSingles)
    (Transformation|SetRelativeScale3D _c (Math|Vector|MakeVector 0.0 0.0 0.0))))

;; ===== GRAFO: GhCollect
(fn GhCollect ()
  (bind _a (Variables|Z-Ghost|GetSingles))
  (Utilities|Array|Clear _a)
  (Utilities|Array|Add _a (Variables|Default|GetTrigR))
  (Utilities|Array|Add _a (Variables|Default|GetTrigL))
  (Utilities|Array|Add _a (Variables|Default|GetHandR))
  (Utilities|Array|Add _a (Variables|Default|GetHandL))
  (Utilities|Array|Add _a (Variables|Default|GetPropR))
  (Utilities|Array|Add _a (Variables|Default|GetPropL))
  (Utilities|Array|Add _a (Variables|Default|GetBeamR))
  (Utilities|Array|Add _a (Variables|Default|GetBeamL))
  (Utilities|Array|Add _a (Variables|Default|GetOrb))
  (Utilities|Array|Add _a (Variables|Default|GetLabel)))

;; ===== GRAFO: GhSetup
;; Que muestra cada mano (con espejo, la mano fisica H muestra lo grabado por la otra), mallas, materiales y colores.
(fn GhSetup ()
  (bind _self self)
  (CallFunction|GhReset _self)
  (bind _t (Variables|Ghost|GetTake))
  (bind _m (Variables|Z-Ghost|GetMirrorOn))
  (bind _hr (Class|BPGhostTakeSC|GetHoldR _t))
  (bind _hl (Class|BPGhostTakeSC|GetHoldL _t))
  (bind _br (Class|BPGhostTakeSC|GetBeamRight _t))
  (bind _bl (Class|BPGhostTakeSC|GetBeamLeft _t))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetKind))
  (Utilities|Array|Add (Variables|Z-Ghost|GetKind) (select _m _hl _hr))
  (Utilities|Array|Add (Variables|Z-Ghost|GetKind) (select _m _hr _hl))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetBeamOn))
  (Utilities|Array|Add (Variables|Z-Ghost|GetBeamOn) (select _m _bl _br))
  (Utilities|Array|Add (Variables|Z-Ghost|GetBeamOn) (select _m _br _bl))
  (CallFunction|GhArrInit _self)
  (CallFunction|GhFixed _self)
  (for _h (range 2)
    (CallFunction|GhSetupHand _self _h)))

;; ===== GRAFO: GhArrInit
(fn GhArrInit ()
  (Utilities|Array|Clear (Variables|Z-Ghost|GetBodyRel))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetPropRel))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetCurXf))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetPlaced))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetHistN))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetHist))
  (for _i (range 8)
    (CallFunction|GhArrAdd self _i)))

;; ===== GRAFO: GhArrAdd
(fn GhArrAdd (I)
  (bind _id (Math|Transform|MakeTransform))
  (Utilities|Array|Add (Variables|Z-Ghost|GetHist) _id)
  (if (< I 2)
    (Utilities|Array|Add (Variables|Z-Ghost|GetBodyRel) _id)
    (Utilities|Array|Add (Variables|Z-Ghost|GetPropRel) _id)
    (Utilities|Array|Add (Variables|Z-Ghost|GetCurXf) _id)
    (Utilities|Array|Add (Variables|Z-Ghost|GetPlaced) false)
    (Utilities|Array|Add (Variables|Z-Ghost|GetHistN) 0)))

;; ===== GRAFO: GhFixed
;; Las piezas que no dependen de la mano: haces, esfera, trazo, puntos del recorrido y el rotulo.
(fn GhFixed ()
  (bind _self self)
  (bind _gc (Variables|Ghost|GetGhostColor))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetBeamR) (Variables|GhostMesh|GetBeamMesh))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetBeamL) (Variables|GhostMesh|GetBeamMesh))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetOrb) (Variables|GhostMesh|GetOrbMesh))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetStroke) (Variables|GhostMesh|GetStrokeMesh))
  (Components|StaticMesh|SetStaticMesh (Variables|Default|GetPath) (Variables|GhostMesh|GetPathMesh))
  (CallFunction|GhPrep _self (Variables|Default|GetBeamR) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetBeamL) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetOrb) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetStroke) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetPath) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetHandR) _gc)
  (CallFunction|GhPrep _self (Variables|Default|GetHandL) _gc)
  (bind _tr (Variables|Default|GetLabel))
  (Rendering|Components|TextRender|SetTextMaterial _tr (Variables|GhostMesh|GetTextMat))
  (Rendering|Components|TextRender|SetWorldSize _tr (Variables|Ghost|GetTextSize))
  (Rendering|Components|TextRender|SetHorizontalAlignment _tr "EHTA_Center")
  (Rendering|Components|TextRender|SetVerticalAlignment _tr "EVRTA_TextCenter")
  (Collision|SetCollisionEnabled _tr "NoCollision"))

;; ===== GRAFO: GhSetupHand
;; Sin ramas: todo se configura; lo que la mano no usa nunca se coloca (queda a escala 0 o sin instancias).
(fn GhSetupHand (H)
  (bind _self self)
  (bind _left (== H 1))
  (bind _k (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H))
  (bind _body (select _left (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)))
  (bind _trig (select _left (Variables|Default|GetTrigL) (Variables|Default|GetTrigR)))
  (bind _prop (select _left (Variables|Default|GetPropL) (Variables|Default|GetPropR)))
  (Components|StaticMesh|SetStaticMesh _body (select (== _k 3) (Variables|GhostMesh|GetSensorMesh) (select _left (Variables|GhostMesh|GetBodyMeshL) (Variables|GhostMesh|GetBodyMeshR))))
  (Components|StaticMesh|SetStaticMesh _trig (select _left (Variables|GhostMesh|GetTrigMeshL) (Variables|GhostMesh|GetTrigMeshR)))
  (Components|StaticMesh|SetStaticMesh _prop (select (== _k 4) (Variables|GhostMesh|GetSaveMesh) (Variables|GhostMesh|GetPaletteMesh)))
  (CallFunction|GhPrep _self _body (Variables|Ghost|GetGhostColor))
  (CallFunction|GhPrep _self _prop (Variables|Ghost|GetGhostColor))
  (CallFunction|GhPrep _self _trig (Variables|Ghost|GetTriggerColor))
  (Rendering|Material|SetScalarParameterValueonMaterials _trig "PressGain" (Variables|Ghost|GetTriggerGlow))
  (CallFunction|GhRels _self H)
  (CallFunction|GhInstInit _self _body (select (>= _k 2) (Variables|Z-Ghost|GetInstN) 0)))

;; ===== GRAFO: GhRels
;; grip -> malla de la mano fisica H. El sensor esta pensado para la DERECHA y el SAVE y la paleta para la IZQUIERDA:
;; en la otra mano van reflejados (GhMirXf).
(fn GhRels (H)
  (bind _self self)
  (bind _left (== H 1))
  (bind _k (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H))
  (bind _px (select (== _k 4) (Variables|GhostMesh|GetSaveXf) (Variables|GhostMesh|GetPaletteXf)))
  (CallFunction|GhMirXf _self (Variables|GhostMesh|GetSensorXf))
  (Variables|Z-Ghost|SetSensorRel (select _left (Variables|Z-Ghost|GetMirXf) (Variables|GhostMesh|GetSensorXf)))
  (CallFunction|GhMirXf _self _px)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetPropRel) H (select _left _px (Variables|Z-Ghost|GetMirXf)) true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetBodyRel) H (select (== _k 1) (select _left (Variables|GhostMesh|GetHandXfL) (Variables|GhostMesh|GetHandXfR)) (select (== _k 3) (Variables|Z-Ghost|GetSensorRel) (select _left (Variables|GhostMesh|GetGripToMeshL) (Variables|GhostMesh|GetGripToMeshR)))) true))

;; ===== GRAFO: GhMirXf
;; Reflejo por el plano XZ del grip: y -> -y, yaw -> -yaw, roll -> -roll, escala Y negada (refleja tambien la malla).
(fn GhMirXf (Xf)
  (bind _l (.location Xf))
  (bind _r (.rotation Xf))
  (bind _s (.scale Xf))
  (Variables|Z-Ghost|SetMirXf (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector (.x _l) (* (.y _l) -1.0) (.z _l)) :Rotation (Math|Rotator|MakeRotator :Roll (* (.roll _r) -1.0) :Pitch (.pitch _r) :Yaw (* (.yaw _r) -1.0)) :Scale (Math|Vector|MakeVector (.x _s) (* (.y _s) -1.0) (.z _s)))))

;; ===== GRAFO: GhPrep
;; El material va PRIMERO (SetMaterial reemplaza la MID) y despues el color (crea la MID).
(fn GhPrep (C Col)
  (CallFunction|GhMats self C)
  (Collision|SetCollisionEnabled C "NoCollision")
  (Rendering|SetCastShadow C false)
  (Rendering|Material|SetVectorParameterValueonMaterials C "Color" (Math|Conversions|ToVector(LinearColor) Col)))

;; ===== GRAFO: GhMats
(fn GhMats (C)
  (for _i (range (Rendering|Material|GetNumMaterials C))   ;;?
    (Rendering|Material|SetMaterial C _i (Variables|GhostMesh|GetGhostMat))))

;; ===== GRAFO: GhInstInit
;; N instancias a escala 0, cada una con su opacidad propia (custom data 0): juego = EchoAlpha por edad; vista
;; previa = 1 la actual y PreviewOnion la cebolla.
(fn GhInstInit (Ism N)
  (bind _self self)
  (Components|InstancedStaticMesh|ClearInstances Ism)
  (Components|InstancedStaticMesh|SetNumCustomDataFloats Ism 1)   ;;?
  (Utilities|Array|Clear (Variables|Z-Ghost|GetTmpXf))
  (CallFunction|GhInstFill _self N)
  (Components|InstancedStaticMesh|AddInstances Ism (Variables|Z-Ghost|GetTmpXf) false true)   ;; InstanceTransforms bShouldReturnIndices bWorldSpace
  (CallFunction|GhInstData _self Ism N))

;; ===== GRAFO: GhInstFill
(fn GhInstFill (N)
  (for _i (range N)
    (Utilities|Array|Add (Variables|Z-Ghost|GetTmpXf) (Math|Transform|MakeTransform :Scale (Math|Vector|MakeVector 0.0 0.0 0.0)))))

;; ===== GRAFO: GhInstData
(fn GhInstData (Ism N)
  (bind _ea (Variables|Ghost|GetEchoAlpha))
  (bind _n (Utilities|Array|Length _ea))
  (for _i (range N)
    (Components|InstancedStaticMesh|SetCustomDataValue Ism _i 0 (select (Variables|Z-Ghost|GetInstPreview) (select (== _i 0) 1.0 (Variables|Ghost|GetPreviewOnion)) (select (< _i _n) (Utilities|Array|Get(acopy) _ea (Math|Integer|Min(Integer) _i (- _n 1))) 0.0)) true)))   ;;?

;; ===== GRAFO: GhAnchor
;; Game y toma de CABEZA (Breath, Heart): posicion de la cabeza + yaw del pawn. Si no: el actor (ubicacion + giro).
(fn GhAnchor (Game)
  (if (and Game (Variables|Z-Ghost|GetHeadAnchor))
    (CallFunction|GhAnchorHead self)
    (else (Variables|Z-Ghost|SetAnchor (Math|Transform|MakeTransform :Location (Transformation|GetActorLocation) :Rotation (Transformation|GetActorRotation))))))

;; ===== GRAFO: GhAnchorHead
(fn GhAnchorHead ()
  (bind _cam (Game|GetPlayerCameraManager 0))
  (bind _yaw (.yaw (Transformation|GetActorRotation (Game|GetPlayerPawn 0))))
  (Variables|Z-Ghost|SetAnchor (Math|Transform|MakeTransform :Location (Camera|GetCameraLocation _cam) :Rotation (Math|Rotator|MakeRotator :Yaw _yaw))))

;; ===== GRAFO: GhLayer
;; El trazo y los puntos viven en el espacio del ancla: el componente va AL ancla, con la Y negada si hay espejo.
(fn GhLayer ()
  (bind _an (Variables|Z-Ghost|GetAnchor))
  (bind _sy (select (Variables|Z-Ghost|GetMirrorOn) -1.0 1.0))
  (bind _xf (Math|Transform|MakeTransform :Location (.location _an) :Rotation (.rotation _an) :Scale (Math|Vector|MakeVector 1.0 _sy 1.0)))
  (Transformation|SetWorldTransform (Variables|Default|GetStroke) _xf)
  (Transformation|SetWorldTransform (Variables|Default|GetPath) _xf))

;; ===== GRAFO: GhFollowInit
;; FollowTag: el fantasma acompana a un objeto que el director mueve en el juego (timbre, sensor), conservando la
;; distancia que quedo en el editor. Solo posicion (el sensor gira).
(fn GhFollowInit ()
  (if (!= (Variables|Ghost|GetFollowTag) "None")
    (CallFunction|GhFollowFind self)))

;; ===== GRAFO: GhFollowFind
(fn GhFollowFind ()
  (bind _arr (Utilities|GetAllActorswithTag (Variables|Ghost|GetFollowTag)))   ;;?
  (if (> (Utilities|Array|Length _arr) 0)
    (Variables|Z-Ghost|SetFollowActor (Utilities|Array|Get(acopy) _arr 0))
    (Variables|Z-Ghost|SetFollowOff (- (Transformation|GetActorLocation) (Transformation|GetActorLocation (Utilities|Array|Get(acopy) _arr 0))))))

;; ===== GRAFO: GhFollowApply
(fn GhFollowApply ()
  (bind _a (Variables|Z-Ghost|GetFollowActor))
  (Utilities|IsValid _a
    (:"Is Valid" (Transformation|SetActorLocation (+ (Transformation|GetActorLocation _a) (Variables|Z-Ghost|GetFollowOff))))   ;;?
    (:"Is Not Valid")))

;; ===== GRAFO: GhBake
;; Una pasada por la toma: la esfera (Extra 1), el trazo (Extra 2) y los puntos del recorrido. En el espacio del ancla
;; y SIN espejo (el espejo lo aplica GhLayer / GhOrbPut).
(fn GhBake ()
  (bind _self self)
  (Utilities|Array|Clear (Variables|Z-Ghost|GetOrbPath))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetStrokeXf))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetStrokeF))
  (Utilities|Array|Clear (Variables|Z-Ghost|GetPathXf))
  (Variables|Z-Ghost|SetBkHeld false)
  (Variables|Z-Ghost|SetBkPrevT 0.0)
  (Variables|Z-Ghost|SetBkPos (Variables|Ghost|GetOrbRest))
  (Variables|Z-Ghost|SetBkHasPrev false)
  (Variables|Z-Ghost|SetBaked true)
  (for _f (range (Variables|Z-Ghost|GetFrames))
    (CallFunction|GhBakeOne _self _f)))

;; ===== GRAFO: GhBakeOne
;; Mano de la accion = la DERECHA de los datos (grip 0-5, aim 12-14 y 28-30, gatillo 18).
(fn GhBakeOne (F)
  (bind _self self)
  (bind _d (Variables|Z-Ghost|GetData))
  (bind _o (* F (Variables|Z-Ghost|GetStride)))
  (bind _gl (Math|Vector|MakeVector (Utilities|Array|Get(acopy) _d _o) (Utilities|Array|Get(acopy) _d (+ _o 1)) (Utilities|Array|Get(acopy) _d (+ _o 2))))
  (bind _gr (Math|Rotator|MakeRotator :Roll (Utilities|Array|Get(acopy) _d (+ _o 5)) :Pitch (Utilities|Array|Get(acopy) _d (+ _o 3)) :Yaw (Utilities|Array|Get(acopy) _d (+ _o 4))))
  (Variables|Z-Ghost|SetBkGrip (Math|Transform|MakeTransform :Location _gl :Rotation _gr))
  (Variables|Z-Ghost|SetBkAim (Math|Rotator|MakeRotator :Roll (Utilities|Array|Get(acopy) _d (+ _o 14)) :Pitch (Utilities|Array|Get(acopy) _d (+ _o 12)) :Yaw (Utilities|Array|Get(acopy) _d (+ _o 13))))
  (Variables|Z-Ghost|SetBkTrig (Utilities|Array|Get(acopy) _d (+ _o 18)))
  (Variables|Z-Ghost|SetBkAimLoc (select (>= (Variables|Z-Ghost|GetStride) 34) (Math|Vector|MakeVector (Utilities|Array|Get(acopy) _d (+ _o 28)) (Utilities|Array|Get(acopy) _d (+ _o 29)) (Utilities|Array|Get(acopy) _d (+ _o 30))) _gl))
  (CallFunction|GhBakePath _self F)
  (bind _x (Variables|Z-Ghost|GetExtra))
  (if (== _x 1)
    (CallFunction|GhBakeOrb _self)
    (elif (== _x 2)
      (CallFunction|GhBakeStroke _self F))))

;; ===== GRAFO: GhBakePath
;; Un punto cada 3 cuadros (10 por segundo) donde pasa el grip: el recorrido entero, solo para el editor.
(fn GhBakePath (F)
  (bind _s (Variables|Ghost|GetPathDot))
  (if (== (Math|Integer|%(Integer) F 3) 0)
    (Utilities|Array|Add (Variables|Z-Ghost|GetPathXf) (Math|Transform|MakeTransform :Location (.location (Variables|Z-Ghost|GetBkGrip)) :Scale (Math|Vector|MakeVector _s _s _s)))))

;; ===== GRAFO: GhBakeOrb
;; La esfera: espera en OrbRest; si el gatillo BAJA con el haz pasando a menos de OrbGrab de ella, la agarra y viaja a
;; OrbHoldDist sobre el haz (VInterpTo, como la esfera real); al soltar queda donde esta.
;; (cada bind de un getter se reevalua en cada uso: BkPos y BkPrevT se leen antes de escribirse)
(fn GhBakeOrb ()
  (bind _o (Variables|Z-Ghost|GetBkAimLoc))
  (bind _dir (Math|Vector|GetForwardVector (Variables|Z-Ghost|GetBkAim)))
  (bind _t (Variables|Z-Ghost|GetBkTrig))
  (bind _v (- (Variables|Z-Ghost|GetBkPos) _o))
  (bind _along (Math|Vector|DotProduct _v _dir))
  (bind _dist (Math|Vector|VectorLength (- _v (* _dir _along))))   ;;?
  (bind _press (and (>= _t 0.5) (< (Variables|Z-Ghost|GetBkPrevT) 0.5)))
  (Variables|Z-Ghost|SetBkHeld (and (>= _t 0.5) (or (Variables|Z-Ghost|GetBkHeld) (and _press (and (> _along 0.0) (< _dist (Variables|Ghost|GetOrbGrab)))))))
  (Variables|Z-Ghost|SetBkPos (select (Variables|Z-Ghost|GetBkHeld) (Math|Vector|VInterpTo (Variables|Z-Ghost|GetBkPos) (+ _o (* _dir (Variables|Ghost|GetOrbHoldDist))) (/ 1.0 (Variables|Z-Ghost|GetHz)) (Variables|Ghost|GetOrbSpeed)) (Variables|Z-Ghost|GetBkPos)))   ;;?
  (Variables|Z-Ghost|SetBkPrevT _t)
  (Utilities|Array|Add (Variables|Z-Ghost|GetOrbPath) (Variables|Z-Ghost|GetBkPos)))

;; ===== GRAFO: GhBakeStroke
;; El trazo: la punta del pincel (TipOffset desde el AIM, como SM_Tip del pincel real) mientras el gatillo esta apretado.
(fn GhBakeStroke (F)
  (bind _self self)
  (Variables|Z-Ghost|SetBkTip (Math|Transform|TransformLocation (Math|Transform|MakeTransform :Location (Variables|Z-Ghost|GetBkAimLoc) :Rotation (Variables|Z-Ghost|GetBkAim)) (Variables|GhostMesh|GetTipOffset)))
  (CallFunction|GhSegMaybe _self F)
  (Variables|Z-Ghost|SetBkPrevTip (Variables|Z-Ghost|GetBkTip))
  (Variables|Z-Ghost|SetBkHasPrev (>= (Variables|Z-Ghost|GetBkTrig) 0.5)))

;; ===== GRAFO: GhSegMaybe
(fn GhSegMaybe (F)
  (if (and (>= (Variables|Z-Ghost|GetBkTrig) 0.5) (Variables|Z-Ghost|GetBkHasPrev))
    (CallFunction|GhSeg self F)))

;; ===== GRAFO: GhSeg
;; Un tramo = cilindro del motor (alto 100 en Z, diametro 100, centrado) entre la punta anterior y la actual.
(fn GhSeg (F)
  (bind _a (Variables|Z-Ghost|GetBkPrevTip))
  (bind _b (Variables|Z-Ghost|GetBkTip))
  (bind _w (/ (Variables|Ghost|GetStrokeWidth) 100.0))
  (bind _len (Math|Vector|VectorLength (- _b _a)))
  (Utilities|Array|Add (Variables|Z-Ghost|GetStrokeXf) (Math|Transform|MakeTransform :Location (* (+ _a _b) 0.5) :Rotation (Math|Rotator|MakeRotfromZ (- _b _a)) :Scale (Math|Vector|MakeVector _w _w (/ (+ _len 0.2) 100.0))))   ;;? MakeRotfromZ
  (Utilities|Array|Add (Variables|Z-Ghost|GetStrokeF) F))

;; ===== GRAFO: GhStart
;; Orden anti-chispazo: pose y opacidad 0 ANTES de mostrar el actor (memoria "de un frame a otro y vuelve").
(fn GhStart ()
  (bind _self self)
  (Variables|Z-Ghost|SetT 0.0)
  (Variables|Z-Ghost|SetGapT 0.0)
  (Variables|Z-Ghost|SetStepIdx -1)
  (Variables|Z-Ghost|SetLoopCount 0)
  (Variables|Z-Ghost|SetFade 0.0)
  (Variables|Z-Ghost|SetLoopK 1.0)
  (Variables|Z-Ghost|SetState 1)
  (Variables|Z-Ghost|SetPlaying true)
  (CallFunction|GhLayer _self)
  (CallFunction|GhRestart _self)
  (CallFunction|GhJump _self (Variables|Z-Ghost|GetStrokeShown))
  (CallFunction|GhText _self)
  (CallFunction|GhAlpha _self)
  (Rendering|SetActorHiddenInGame false)
  (Actor|Tick|SetActorTickEnabled _self true)
  (CallFunction|GhSound _self (Variables|Ghost|GetAppearSound)))

;; ===== GRAFO: GhRestart
;; Vuelta al cuadro 0: sin ecos y sin trazo. (GhStart pasa StrokeShown, que aca queda en 0, como el paso 0.)
(fn GhRestart ()
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHistN) 0 0 true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHistN) 1 0 true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetPlaced) 0 false true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetPlaced) 1 false true)
  (Components|InstancedStaticMesh|ClearInstances (Variables|Default|GetStroke))
  (Variables|Z-Ghost|SetStrokeShown 0))

;; ===== GRAFO: GhSound
(fn GhSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid" (Audio|PlaySound2D Snd (Variables|Ghost|GetSfxVol)))
    (:"Is Not Valid")))

;; ===== GRAFO: GhTick
(fn GhTick (Dt)
  (bind _self self)
  (CallFunction|GhFadeStep _self Dt)
  (CallFunction|GhRun _self Dt)
  (CallFunction|GhAlpha _self)
  (CallFunction|GhEnd _self))

;; ===== GRAFO: GhFadeStep
(fn GhFadeStep (Dt)
  (bind _s (Variables|Z-Ghost|GetState))
  (bind _in (/ Dt (Math|Float|Max(Float) 0.01 (Variables|Ghost|GetFadeIn))))
  (bind _out (/ Dt (Math|Float|Max(Float) 0.01 (Variables|Ghost|GetFadeOut))))
  (Variables|Z-Ghost|SetFade (Math|Float|Clamp(Float) (select (== _s 4) (- (Variables|Z-Ghost|GetFade) _out) (+ (Variables|Z-Ghost|GetFade) _in))))
  (if (and (== _s 1) (>= (Variables|Z-Ghost|GetFade) 1.0))
    (Variables|Z-Ghost|SetState 2)))

;; ===== GRAFO: GhRun
(fn GhRun (Dt)
  (bind _self self)
  (bind _s (Variables|Z-Ghost|GetState))
  (bind _dur (/ (Math|Conversions|ToFloat(Integer) (- (Variables|Z-Ghost|GetFrames) 1)) (Math|Float|Max(Float) 1.0 (Variables|Z-Ghost|GetHz))))
  (if (== _s 3)
    (CallFunction|GhGap _self Dt)
    (elif (> _s 0)
      (CallFunction|GhAdvance _self Dt _dur))))

;; ===== GRAFO: GhAdvance
;; LoopK: en el primer bucle vale 1 (la entrada la hace Fade); desde el segundo sube en LoopFade. En el estado 4 no se
;; toca (si Stop llega en la pausa, reponerlo a 1 haria reaparecer al fantasma un cuadro antes de irse).
(fn GhAdvance (Dt Dur)
  (bind _self self)
  (Variables|Z-Ghost|SetT (+ (Variables|Z-Ghost|GetT) Dt))
  (Variables|Z-Ghost|SetLoopK (select (== (Variables|Z-Ghost|GetState) 4) (Variables|Z-Ghost|GetLoopK) (select (> (Variables|Z-Ghost|GetLoopCount) 0) (Math|Float|Clamp(Float) (/ (Variables|Z-Ghost|GetT) (Math|Float|Max(Float) 0.01 (Variables|Ghost|GetLoopFade)))) 1.0)))
  (CallFunction|GhStepCheck _self Dur)
  (CallFunction|GhLoopCheck _self Dur))

;; ===== GRAFO: GhStepCheck
(fn GhStepCheck (Dur)
  (bind _step (Math|Float|Floor (* (Math|Float|Min(Float) (Variables|Z-Ghost|GetT) Dur) (Variables|Ghost|GetStepHz))))
  (if (!= _step (Variables|Z-Ghost|GetStepIdx))
    (CallFunction|GhJump self _step)))

;; ===== GRAFO: GhLoopCheck
(fn GhLoopCheck (Dur)
  (if (and (== (Variables|Z-Ghost|GetState) 2) (>= (Variables|Z-Ghost|GetT) Dur))
    (Variables|Z-Ghost|SetState 3)
    (Variables|Z-Ghost|SetGapT 0.0)))

;; ===== GRAFO: GhGap
;; Pausa entre bucles: LoopK baja 1 -> 0 en LoopFade; al cumplir LoopGap vuelve a empezar desde el cuadro 0.
(fn GhGap (Dt)
  (bind _self self)
  (Variables|Z-Ghost|SetGapT (+ (Variables|Z-Ghost|GetGapT) Dt))
  (Variables|Z-Ghost|SetLoopK (- 1.0 (Math|Float|Clamp(Float) (/ (Variables|Z-Ghost|GetGapT) (Math|Float|Max(Float) 0.01 (Variables|Ghost|GetLoopFade))))))
  (if (>= (Variables|Z-Ghost|GetGapT) (Variables|Ghost|GetLoopGap))
    (Variables|Z-Ghost|SetT 0.0)
    (Variables|Z-Ghost|SetLoopK 0.0)
    (Variables|Z-Ghost|SetLoopCount (+ (Variables|Z-Ghost|GetLoopCount) 1))
    (Variables|Z-Ghost|SetState 2)
    (CallFunction|GhRestart _self)
    (CallFunction|GhJump _self (Variables|Z-Ghost|GetStrokeShown))))

;; ===== GRAFO: GhEnd
(fn GhEnd ()
  (if (and (== (Variables|Z-Ghost|GetState) 4) (<= (Variables|Z-Ghost|GetFade) 0.0))
    (CallFunction|GhReset self)
    (Rendering|SetActorHiddenInGame true)))

;; ===== GRAFO: GhJump
;; S = indice de paso. Cuadro = round(S / StepHz * Hz), con tope en el ultimo.
(fn GhJump (S)
  (bind _self self)
  (Variables|Z-Ghost|SetStepIdx S)
  (Variables|Z-Ghost|SetCurF (Math|Integer|Min(Integer) (- (Variables|Z-Ghost|GetFrames) 1) (Math|Float|Round (* (/ (Math|Conversions|ToFloat(Integer) S) (Math|Float|Max(Float) 1.0 (Variables|Ghost|GetStepHz))) (Variables|Z-Ghost|GetHz)))))
  (CallFunction|GhOrbAt _self)
  (CallFunction|GhStrokeTo _self)
  (for _h (range 2)
    (CallFunction|GhJumpHand _self _h)))

;; ===== GRAFO: GhJumpHand
(fn GhJumpHand (H)
  (bind _self self)
  (if (> (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 0)
    (CallFunction|GhPush _self H)
    (CallFunction|GhPose _self (Variables|Z-Ghost|GetCurF) H)
    (CallFunction|GhPlace _self H)))

;; ===== GRAFO: GhPush
;; Los ecos de la mano H corren un lugar: el mas nuevo toma la pose que tenia la actual.
(fn GhPush (H)
  (bind _b (* H 4))
  (bind _h (Variables|Z-Ghost|GetHist))
  (if (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetPlaced) H)
    (Utilities|Array|SetArrayElem _h (+ _b 3) (Utilities|Array|Get(acopy) _h (+ _b 2)) true)
    (Utilities|Array|SetArrayElem _h (+ _b 2) (Utilities|Array|Get(acopy) _h (+ _b 1)) true)
    (Utilities|Array|SetArrayElem _h (+ _b 1) (Utilities|Array|Get(acopy) _h _b) true)
    (Utilities|Array|SetArrayElem _h _b (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetCurXf) H) true)
    (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHistN) H (Math|Integer|Min(Integer) 4 (+ (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetHistN) H) 1)) true)))

;; ===== GRAFO: GhPose
;; Pose del cuadro F para la mano fisica H, en MUNDO. Con espejo lee la otra mano y refleja: y -> -y, yaw y roll -> -.
(fn GhPose (F H)
  (bind _m (Variables|Z-Ghost|GetMirrorOn))
  (bind _src (select _m (- 1 H) H))
  (bind _d (Variables|Z-Ghost|GetData))
  (bind _o (* F (Variables|Z-Ghost|GetStride)))
  (bind _b (+ _o (* _src 6)))
  (bind _ab (+ _o (+ 12 (* _src 3))))
  (bind _sy (select _m -1.0 1.0))
  (bind _loc (Math|Vector|MakeVector (Utilities|Array|Get(acopy) _d _b) (* _sy (Utilities|Array|Get(acopy) _d (+ _b 1))) (Utilities|Array|Get(acopy) _d (+ _b 2))))
  (bind _rot (Math|Rotator|MakeRotator :Roll (* _sy (Utilities|Array|Get(acopy) _d (+ _b 5))) :Pitch (Utilities|Array|Get(acopy) _d (+ _b 3)) :Yaw (* _sy (Utilities|Array|Get(acopy) _d (+ _b 4)))))
  (bind _aim (Math|Rotator|MakeRotator :Roll (* _sy (Utilities|Array|Get(acopy) _d (+ _ab 2))) :Pitch (Utilities|Array|Get(acopy) _d _ab) :Yaw (* _sy (Utilities|Array|Get(acopy) _d (+ _ab 1)))))
  (bind _an (Variables|Z-Ghost|GetAnchor))
  (Variables|Z-Ghost|SetPoseXf (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Location _loc :Rotation _rot) _an))
  (Variables|Z-Ghost|SetPoseAim (Math|Transform|TransformRotation _an _aim))
  (bind _al (+ _o (+ 28 (* _src 3))))
  (bind _ha (>= (Variables|Z-Ghost|GetStride) 34))
  (Variables|Z-Ghost|SetPoseAimLoc (select _ha (Math|Transform|TransformLocation _an (Math|Vector|MakeVector (Utilities|Array|Get(acopy) _d _al) (* _sy (Utilities|Array|Get(acopy) _d (+ _al 1))) (Utilities|Array|Get(acopy) _d (+ _al 2)))) (.location (Variables|Z-Ghost|GetPoseXf))))
  (Variables|Z-Ghost|SetPoseTrig (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) _d (+ _o (+ 18 _src))))))

;; ===== GRAFO: GhPlace
;; Lleva la mano H a la pose recien calculada (PoseXf/PoseAim/PoseTrig): cuerpo y ecos, gatillo, lo que sostiene, haz.
(fn GhPlace (H)
  (bind _self self)
  (bind _mx (Math|Transform|ComposeTransforms (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetBodyRel) H) (Variables|Z-Ghost|GetPoseXf)))
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetCurXf) H _mx true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetPlaced) H true true)
  (CallFunction|GhPlaceTrig _self H _mx)
  (CallFunction|GhPlaceProp _self H)
  (CallFunction|GhPlaceBeam _self H)
  (CallFunction|GhPlaceBody _self H _mx))

;; ===== GRAFO: GhPlaceBody
(fn GhPlaceBody (H Mx)
  (if (== (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 1)
    (Transformation|SetWorldTransform (select (== H 1) (Variables|Default|GetHandL) (Variables|Default|GetHandR)) Mx)
    (else (CallFunction|GhPlaceIsm self H Mx))))

;; ===== GRAFO: GhPlaceIsm
(fn GhPlaceIsm (H Mx)
  (bind _ism (select (== H 1) (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)))
  (Components|InstancedStaticMesh|UpdateInstanceTransform _ism 0 Mx true true true)   ;;? InstanceIndex NewInstanceTransform bWorldSpace bMarkRenderStateDirty bTeleport
  (if (not (Variables|Z-Ghost|GetInstPreview))
    (CallFunction|GhEchoes self H)))

;; ===== GRAFO: GhEchoes
(fn GhEchoes (H)
  (for _k (range 4)
    (CallFunction|GhEchoInst self H _k)))

;; ===== GRAFO: GhEchoInst
;; Eco K (edad K+1) = instancia K+1. Los que todavia no tienen pose quedan a escala 0.
(fn GhEchoInst (H K)
  (bind _ism (select (== H 1) (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)))
  (bind _on (< K (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetHistN) H)))
  (Components|InstancedStaticMesh|UpdateInstanceTransform _ism (+ K 1) (select _on (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetHist) (+ (* H 4) K)) (Math|Transform|MakeTransform :Scale (Math|Vector|MakeVector 0.0 0.0 0.0))) true true true))

;; ===== GRAFO: GhPlaceTrig
(fn GhPlaceTrig (H Mx)
  (bind _k (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H))
  (if (or (== _k 2) (>= _k 4))
    (CallFunction|GhTrigSet self H (Variables|Z-Ghost|GetPoseTrig) Mx)))

;; ===== GRAFO: GhTrigSet
;; El gatillo gira en su bisagra (datos de BP_QuestCtrl_SC: pivote R, eje R; L = x del pivote negado, eje (ax,-ay,-az))
;; y brilla con Pressed (su propio color: TriggerColor).
(fn GhTrigSet (H V Mx)
  (bind _left (== H 1))
  (bind _pr (Variables|GhostMesh|GetHingePivotR))
  (bind _ar (Variables|GhostMesh|GetHingeAxisR))
  (bind _piv (select _left (Math|Vector|MakeVector (* (.x _pr) -1.0) (.y _pr) (.z _pr)) _pr))
  (bind _ax (select _left (Math|Vector|MakeVector (.x _ar) (* (.y _ar) -1.0) (* (.z _ar) -1.0)) _ar))
  (bind _rot (Math|Vector|RotatorfromAxisandAngle _ax (* (* (Variables|GhostMesh|GetPressSign) V) (Variables|GhostMesh|GetPressDegrees))))
  (bind _tr (select _left (Variables|Default|GetTrigL) (Variables|Default|GetTrigR)))
  (Transformation|SetWorldTransform _tr (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Location _piv :Rotation _rot) Mx))
  (Rendering|Material|SetScalarParameterValueonMaterials _tr "Pressed" V))

;; ===== GRAFO: GhPlaceProp
(fn GhPlaceProp (H)
  (if (>= (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 4)
    (Transformation|SetWorldTransform (select (== H 1) (Variables|Default|GetPropL) (Variables|Default|GetPropR)) (Math|Transform|ComposeTransforms (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetPropRel) H) (Variables|Z-Ghost|GetPoseXf)))))

;; ===== GRAFO: GhPlaceBeam
(fn GhPlaceBeam (H)
  (if (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetBeamOn) H)
    (CallFunction|GhBeamSet self H)))

;; ===== GRAFO: GhBeamSet
;; Haz: cilindro del motor (alto 100 en Z, radio 50, centrado), desde el AIM y acostado sobre el con un pitch -90.
(fn GhBeamSet (H)
  (bind _len (Variables|Ghost|GetBeamLength))
  (bind _rad (/ (Variables|Ghost|GetBeamRadius) 50.0))
  (bind _r (Variables|Z-Ghost|GetPoseAim))
  (bind _fwd (Math|Vector|GetForwardVector _r))
  (bind _rb (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator :Pitch -90.0) _r))
  (Transformation|SetWorldTransform (select (== H 1) (Variables|Default|GetBeamL) (Variables|Default|GetBeamR)) (Math|Transform|MakeTransform :Location (+ (Variables|Z-Ghost|GetPoseAimLoc) (* _fwd (* _len 0.5))) :Rotation _rb :Scale (Math|Vector|MakeVector _rad _rad (/ _len 100.0)))))

;; ===== GRAFO: GhOrbAt
(fn GhOrbAt ()
  (if (and (== (Variables|Z-Ghost|GetExtra) 1) (> (Utilities|Array|Length (Variables|Z-Ghost|GetOrbPath)) 0))
    (CallFunction|GhOrbPut self)))

;; ===== GRAFO: GhOrbPut
(fn GhOrbPut ()
  (bind _op (Variables|Z-Ghost|GetOrbPath))
  (bind _p (Utilities|Array|Get(acopy) _op (Math|Integer|Min(Integer) (Variables|Z-Ghost|GetCurF) (- (Utilities|Array|Length _op) 1))))
  (bind _sy (select (Variables|Z-Ghost|GetMirrorOn) -1.0 1.0))
  (bind _s (/ (Variables|Ghost|GetOrbSize) 100.0))
  (Transformation|SetWorldTransform (Variables|Default|GetOrb) (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation (Variables|Z-Ghost|GetAnchor) (Math|Vector|MakeVector (.x _p) (* _sy (.y _p)) (.z _p))) :Scale (Math|Vector|MakeVector _s _s _s))))

;; ===== GRAFO: GhStrokeTo
(fn GhStrokeTo ()
  (if (== (Variables|Z-Ghost|GetExtra) 2)
    (CallFunction|GhStrokeGrow self)))

;; ===== GRAFO: GhStrokeGrow
;; Agrega los tramos hasta el cuadro actual (pocos por salto). El componente esta en el ancla: instancias LOCALES.
(fn GhStrokeGrow ()
  (while (and (< (Variables|Z-Ghost|GetStrokeShown) (Utilities|Array|Length (Variables|Z-Ghost|GetStrokeF))) (<= (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetStrokeF) (Variables|Z-Ghost|GetStrokeShown)) (Variables|Z-Ghost|GetCurF)))
    (Components|InstancedStaticMesh|AddInstance (Variables|Default|GetStroke) (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetStrokeXf) (Variables|Z-Ghost|GetStrokeShown)) false)   ;;? InstanceTransform bWorldSpace
    (Variables|Z-Ghost|SetStrokeShown (+ (Variables|Z-Ghost|GetStrokeShown) 1))))

;; ===== GRAFO: GhAlpha
;; Opacidad = curva(Fade) * LoopK * GhostOpacity. Cada eco multiplica por su custom data (EchoAlpha por edad).
(fn GhAlpha ()
  (bind _self self)
  (bind _f (Variables|Z-Ghost|GetFade))
  (Variables|Z-Ghost|SetAlphaK (* (* (* _f (* _f (- 3.0 (* 2.0 _f)))) (Variables|Z-Ghost|GetLoopK)) (Variables|Ghost|GetGhostOpacity)))
  (bind _k (Variables|Z-Ghost|GetAlphaK))
  (CallFunction|GhOp _self (Variables|Default|GetOrb) _k)
  (CallFunction|GhOp _self (Variables|Default|GetStroke) _k)
  (CallFunction|GhOp _self (Variables|Default|GetPath) (* _k 0.5))
  (CallFunction|GhTextAlpha _self _k)
  (for _h (range 2)
    (CallFunction|GhAlphaHand _self _h)))

;; ===== GRAFO: GhAlphaHand
(fn GhAlphaHand (H)
  (bind _self self)
  (bind _left (== H 1))
  (bind _k (Variables|Z-Ghost|GetAlphaK))
  (CallFunction|GhOp _self (select _left (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)) _k)
  (CallFunction|GhOp _self (select _left (Variables|Default|GetHandL) (Variables|Default|GetHandR)) _k)
  (CallFunction|GhOp _self (select _left (Variables|Default|GetTrigL) (Variables|Default|GetTrigR)) _k)
  (CallFunction|GhOp _self (select _left (Variables|Default|GetPropL) (Variables|Default|GetPropR)) _k)
  (CallFunction|GhOp _self (select _left (Variables|Default|GetBeamL) (Variables|Default|GetBeamR)) (* _k 0.6)))

;; ===== GRAFO: GhOp
(fn GhOp (C V)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Opacity" V))

;; ===== GRAFO: GhText
;; La linea de texto en TextOffset (espacio del ancla), mirando al usuario (yaw del ancla + 180).
(fn GhText ()
  (bind _tc (Variables|Default|GetLabel))
  (bind _an (Variables|Z-Ghost|GetAnchor))
  (Transformation|SetWorldTransform _tc (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation _an (Variables|Ghost|GetTextOffset)) :Rotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (.rotation _an)) 180.0))))
  (Rendering|Components|TextRender|SetText _tc (Utilities|Text|ToText(String) (Variables|Z-Ghost|GetLineText))))

;; ===== GRAFO: GhTextAlpha
;; M_TextUnlit (Core/UI): emisivo = color de vertice -> el fundido es el brillo del TextRenderColor (a negro).
;; bShowText apaga el texto (la instruccion puede ir solo con la voz).
(fn GhTextAlpha (K)
  (bind _k (select (Variables|Ghost|GetShowText) K 0.0))
  (Rendering|Components|TextRender|SetTextRenderColor (Variables|Default|GetLabel) (Math|Conversions|ToColor(LinearColor) (* (Variables|Ghost|GetTextColor) _k))))

;; ===== GRAFO: GhAutoPlay
;; Gancho de PRUEBA (bAutoPlay): reproduce en bucle, sin espejo (para Simulate en el editor o un PIE sin director).
(fn GhAutoPlay ()
  (CallFunction|Play self (Variables|Z-Ghost|GetMirrorOn)))

;; ===== GRAFO: GhPreview
;; Vista previa del editor: la pose en PreviewTime, la cebolla (PreviewPoses poses repartidas), el recorrido en puntos,
;; el trazo hasta ese cuadro y la esfera. Ancla = el actor (las de cabeza: el origen del actor representa los ojos).
(fn GhPreview ()
  (bind _self self)
  (Variables|Z-Ghost|SetMirrorOn false)
  (Variables|Z-Ghost|SetInstN (+ 1 (Variables|Ghost|GetPreviewPoses)))
  (Variables|Z-Ghost|SetInstPreview true)
  (CallFunction|GhSetup _self)
  (CallFunction|GhAnchor _self (Variables|Z-Ghost|GetMirrorOn))
  (CallFunction|GhBake _self)
  (CallFunction|GhLayer _self)
  (Variables|Z-Ghost|SetCurF (Math|Float|Round (* (Math|Float|Clamp(Float) (Variables|Ghost|GetPreviewTime)) (Math|Conversions|ToFloat(Integer) (- (Variables|Z-Ghost|GetFrames) 1)))))
  (CallFunction|GhOrbAt _self)
  (CallFunction|GhStrokeTo _self)
  (Components|InstancedStaticMesh|AddInstances (Variables|Default|GetPath) (Variables|Z-Ghost|GetPathXf) false false)
  (CallFunction|GhPvHands _self)
  (Variables|Z-Ghost|SetFade 1.0)
  (Variables|Z-Ghost|SetLoopK 1.0)
  (CallFunction|GhAlpha _self)
  (CallFunction|GhText _self))

;; ===== GRAFO: GhPvHands
(fn GhPvHands ()
  (for _h (range 2)
    (CallFunction|GhPvHand self _h)))

;; ===== GRAFO: GhPvHand
(fn GhPvHand (H)
  (bind _self self)
  (if (> (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 0)
    (CallFunction|GhPose _self (Variables|Z-Ghost|GetCurF) H)
    (CallFunction|GhPlace _self H)
    (CallFunction|GhOnion _self H)))

;; ===== GRAFO: GhOnion
;; La mano (malla con esqueleto) no tiene cebolla: su recorrido lo muestran los puntos.
(fn GhOnion (H)
  (if (!= (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetKind) H) 1)
    (CallFunction|GhOnionAll self H)))

;; ===== GRAFO: GhOnionAll
(fn GhOnionAll (H)
  (for _k (range (Variables|Ghost|GetPreviewPoses))
    (CallFunction|GhOnionOne self H _k)))

;; ===== GRAFO: GhOnionOne
;; Pose K de la cebolla = cuadro repartido en toda la toma; instancia K+1 del cuerpo de la mano H.
(fn GhOnionOne (H K)
  (bind _self self)
  (bind _pp (Math|Integer|Max(Integer) 2 (Variables|Ghost|GetPreviewPoses)))
  (bind _f (Math|Float|Round (* (/ (Math|Conversions|ToFloat(Integer) K) (Math|Conversions|ToFloat(Integer) (- _pp 1))) (Math|Conversions|ToFloat(Integer) (- (Variables|Z-Ghost|GetFrames) 1)))))
  (CallFunction|GhPose _self _f H)
  (Components|InstancedStaticMesh|UpdateInstanceTransform (select (== H 1) (Variables|Default|GetBodyL) (Variables|Default|GetBodyR)) (+ K 1) (Math|Transform|ComposeTransforms (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetBodyRel) H) (Variables|Z-Ghost|GetPoseXf)) true true true))

;; ===== GRAFO: GhNoTake
;; Sin toma (o sin Take): un rotulo en el editor para ubicar el fantasma.
(fn GhNoTake ()
  (bind _tc (Variables|Default|GetLabel))
  (Rendering|Components|TextRender|SetTextMaterial _tc (Variables|GhostMesh|GetTextMat))
  (Rendering|Components|TextRender|SetWorldSize _tc 3.0)
  (Rendering|Components|TextRender|SetHorizontalAlignment _tc "EHTA_Center")
  (Rendering|Components|TextRender|SetTextRenderColor _tc (Math|Conversions|ToColor(LinearColor) (Variables|Ghost|GetTextColor)))
  (Transformation|SetWorldTransform _tc (Math|Transform|MakeTransform :Location (+ (Transformation|GetActorLocation) (Math|Vector|MakeVector 0.0 0.0 8.0)) :Rotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (Transformation|GetActorRotation)) 180.0))))
  (Utilities|IsValid (Variables|Ghost|GetTake)
    (:"Is Valid" (Rendering|Components|TextRender|SetText _tc (Utilities|Text|ToText(String) (Utilities|String|Append (Utilities|String|ToString(Name) (Class|BPGhostTakeSC|GetId (Variables|Ghost|GetTake))) "  (sin toma)"))))
    (:"Is Not Valid" (Rendering|Components|TextRender|SetText _tc (Utilities|Text|ToText(String) "FANTASMA (sin Take)")))))
