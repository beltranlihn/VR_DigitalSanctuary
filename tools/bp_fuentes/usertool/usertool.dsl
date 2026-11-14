;; usertool.dsl - los grafos de BP_UserTool_SC (el objeto que el usuario lleva en la mano dominante: mando -> sensor).
;; 2026-09-30 (noche), sesion Breath, aprobado por Narrativa. BP = DUPLICADO de BP_BioSensorArt_SC (Mesh 3D): trae Body,
;; Button, Waves, Trace (con sus tags AppearBody/Mover/Late/Trace) y Appear (BPC_AppearLuz_SC, FaceAxis (0,0,-1)).
;; LA RAIZ DEL ACTOR ES EL MARCO DEL SENSOR (la aparicion luz primero calcula en el marco del duenio): el actor se cuelga
;; del GRIP con SensorXf; el mando y la mano fantasma van como hijos con Compose(XfEnGrip, Invert(SensorXf)).
;; Variables TODAS en Default al escribir (gotchas 296/466); se categorizan despues. Bools sin la b (gotcha 475).
;; Un write por grafo; cada grafo NUEVO o VACIO. El multi-exec (if/switch/IsValid) va AL FINAL de cada lista.

;; ===== GRAFO: ToolPose
(fn ToolPose ()
  (bind _r (Variables|Default|GetRight))
  (bind _inv (Math|Transform|InvertTransform (select _r (Variables|Default|GetSensorXfR) (Variables|Default|GetSensorXfL))))
  (Variables|Default|SetMandoRest (Math|Transform|ComposeTransforms (select _r (Variables|Default|GetMandoXfR) (Variables|Default|GetMandoXfL)) _inv))
  (Transformation|SetRelativeTransform (Variables|Default|GetMandoBodyR) (Variables|Default|GetMandoRest))
  (Transformation|SetRelativeTransform (Variables|Default|GetMandoBodyL) (Variables|Default|GetMandoRest))
  (Transformation|SetRelativeTransform (Variables|Default|GetHandGhost) (Math|Transform|ComposeTransforms (Variables|Default|GetHandRelR) _inv)))

;; ===== GRAFO: PushColor   (param C LinearColor)
;; __PUSHCOLOR__ se completa con los parametros reales de M_SCLight_SC / M_BioSensorWaves_SC (recon)
(fn PushColor (C)
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetBody) "Color" C)
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetButton) "Color" C)
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetWaves) "Color" C))

;; ===== GRAFO: ToolHide
(fn ToolHide ()
  (Rendering|SetVisibility (Variables|Default|GetMandoBodyR) false true)
  (Rendering|SetVisibility (Variables|Default|GetMandoBodyL) false true)
  (Rendering|SetVisibility (Variables|Default|GetHandGhost) false false)
  (Class|BPCAppearLuzSC|Prepare (Variables|Default|GetAppear))
  (Variables|Default|SetMode 0)
  (Variables|Default|SetModeReq (select (Variables|Default|GetShowMandoOnBegin) 1 (Variables|Default|GetModeReq)))
  (Variables|Default|SetMorphT 1.0)
  (Variables|Default|SetColorT 1.0)
  (CallFunction|PushColor :C (Variables|Default|GetLightColor))
  (Development|PrintString "USERTOOL: listo, espera la mano del pawn"))

;; ===== GRAFO: ToolMount
;; la busqueda probada del rig (FindHand): componente del pawn por NOMBRE HandRight/HandLeft; su padre es el grip
(fn ToolMount ()
  (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SceneComponent")
    (if (Utilities|String|EqualExactly(String) (Utilities|GetObjectName _c) (select (Variables|Default|GetRight) "HandRight" "HandLeft"))
      (Variables|Default|SetHand _c)
      (Variables|Default|SetGrip (Transformation|GetAttachParent _c)))))

;; ===== GRAFO: ToolAttach
(fn ToolAttach ()
  (Utilities|IsValid (Variables|Default|GetGrip)
    (:"Is Valid"
      (Transformation|AttachActorToComponent self (Variables|Default|GetGrip) :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld")
      (Transformation|SetActorRelativeTransform :NewRelativeTransform (select (Variables|Default|GetRight) (Variables|Default|GetSensorXfR) (Variables|Default|GetSensorXfL)))
      (CallFunction|ToolPose)
      (Variables|Default|SetMounted true)
      (Development|PrintString "USERTOOL: montado en el grip de la mano dominante"))))

;; ===== GRAFO: ToolApply
;; aplica el pedido (ModeReq) una vez: 1 mando · 2 mando -> sensor · 3 el sensor se va. PrevMode guarda el modo viejo
;; ANTES de pisarlo (un bind se re-evaluaria con el nuevo).
(fn ToolApply ()
  (bind _mando (select (Variables|Default|GetRight) (Variables|Default|GetMandoBodyR) (Variables|Default|GetMandoBodyL)))
  (if (and (>= (Variables|Default|GetModeReq) 0) (!= (Variables|Default|GetModeReq) (Variables|Default|GetMode)))
      (Variables|Default|SetPrevMode (Variables|Default|GetMode))
      (Variables|Default|SetMode (Variables|Default|GetModeReq))
      (Variables|Default|SetModeReq -1)
      (CallFunction|ToolPose)
      (switch int (- (Variables|Default|GetMode) 1)
        (:0
          (Variables|Default|SetMorphT 0.0)
          (Transformation|SetRelativeTransform _mando (Math|Transform|MakeTransform (.location (Variables|Default|GetMandoRest)) (.rotation (Variables|Default|GetMandoRest)) (Math|Vector|MakeVector 0.001 0.001 0.001)))
          (Rendering|SetVisibility _mando true true)
          (Development|SetHiddeninGame (Variables|Default|GetHand) true false)
          (Audio|PlaySound2D (Variables|Default|GetMandoSound))
          (Development|PrintString "USERTOOL: mando en la mano"))
        (:1
          (Variables|Default|SetMorphT (select (== (Variables|Default|GetPrevMode) 1) 0.0 1.0))
          (Rendering|SetVisibility _mando (== (Variables|Default|GetPrevMode) 1) true)
          (Class|BPCAppearLuzSC|Appear (Variables|Default|GetAppear))
          (Development|SetHiddeninGame (Variables|Default|GetHand) true false)
          (Development|PrintString "USERTOOL: el mando se convierte en el sensor"))
        (:2
          (Variables|Default|SetMorphT 0.0)
          (Rendering|SetVisibility _mando false true)
          (Class|BPCAppearLuzSC|Vanish (Variables|Default|GetAppear))
          (Development|PrintString "USERTOOL: el sensor se va (Release)")))))

;; ===== GRAFO: ToolMorph   (param DT float)
;; MorphT (0..1) es el reloj de la transicion del modo actual:
;;   1 mando: crece en su lugar (escala 1-(1-t)^3, ease-out; nada aparece de golpe)
;;   2 mando -> sensor: se achica (1-t^2, ease-in) y viaja al centro del sensor (la raiz) mientras el sensor aparece
;;   3 Release: reloj de la salida del sensor (1,6 s); al terminar vuelve la mano del pawn
(fn ToolMorph (DT)
  (bind _mando (select (Variables|Default|GetRight) (Variables|Default|GetMandoBodyR) (Variables|Default|GetMandoBodyL)))
  (if (< (Variables|Default|GetMorphT) 1.0)
      (Variables|Default|SetMorphT (Math|Float|Min(Float) (+ (Variables|Default|GetMorphT) (/ DT (select (== (Variables|Default|GetMode) 3) 1.6 (Math|Float|Max(Float) (Variables|Default|GetMorphTime) 0.01)))) 1.0))
      (bind _t (Variables|Default|GetMorphT))
      (bind _one (== (Variables|Default|GetMode) 1))
      (bind _u (- 1.0 _t))
      (bind _l (select _one 1.0 (- 1.0 (* _t _t))))
      (bind _s (Math|Float|Max(Float) (select _one (- 1.0 (* (* _u _u) _u)) (- 1.0 (* _t _t))) 0.001))
      (bind _rest (Variables|Default|GetMandoRest))
      (Transformation|SetRelativeTransform _mando (Math|Transform|MakeTransform (Math|Vector|MakeVector (* (.x (.location _rest)) _l) (* (.y (.location _rest)) _l) (* (.z (.location _rest)) _l)) (.rotation _rest) (Math|Vector|MakeVector (* (.x (.scale _rest)) _s) (* (.y (.scale _rest)) _s) (* (.z (.scale _rest)) _s))))
      (if (>= (Variables|Default|GetMorphT) 1.0)
          (Rendering|SetVisibility _mando (== (Variables|Default|GetMode) 1) true)
          (Development|SetHiddeninGame (Variables|Default|GetHand) (!= (Variables|Default|GetMode) 3) false))))

;; ===== GRAFO: ToolAnim   (param DT float) -- el color de las luces va de ColorFrom a ColorTo en ColorTime (SetSensorColor)
(fn ToolAnim (DT)
  (if (< (Variables|Default|GetColorT) 1.0)
      (Variables|Default|SetColorT (Math|Float|Min(Float) (+ (Variables|Default|GetColorT) (/ DT (Math|Float|Max(Float) (Variables|Default|GetColorTime) 0.01))) 1.0))
      (bind _s (Variables|Default|GetColorT))
      (Variables|Default|SetLightColor (Math|Color|Lerp(LinearColor) (Variables|Default|GetColorFrom) (Variables|Default|GetColorTo) (* (* _s _s) (- 3.0 (* 2.0 _s)))))
      (CallFunction|PushColor :C (Variables|Default|GetLightColor))))

;; ===== GRAFO: ToolTick   (param DT float)
;; regla de la obra (Narrativa, 2026-09-30): toda animacion limita su paso a 1/30 s (un cuadro trabado no se come la entrada)
(fn ToolTick (DT)
  (bind _dt (Math|Float|Min(Float) DT 0.0333))
  (if (not (Variables|Default|GetMounted))
      (CallFunction|ToolMount)
      (CallFunction|ToolAttach)
    (else
      (CallFunction|ToolApply)
      (CallFunction|ToolMorph :DT _dt)
      (CallFunction|ToolAnim :DT _dt))))

;; ===== GRAFO: ShowMando   (param Right bool) -- API: el Hall, al tomar el mando
(fn ShowMando (Right)
  (Variables|Default|SetMounted (and (Variables|Default|GetMounted) (== Right (Variables|Default|GetRight))))
  (Variables|Default|SetRight Right)
  (Variables|Default|SetModeReq 1))

;; ===== GRAFO: ToSensor   (param Color LinearColor) -- API: Breath StageIntro (azulado)
(fn ToSensor (Color)
  (Variables|Default|SetLightColor Color)
  (Variables|Default|SetColorFrom Color)
  (Variables|Default|SetColorTo Color)
  (Variables|Default|SetColorT 1.0)
  (CallFunction|PushColor :C Color)
  (Variables|Default|SetModeReq 2))

;; ===== GRAFO: SetSensorColor   (param Color LinearColor) -- API: Heart StageIntro (rojizo), fundido de ColorTime
(fn SetSensorColor (Color)
  (Variables|Default|SetColorFrom (Variables|Default|GetLightColor))
  (Variables|Default|SetColorTo Color)
  (Variables|Default|SetColorT 0.0))

;; ===== GRAFO: Release -- API: Heart StageOutro (el sensor se va y vuelve la mano)
(fn Release ()
  (Variables|Default|SetModeReq 3))

;; ===== GRAFO: ConstructionScript
(fn ConstructionScript ()
  (CallFunction|ToolPose)
  (bind _r (Variables|Default|GetRight))
  (Rendering|SetVisibility (Variables|Default|GetMandoBodyR) _r true)
  (Rendering|SetVisibility (Variables|Default|GetMandoBodyL) (not _r) true)
  (Rendering|SetVisibility (Variables|Default|GetHandGhost) _r false)
  (CallFunction|PushColor :C (Variables|Default|GetLightColor)))

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (CallFunction|ToolHide))
(event EventTick (DeltaSeconds)
  (CallFunction|ToolTick :DT DeltaSeconds))
