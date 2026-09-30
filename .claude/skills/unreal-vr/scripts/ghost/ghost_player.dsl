;; ghost_player.dsl - BP_GhostPlayer_SC: el FANTASMA de las instrucciones demostrativas (2026-09-30, Drawing).
;; Plan: docs/PLAN-FANTASMAS-2026-09-30.md. Variables y parametros: ghost_spec.json (lo lee ghost_build_player.py).
;; Reglas del parser: if/for/switch/IsValid/cast AL FINAL de su lista; impuros con bind; CallFunction con self PRIMERO
;; (sin self, el primer literal cae en el pin self y se pierde); bool bX se lee GetX; switch int solo :0 :1 :2.
;; ";;?" = nombre de nodo a confirmar con find_node_types en el turno.
;;
;; Datos (DA BP_GhostTake_SC): Data float[] con Stride 28 por cuadro, en ESPACIO DEL ANCLA (cabeza al empezar + yaw
;; del pawn): 0-5 grip R (x y z pitch yaw roll) · 6-11 grip L · 12-14 aim R (pitch yaw roll) · 15-17 aim L ·
;; 18 gatillo R · 19 gatillo L · 20 grip R · 21 grip L · 22-27 cabeza.
;; Estados: 0 quieto · 1 aparece (Fade 0->1, ya se mueve) · 2 bucle · 3 pausa entre bucles · 4 se va (Fade 1->0).
;; Cada cambio de paso (StepHz) = un SALTO: la copia actual deja su pose a la copia de eco mas vieja y salta a la
;; pose nueva. Opacidad por edad: actual EchoAlpha[0], ecos EchoAlpha[edad+1].

;; ===== GRAFO: EventGraph
;; Nada visible en BeginPlay. AutoPlayId (solo PRUEBA, None por defecto) arranca un gesto despues de AutoPlayDelay.
(event EventBeginPlay
  (Rendering|SetActorHiddenInGame true)   ;;?
  (Actor|Tick|SetActorTickEnabled self false)
  (if (!= (Variables|Ghost|GetAutoPlayId) "None")
    (Utilities|Time|SetTimerbyFunctionName self "GhAutoPlay" (Variables|Ghost|GetAutoPlayDelay) false)))

(event EventTick (DeltaSeconds)
  (CallFunction|GhTick self (Math|Float|Min(Float) DeltaSeconds 0.0333)))

;; ===== GRAFO: Play
;; Play(DemoId, Col, Mirror): busca el DA por Id y arranca. Sin toma (o vacia) no hace nada y avisa en el log.
(fn Play (DemoId Col Mirror)
  (Variables|Z-Ghost|SetFound false)
  (Variables|Z-Ghost|SetWantCol Col)
  (Variables|Z-Ghost|SetMirrorOn Mirror)
  (CallFunction|GhFindLoop self DemoId)
  (if (not (Variables|Z-Ghost|GetFound))
    (Development|PrintString "GHOST: no hay toma con ese Id (o esta vacia)")))

;; ===== GRAFO: Stop
(fn Stop ()
  (bind _s (Variables|Z-Ghost|GetState))
  (if (and (> _s 0) (< _s 4))
    (Variables|Z-Ghost|SetState 4)
    (Variables|Z-Ghost|SetPlaying false)
    (CallFunction|GhSound self (Variables|Ghost|GetVanishSound))))

;; ===== GRAFO: Reanchor
(fn Reanchor ()
  (CallFunction|GhAnchor self))

;; ===== GRAFO: PreviewData
;; Para el grabador: reproduce una toma en memoria (misma ruta que un DA).
(fn PreviewData (D N UR UL BR BL Txt Col)
  (Variables|Z-Ghost|SetData D)
  (Variables|Z-Ghost|SetFrames N)
  (Variables|Z-Ghost|SetHz 30.0)
  (Variables|Z-Ghost|SetStride 28)
  (Variables|Z-Ghost|SetUseR UR)
  (Variables|Z-Ghost|SetUseL UL)
  (Variables|Z-Ghost|SetBeamR BR)
  (Variables|Z-Ghost|SetBeamL BL)
  (Variables|Z-Ghost|SetLineText Txt)
  (Variables|Z-Ghost|SetWantCol Col)
  (Variables|Z-Ghost|SetMirrorOn false)
  (CallFunction|GhStart self))

;; ===== GRAFO: GhFindLoop
(fn GhFindLoop (DemoId)
  (for _t (Variables|Ghost|GetTakes)
    (CallFunction|GhFindOne self _t DemoId)))

;; ===== GRAFO: GhFindOne
(fn GhFindOne (Tk DemoId)
  (Utilities|IsValid Tk
    (:"Is Valid"
      (if (and (not (Variables|Z-Ghost|GetFound)) (== (Class|BPGhostTakeSC|GetId Tk) DemoId))
        (Variables|Z-Ghost|SetFound true)
        (CallFunction|GhLoad self Tk)))
    (:"Is Not Valid")))

;; ===== GRAFO: GhLoad
(fn GhLoad (Tk)
  (Variables|Z-Ghost|SetData (Class|BPGhostTakeSC|GetData Tk))
  (Variables|Z-Ghost|SetFrames (Class|BPGhostTakeSC|GetFrames Tk))
  (Variables|Z-Ghost|SetHz (Math|Float|Max(Float) 1.0 (Class|BPGhostTakeSC|GetHz Tk)))
  (Variables|Z-Ghost|SetStride (Math|Integer|Max(Integer) 28 (Class|BPGhostTakeSC|GetStride Tk)))
  (Variables|Z-Ghost|SetUseR (Class|BPGhostTakeSC|GetUseRight Tk))
  (Variables|Z-Ghost|SetUseL (Class|BPGhostTakeSC|GetUseLeft Tk))
  (Variables|Z-Ghost|SetBeamR (Class|BPGhostTakeSC|GetBeamRight Tk))
  (Variables|Z-Ghost|SetBeamL (Class|BPGhostTakeSC|GetBeamLeft Tk))
  (Variables|Z-Ghost|SetLineText (Class|BPGhostTakeSC|GetText Tk))
  (CallFunction|GhStart self))

;; ===== GRAFO: GhStart
;; Orden anti-chispazo: pose y opacidad 0 ANTES de mostrar el actor (memoria "de un frame a otro y vuelve").
(fn GhStart ()
  (bind _self self)
  (if (< (Variables|Z-Ghost|GetFrames) 2)
    (Variables|Z-Ghost|SetFound false)
    (else
      (CallFunction|GhEnsure _self)
      (CallFunction|GhAnchor _self)
      (CallFunction|GhActive _self)
      (CallFunction|GhColor _self)
      (Variables|Z-Ghost|SetT 0.0)
      (Variables|Z-Ghost|SetGapT 0.0)
      (Variables|Z-Ghost|SetStepIdx -1)
      (Variables|Z-Ghost|SetLoopCount 0)
      (Variables|Z-Ghost|SetFade 0.0)
      (Variables|Z-Ghost|SetLoopK 1.0)
      (Variables|Z-Ghost|SetState 1)
      (Variables|Z-Ghost|SetPlaying true)
      (CallFunction|GhEchoReset _self)
      (CallFunction|GhJump _self 0)
      (CallFunction|GhText _self)
      (CallFunction|GhAlpha _self)
      (Rendering|SetActorHiddenInGame false)   ;;?
      (Actor|Tick|SetActorTickEnabled _self true)
      (CallFunction|GhSound _self (Variables|Ghost|GetAppearSound)))))

;; ===== GRAFO: GhActive
;; Que componente muestra que mano: con espejo (zurdo) la mano L muestra lo grabado por R reflejado, y viceversa.
(fn GhActive ()
  (bind _m (Variables|Z-Ghost|GetMirrorOn))
  (Variables|Z-Ghost|SetActR (select _m (Variables|Z-Ghost|GetUseL) (Variables|Z-Ghost|GetUseR)))
  (Variables|Z-Ghost|SetActL (select _m (Variables|Z-Ghost|GetUseR) (Variables|Z-Ghost|GetUseL)))
  (Variables|Z-Ghost|SetBeamActR (select _m (Variables|Z-Ghost|GetBeamL) (Variables|Z-Ghost|GetBeamR)))
  (Variables|Z-Ghost|SetBeamActL (select _m (Variables|Z-Ghost|GetBeamR) (Variables|Z-Ghost|GetBeamL))))

;; ===== GRAFO: GhSound
(fn GhSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid" (Audio|PlaySound2D Snd (Variables|Ghost|GetSfxVol)))
    (:"Is Not Valid")))

;; ===== GRAFO: GhAnchor
;; Ancla = posicion de la CABEZA + yaw del PAWN (decision de Narrativa 2026-09-30). Igual que el grabador.
(fn GhAnchor ()
  (bind _cam (Game|GetPlayerCameraManager 0))
  (bind _loc (Camera|GetCameraLocation _cam))
  (bind _pawn (Game|GetPlayerPawn 0))
  (bind _yaw (.yaw (Transformation|GetActorRotation _pawn)))
  (Variables|Z-Ghost|SetAnchor (Math|Transform|MakeTransform :Location _loc :Rotation (Math|Rotator|MakeRotator :Yaw _yaw))))

;; ===== GRAFO: GhEnsure
;; Componentes en runtime (patron de la paleta: InkEnsure/AppearEnsure). Una sola vez, en el primer Play.
(fn GhEnsure ()
  (bind _self self)
  (if (not (Variables|Z-Ghost|GetEnsured))
    (Variables|Z-Ghost|SetEnsured true)
    (CallFunction|GhMakeHand _self 0)
    (CallFunction|GhMakeHand _self 1)
    (CallFunction|GhMakeText _self)))

;; ===== GRAFO: GhMakeHand
;; Por mano: Curs[H] (cuerpo) · Trigs[H] (gatillo) · Beams[H] (haz) · 4 ecos Echoes[H*4+i] con Ages 99 (invisibles).
(fn GhMakeHand (H)
  (bind _self self)
  (bind _left (== H 1))
  (bind _body (select _left (Variables|GhostMesh|GetBodyMeshL) (Variables|GhostMesh|GetBodyMeshR)))
  (CallFunction|GhMakeMesh _self _body)
  (Utilities|Array|Add (Variables|Z-Ghost|GetCurs) (Variables|Z-Ghost|GetNewComp))
  (CallFunction|GhMakeMesh _self (select _left (Variables|GhostMesh|GetTrigMeshL) (Variables|GhostMesh|GetTrigMeshR)))
  (Utilities|Array|Add (Variables|Z-Ghost|GetTrigs) (Variables|Z-Ghost|GetNewComp))
  (CallFunction|GhMakeMesh _self (Variables|GhostMesh|GetBeamMesh))
  (Utilities|Array|Add (Variables|Z-Ghost|GetBeams) (Variables|Z-Ghost|GetNewComp))
  (Utilities|Array|Add (Variables|Z-Ghost|GetCurXf) (Math|Transform|MakeTransform))
  (Utilities|Array|Add (Variables|Z-Ghost|GetHasPrev) false)
  (for _i (range 4)
    (CallFunction|GhMakeMesh _self _body)
    (Utilities|Array|Add (Variables|Z-Ghost|GetEchoes) (Variables|Z-Ghost|GetNewComp))
    (Utilities|Array|Add (Variables|Z-Ghost|GetAges) 99)))

;; ===== GRAFO: GhMakeMesh
;; Game|AddComponentbyClass + cast PURO en un bind (asi anda AppearEnsure de la paleta): sin rama, no corta la lista.
(fn GhMakeMesh (M)
  (bind _c (Game|AddComponentbyClass :Class "/Script/Engine.StaticMeshComponent"))
  (bind _sm (Utilities|Casting|CastToStaticMeshComponent _c))
  (Components|StaticMesh|SetStaticMesh _sm M)
  (Rendering|Material|SetMaterial _sm 0 (Variables|GhostMesh|GetGhostMat))
  (Collision|SetCollisionEnabled _sm "NoCollision")
  (Rendering|SetCastShadow _sm false)
  (Rendering|SetVisibility _sm false)
  (Variables|Z-Ghost|SetNewComp _sm))

;; ===== GRAFO: GhMakeText
(fn GhMakeText ()
  (bind _c (Game|AddComponentbyClass :Class "/Script/Engine.TextRenderComponent"))
  (bind _tr (Utilities|Casting|CastToTextRenderComponent _c))
  (Rendering|Components|TextRender|SetTextMaterial _tr (Variables|GhostMesh|GetTextMat))
  (Rendering|Components|TextRender|SetWorldSize _tr (Variables|Ghost|GetTextSize))   ;;?
  (Rendering|Components|TextRender|SetHorizontalAlignment _tr "EHTA_Center")   ;;?
  (Rendering|Components|TextRender|SetVerticalAlignment _tr "EVRTA_TextCenter")   ;;?
  (Collision|SetCollisionEnabled _tr "NoCollision")
  (Rendering|SetVisibility _tr false)
  (Variables|Z-Ghost|SetTextC _tr))

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
;; LoopK: en el primer bucle vale 1 (la entrada la hace Fade); desde el segundo, sube en LoopFade (fundido del bucle).
;; En el estado 4 (se va) LoopK NO se toca: si Stop llega en la pausa, reponerlo a 1 haria reaparecer al fantasma
;; un cuadro antes de irse.
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
    (CallFunction|GhEchoReset _self)
    (CallFunction|GhJump _self 0)))

;; ===== GRAFO: GhEnd
(fn GhEnd ()
  (if (and (== (Variables|Z-Ghost|GetState) 4) (<= (Variables|Z-Ghost|GetFade) 0.0))
    (Variables|Z-Ghost|SetState 0)
    (Rendering|SetActorHiddenInGame true)   ;;?
    (Actor|Tick|SetActorTickEnabled self false)))

;; ===== GRAFO: GhJump
;; S = indice de paso. Cuadro = round(S / StepHz * Hz), con tope en el ultimo.
(fn GhJump (S)
  (bind _self self)
  (Variables|Z-Ghost|SetStepIdx S)
  (bind _f (Math|Integer|Min(Integer) (- (Variables|Z-Ghost|GetFrames) 1) (Math|Float|Round (* (/ (Math|Conversions|ToFloat(Integer) S) (Math|Float|Max(Float) 1.0 (Variables|Ghost|GetStepHz))) (Variables|Z-Ghost|GetHz)))))
  (CallFunction|GhEchoAge _self)
  (CallFunction|GhJumpHand _self 0 _f)
  (CallFunction|GhJumpHand _self 1 _f))

;; ===== GRAFO: GhJumpHand
(fn GhJumpHand (H F)
  (bind _self self)
  (if (select (== H 1) (Variables|Z-Ghost|GetActL) (Variables|Z-Ghost|GetActR))
    (CallFunction|GhEchoPush _self H)
    (CallFunction|GhPose _self F H)
    (CallFunction|GhPlace _self H)))

;; ===== GRAFO: GhPlace
;; Lleva la copia actual, su gatillo y su haz a la pose recien calculada (PoseXf/PoseAim/PoseTrig).
(fn GhPlace (H)
  (bind _self self)
  (bind _mx (Math|Transform|ComposeTransforms (select (== H 1) (Variables|GhostMesh|GetGripToMeshL) (Variables|GhostMesh|GetGripToMeshR)) (Variables|Z-Ghost|GetPoseXf)))
  (Transformation|SetWorldTransform (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetCurs) H) _mx)   ;;? K2_SetWorldTransform
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetCurXf) H _mx true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHasPrev) H true true)
  (CallFunction|GhTrigSet _self H (Variables|Z-Ghost|GetPoseTrig) _mx)
  (CallFunction|GhBeamSet _self H))

;; ===== GRAFO: GhPose
;; Pose del cuadro F para la mano H, en MUNDO. Con espejo lee la otra mano y refleja: y -> -y, yaw -> -yaw, roll -> -roll.
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
  (Variables|Z-Ghost|SetPoseAim (Math|Transform|TransformRotation _an _aim))   ;;?
  (Variables|Z-Ghost|SetPoseTrig (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) _d (+ _o (+ 18 _src))))))

;; ===== GRAFO: GhTrigSet
;; El gatillo gira en su bisagra (datos de BP_QuestCtrl_SC: pivote R, eje R; L = x del pivote negado, eje (ax,-ay,-az)).
(fn GhTrigSet (H V Mx)
  (bind _left (== H 1))
  (bind _pr (Variables|GhostMesh|GetHingePivotR))
  (bind _ar (Variables|GhostMesh|GetHingeAxisR))
  (bind _piv (select _left (Math|Vector|MakeVector (* (.x _pr) -1.0) (.y _pr) (.z _pr)) _pr))
  (bind _ax (select _left (Math|Vector|MakeVector (.x _ar) (* (.y _ar) -1.0) (* (.z _ar) -1.0)) _ar))
  (bind _rot (Math|Vector|RotatorfromAxisandAngle _ax (* (* (Variables|GhostMesh|GetPressSign) V) (Variables|GhostMesh|GetPressDegrees))))   ;;?
  (bind _tr (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetTrigs) H))
  (Transformation|SetWorldTransform _tr (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Location _piv :Rotation _rot) Mx))
  (Rendering|Material|SetScalarParameterValueonMaterials _tr "Pressed" V))

;; ===== GRAFO: GhBeamSet
;; Haz: cilindro del motor (alto 100 en Z, radio 50, centrado), acostado sobre el Aim con un pitch -90 previo.
(fn GhBeamSet (H)
  (bind _len (Variables|Ghost|GetBeamLength))
  (bind _rad (/ (Variables|Ghost|GetBeamRadius) 50.0))
  (bind _r (Variables|Z-Ghost|GetPoseAim))
  (bind _fwd (Math|Vector|GetForwardVector _r))   ;;?
  (bind _rb (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator :Pitch -90.0) _r))   ;;?
  (Transformation|SetWorldTransform (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetBeams) H) (Math|Transform|MakeTransform :Location (+ (.location (Variables|Z-Ghost|GetPoseXf)) (* _fwd (* _len 0.5))) :Rotation _rb :Scale (Math|Vector|MakeVector _rad _rad (/ _len 100.0)))))

;; ===== GRAFO: GhEchoAge
(fn GhEchoAge ()
  (for _i (range (Utilities|Array|Length (Variables|Z-Ghost|GetAges)))
    (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetAges) _i (Math|Integer|Min(Integer) 99 (+ (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetAges) _i) 1)) true)))

;; ===== GRAFO: GhEchoReset
(fn GhEchoReset ()
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHasPrev) 0 false true)
  (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetHasPrev) 1 false true)
  (for _i (range (Utilities|Array|Length (Variables|Z-Ghost|GetAges)))
    (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetAges) _i 99 true)))

;; ===== GRAFO: GhEchoPush
;; La copia de eco MAS VIEJA de la mano toma la pose que tenia la actual y pasa a edad 0.
(fn GhEchoPush (H)
  (bind _self self)
  (CallFunction|GhEchoFind _self H)
  (bind _i (Variables|Z-Ghost|GetOldI))
  (if (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetHasPrev) H)
    (Transformation|SetWorldTransform (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetEchoes) _i) (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetCurXf) H))
    (Utilities|Array|SetArrayElem (Variables|Z-Ghost|GetAges) _i 0 true)))

;; ===== GRAFO: GhEchoFind
(fn GhEchoFind (H)
  (Variables|Z-Ghost|SetOldI (* H 4))
  (Variables|Z-Ghost|SetOldAge -1)
  (for _k (range 4)
    (CallFunction|GhEchoOld self (+ (* H 4) _k))))

;; ===== GRAFO: GhEchoOld
(fn GhEchoOld (I)
  (bind _a (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetAges) I))
  (if (> _a (Variables|Z-Ghost|GetOldAge))
    (Variables|Z-Ghost|SetOldAge _a)
    (Variables|Z-Ghost|SetOldI I)))

;; ===== GRAFO: GhAlpha
;; Opacidad = curva(Fade) * LoopK * GhostOpacity; cada copia por su edad. Se escribe cada cuadro (Fade cambia suave).
(fn GhAlpha ()
  (bind _self self)
  (bind _f (Variables|Z-Ghost|GetFade))
  (bind _k (* (* (* _f (* _f (- 3.0 (* 2.0 _f)))) (Variables|Z-Ghost|GetLoopK)) (Variables|Ghost|GetGhostOpacity)))
  (CallFunction|GhAlphaHand _self 0 _k)
  (CallFunction|GhAlphaHand _self 1 _k)
  (CallFunction|GhTextAlpha _self _k))

;; ===== GRAFO: GhAlphaHand
(fn GhAlphaHand (H K)
  (bind _self self)
  (bind _k (select (select (== H 1) (Variables|Z-Ghost|GetActL) (Variables|Z-Ghost|GetActR)) K 0.0))
  (bind _a0 (* _k (Utilities|Array|Get(acopy) (Variables|Ghost|GetEchoAlpha) 0)))
  (CallFunction|GhSetOp _self (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetCurs) H) _a0)
  (CallFunction|GhSetOp _self (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetTrigs) H) _a0)
  (CallFunction|GhSetOp _self (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetBeams) H) (select (select (== H 1) (Variables|Z-Ghost|GetBeamActL) (Variables|Z-Ghost|GetBeamActR)) (* _a0 0.6) 0.0))
  (for _i (range 4)
    (CallFunction|GhEchoAlpha _self (+ (* H 4) _i) _k)))

;; ===== GRAFO: GhEchoAlpha
;; Edad a (0 = eco mas nuevo) -> EchoAlpha[a+1]; fuera del arreglo = 0. El indice va protegido (select evalua las 2 ramas).
(fn GhEchoAlpha (I K)
  (bind _ea (Variables|Ghost|GetEchoAlpha))
  (bind _n (Utilities|Array|Length _ea))
  (bind _a (+ (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetAges) I) 1))
  (CallFunction|GhSetOp self (Utilities|Array|Get(acopy) (Variables|Z-Ghost|GetEchoes) I) (select (< _a _n) (* K (Utilities|Array|Get(acopy) _ea (Math|Integer|Min(Integer) _a (- _n 1)))) 0.0)))

;; ===== GRAFO: GhSetOp
;; Opacidad por el componente (crea y reusa su MID: sin arreglos de MIDs ni el overload de MPC).
(fn GhSetOp (C V)
  (Rendering|Material|SetScalarParameterValueonMaterials C "Opacity" V)
  (Rendering|SetVisibility C (> V 0.002)))

;; ===== GRAFO: GhColor
;; El color de la etapa en TODAS las copias (parametro "Color" de M_Ghost_SC, vector).
(fn GhColor ()
  (bind _self self)
  (CallFunction|GhColorArr _self (Variables|Z-Ghost|GetCurs))
  (CallFunction|GhColorArr _self (Variables|Z-Ghost|GetTrigs))
  (CallFunction|GhColorArr _self (Variables|Z-Ghost|GetBeams))
  (CallFunction|GhColorArr _self (Variables|Z-Ghost|GetEchoes)))

;; ===== GRAFO: GhColorArr
(fn GhColorArr (A)
  (bind _v (Math|Conversions|ToVector(LinearColor) (Variables|Z-Ghost|GetWantCol)))
  (for _m A
    (Rendering|Material|SetVectorParameterValueonMaterials _m "Color" _v)))

;; ===== GRAFO: GhText
;; La linea de texto: bajo el fantasma, mirando al usuario (yaw del ancla + 180).
(fn GhText ()
  (bind _tc (Variables|Z-Ghost|GetTextC))
  (bind _an (Variables|Z-Ghost|GetAnchor))
  (Transformation|SetWorldTransform _tc (Math|Transform|MakeTransform :Location (Math|Transform|TransformLocation _an (Variables|Ghost|GetTextOffset)) :Rotation (Math|Rotator|MakeRotator :Yaw (+ (.yaw (.rotation _an)) 180.0))))
  (Rendering|Components|TextRender|SetText _tc (Utilities|Text|ToText(String) (Variables|Z-Ghost|GetLineText))))   ;;?

;; ===== GRAFO: GhTextAlpha
;; M_TextUnlit (Core/UI): emisivo = color de vertice -> el fundido es el brillo del TextRenderColor (a negro).
(fn GhTextAlpha (K)
  (bind _tc (Variables|Z-Ghost|GetTextC))
  (bind _k (select (Variables|Ghost|GetShowText) K 0.0))
  (Rendering|Components|TextRender|SetTextRenderColor _tc (Math|Conversions|ToColor(LinearColor) (* (Variables|Ghost|GetTextColor) _k)))   ;;? LinearColor -> Color
  (Rendering|SetVisibility _tc (> _k 0.002)))

;; ===== GRAFO: GhAutoPlay
;; Gancho de PRUEBA (AutoPlayId): reproduce en bucle con el color de prueba, sin espejo.
(fn GhAutoPlay ()
  (CallFunction|Play self (Variables|Ghost|GetAutoPlayId) (Variables|Ghost|GetTestColor) false))
