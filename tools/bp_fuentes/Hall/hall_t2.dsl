;; hall_t2.dsl — T2 del director del Hall (grafos que quedaron VACÍOS en T1 + HallHudBirth reescrito en vacío).
;; Nada estructural en BP_HallDirector_SC (instancia colocada: gotcha 402). BP_HallFog_SC es un BP NUEVO: se arma
;; entero (variables, componentes, eventos) ANTES de colocarlo.
;; VERIFICAR con find_node_types antes de pegar: Class|BPSoulPickerSC|Awake/ForceChoose/GetChosen/GetWinner,
;; Class|BPProtoSoulSC|Disappear, Class|BPHallFogSC|FogOn/FogOff, Math|Interpolation|VInterpTo, Math|Vector|Normalize,
;; Transformation|GetForwardVector, Utilities|Array|FindItem, Math|Integer|%(Integer), Math|Conversions|ToFloat(Integer).

;; ===== GRAFO: HallPickStart  (vacío) — candidatas ALCANZABLES en arco frente al pecho, del centro hacia afuera:
;; índice 0 = centro (así el ForceChoose del picker, que elige Souls[0], elige la del centro = cortafuegos FW_Choose),
;; 1 izq, 2 der, 3 más izq, 4 más der. 19 cm entre ellas, el arco se aleja 3 cm por paso lateral.
(fn HallPickStart ()
  (bind _s (Actor|GetAllActorswithTag "soul_pick"))
  (Variables|Default|SetSouls _s)
  (for _i (range (Utilities|Array|Length _s))
    (bind _fi (Math|Conversions|ToFloat(Integer) _i))
    (bind _k (select (== (Math|Integer|%(Integer) _i 2) 1) (neg (* 0.5 (+ _fi 1.0))) (* 0.5 _fi)))
    (CallFunction|HallReach :Fwd (- (+ (Variables|Default|GetReachFwd) 6.0) (* 3.0 (Math|Float|Absolute(Float) _k))) :Down (Variables|Default|GetReachDown) :Side (* 19.0 _k))
    (Transformation|SetActorLocation :self (Utilities|Array|Get(acopy) _s _i) :NewLocation (Variables|Default|GetReachLoc) :bSweep false :bTeleport true))
  (Variables|Default|SetPickLive true)
  (Variables|Default|SetGate false)
  (Utilities|IsValid (Variables|Default|GetPicker)
    (:"Is Valid" (Class|BPSoulPickerSC|Awake (Variables|Default|GetPicker)))
    (:"Is Not Valid" (Variables|Default|SetPickLive false) (Variables|Default|SetGate true))))

;; ===== GRAFO: HallTickPick  (vacío) — la elección del picker (hover + gatillo) → ChosenSoul; FW_Choose → la del centro
(fn HallTickPick ()
  (if (Variables|Default|GetPickLive)
    (if (Class|BPSoulPickerSC|GetChosen (Variables|Default|GetPicker))
      (Variables|Default|SetChosenSoul (Utilities|Array|FindItem (Variables|Default|GetSouls) (Class|BPSoulPickerSC|GetWinner (Variables|Default|GetPicker))))
      (Variables|Default|SetPickLive false)
      (Variables|Default|SetGate true)
      (elif (> (Variables|Default|GetStepTime) (Variables|Default|GetFWChoose))
        (Class|BPSoulPickerSC|ForceChoose (Variables|Default|GetPicker))))))

;; ===== GRAFO: HallTickLead  (DT float; vacío) — contrato con la Obra: LeadActor ("tu alma va primero").
;; Regreso: pasos 0-2 (a oscuras) se COLOCA delante del pawn; desde el paso 3 (la caminata) vuela suave 2,5 m por delante,
;; rumbo a 1,8 m frente a StopCard. Salida: desde el paso 1, rumbo a 2,2 m delante de StopExit. Solo posición.
(fn HallTickLead (DT)
  (bind _m (Variables|Default|GetMode))
  (bind _st (Variables|Default|GetStep))
  (if (or (== _m 2) (and (== _m 3) (>= _st 1)))
    (bind _L (Variables|Default|GetLeadActor))
    (bind _P (Transformation|GetActorLocation :self (Variables|Default|GetPawn)))
    (bind _card (Variables|Default|GetStopCard))
    (bind _exit (Variables|Default|GetStopExit))
    (bind _G (select (== _m 2) (+ (Transformation|GetWorldLocation :self _card) (* (Transformation|GetForwardVector :self _card) 180.0)) (+ (Transformation|GetWorldLocation :self _exit) (* (Transformation|GetForwardVector :self _exit) 220.0))))
    (bind _dx (- (.x _G) (.x _P)))
    (bind _dy (- (.y _G) (.y _P)))
    (bind _len (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* _dx _dx) (* _dy _dy))) 1.0))
    (bind _a (Math|Float|Min(Float) 250.0 _len))
    (bind _T (Math|Vector|MakeVector (+ (.x _P) (* (/ _dx _len) _a)) (+ (.y _P) (* (/ _dy _len) _a)) (+ (.z _P) 110.0)))
    (Utilities|IsValid _L
      (:"Is Valid"
        (Transformation|SetActorLocation :self _L :NewLocation (select (and (== _m 2) (< _st 3)) _T (Math|Interpolation|VInterpTo (Transformation|GetActorLocation :self _L) _T DT 1.5)) :bSweep false :bTeleport true))
      (:"Is Not Valid"))))

;; ===== GRAFO: HallFogSet  (Lit bool; vacío) — la niebla del inicio/final (BP_HallFog_SC, azul noche casi negro)
(fn HallFogSet (Lit)
  (bind _f (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Hall/BP_HallFog_SC.BP_HallFog_SC_C"))
  (Utilities|IsValid _f
    (:"Is Valid"
      (if Lit
        (Class|BPHallFogSC|FogOn _f)
        (else (Class|BPHallFogSC|FogOff _f))))
    (:"Is Not Valid")))

;; ===== GRAFO: HallHudBirth  (REESCRIBIR EN VACÍO: borrar sus nodos salvo la entrada) — marca el momento y el alma
;; elegida se va (se encoge 0,6 s) mientras nace el HUD, que usa su propia alma (pedido de Narrativa).
(fn HallHudBirth ()
  (Variables|Default|SetHudBorn true)
  (Development|PrintString "HALL: nace el HUD (bHudBorn)" :bPrintToScreen false)
  (Utilities|IsValid (Variables|Default|GetPicker)
    (:"Is Valid"
      (Utilities|IsValid (Class|BPSoulPickerSC|GetWinner (Variables|Default|GetPicker))
        (:"Is Valid" (Class|BPProtoSoulSC|Disappear (Class|BPSoulPickerSC|GetWinner (Variables|Default|GetPicker))))
        (:"Is Not Valid")))
    (:"Is Not Valid")))

;; ===== BP_HallFog_SC (nuevo, Mechanics/Hall) — esfera r 6 m pegada a la cámara, M_HallFog_SC (duplicado de M_TourVeil_SC
;; con bDisableDepthTest = false: las manos y lo que esté a < 6 m se ven; el hall y todo lo lejano queda tapado).
;; Componente Sphere (/Engine/BasicShapes/Sphere, escala 12, sin sombra, sin colisión, TranslucencySortPriority -10).
;; Variables: Amount (float 1) · Target (float 1) · FadeIn (float 2, ed) · FadeOut (float 6, ed) · CTopFog / CHorFog
;; (LinearColor, ed: azul noche casi negro) · bStartOn (bool true, ed).
;; ===== GRAFO: BP_HallFog_SC EventGraph
(event EventBeginPlay
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetSphere) "CTop" (Variables|Default|GetCTopFog))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetSphere) "CHor" (Variables|Default|GetCHorFog))
  (Variables|Default|SetAmount (select (Variables|Default|GetStartOn) 1.0 0.0))
  (Variables|Default|SetTarget (Variables|Default|GetAmount)))

(event Custom|FogOn ()
  (Variables|Default|SetTarget 1.0))

(event Custom|FogOff ()
  (Variables|Default|SetTarget 0.0))

(event EventTick (DeltaSeconds)
  (bind _dt (Math|Float|Min(Float) DeltaSeconds 0.0333))
  (bind _up (> (Variables|Default|GetTarget) (Variables|Default|GetAmount)))
  (Variables|Default|SetAmount (Math|Interpolation|FInterptoConstant (Variables|Default|GetAmount) (Variables|Default|GetTarget) _dt (/ 1.0 (Math|Float|Max(Float) (select _up (Variables|Default|GetFadeIn) (Variables|Default|GetFadeOut)) 0.1))))
  (bind _e (Math|Float|FInterpEaseinOut 0.0 1.0 (Variables|Default|GetAmount) 2.0))
  (Transformation|SetWorldLocation (Variables|Default|GetSphere) (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0)))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetSphere) "Amount" _e)
  (Rendering|SetVisibility (Variables|Default|GetSphere) (> _e 0.001) false))
