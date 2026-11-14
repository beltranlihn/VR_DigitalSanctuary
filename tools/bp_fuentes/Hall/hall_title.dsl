;; hall_title.dsl — BP_HallTitle_SC (Mechanics/Hall): el título SOUL CHARGER / CENTER al costado derecho de la puerta Oeste.
;; Pedido de Beltrán 2026-09-30: aparece cuando se ilumina el Hall y se va al entrar, con el barrido líquido de los
;; títulos de transición (M_TourTitle_SC: Reveal 0→1 entra, Out 0→1 se disuelve).
;; NO toca al director: LEE su Mode/Step (visible con Mode == ShowMode y ShowFromStep ≤ Step < HideAtStep). Sin TestOnly.
;; DOS instancias (precisión de Beltrán vía Narrativa): HallTitle_West (ShowMode 1, pasos 5→9: HallIntro, se prende el
;; Hall → empezamos a caminar) y HallTitle_East (ShowMode 2, pasos 1→3: HallReturn, se prende el Hall y se abre la
;; puerta → caminamos hacia adentro). Cada una al costado DERECHO de su puerta, mirando a la parada frente a ella.
;; Componentes: DefaultSceneRoot (la rotación en yaw del ACTOR = hacia dónde mira) → Plane (/Engine/BasicShapes/Plane,
;; relativa (0, 90, 90) = se lee derecho mirando +X en el marco del actor, escala (1,6; 0,4; 1) = 160 × 40 cm,
;; MI_HallTitle_Center_SC). Variables (Default): ShowMode int 1 · ShowFromStep int 5 · HideAtStep int 9 · RevealTime 4,5 · OutTime 3
;; (editables) · Director (BP_HallDirector_SC) · Rev · Out (float).

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (Variables|Default|SetDirector (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC_C"))
  (Variables|Default|SetRev 0.0)
  (Variables|Default|SetOut 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetPlane) "Reveal" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetPlane) "Out" 0.0)
  (Rendering|SetVisibility (Variables|Default|GetPlane) false false))

(event EventTick (DeltaSeconds)
  (Utilities|IsValid (Variables|Default|GetDirector)
    (:"Is Valid"
      (bind _dt (Math|Float|Min(Float) DeltaSeconds 0.0333))
      (bind _d (Variables|Default|GetDirector))
      (bind _st (Class|BPHallDirectorSC|GetStep _d))
      (bind _want (and (== (Class|BPHallDirectorSC|GetMode _d) (Variables|Default|GetShowMode)) (and (>= _st (Variables|Default|GetShowFromStep)) (< _st (Variables|Default|GetHideAtStep)))))
      (Variables|Default|SetRev (select (and _want (<= (Variables|Default|GetOut) 0.0)) (Math|Interpolation|FInterptoConstant (Variables|Default|GetRev) 1.0 _dt (/ 1.0 (Math|Float|Max(Float) (Variables|Default|GetRevealTime) 0.1))) (Variables|Default|GetRev)))
      (Variables|Default|SetOut (select (and (not _want) (> (Variables|Default|GetRev) 0.0)) (Math|Interpolation|FInterptoConstant (Variables|Default|GetOut) 1.0 _dt (/ 1.0 (Math|Float|Max(Float) (Variables|Default|GetOutTime) 0.1))) (Variables|Default|GetOut)))
      (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetPlane) "Reveal" (Variables|Default|GetRev))
      (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetPlane) "Out" (Variables|Default|GetOut))
      (Rendering|SetVisibility (Variables|Default|GetPlane) (> (Variables|Default|GetRev) 0.0) false)
      (if (>= (Variables|Default|GetOut) 1.0)
        (Variables|Default|SetRev 0.0)
        (Variables|Default|SetOut 0.0)))
    (:"Is Not Valid")))
