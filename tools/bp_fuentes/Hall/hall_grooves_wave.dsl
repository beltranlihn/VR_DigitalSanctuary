;; hall_grooves_wave.dsl — BP_HallGrooves_SC (Mechanics/Hall). Pedido de Beltrán 2026-09-30: las líneas de luz del interior
;; se encienden como una onda (gota) al ENTRAR y se apagan en reversa al SALIR, en la entrada y en el regreso.
;; NO toca al director: lee Mode/Step y escribe MPC_Hall_SC.GrooveFront = Front × FrontMax (el shader HallGrooveRevealPS
;; enciende lo que el frente ya pasó, con un pulso en el borde). Front avanza LINEAL (velocidad de propagación constante).
;; Ventanas (perillas): HallIntro → apagado hasta EnterStepIntro (9, caminamos hacia adentro), encendido hasta
;; LeaveStepIntro (27, se abre la puerta de salida) · HallReturn → apagado hasta EnterStepReturn (3) y queda encendido ·
;; HallExit → se apaga desde LeaveStepExit (1). En el paso 0 de HallIntro/HallReturn (a oscuras) se pone en 0 de golpe.
;; Mode 0: conserva. Arranca en 1 (encendido: lo mismo que se ve en el editor y en las pruebas de otros en Test_Hall).
;; Variables: Director (BP_HallDirector_SC) · Front (float, 1) · editables: EnterStepIntro 9 · LeaveStepIntro 27 ·
;; EnterStepReturn 3 · LeaveStepExit 1 · InTime 6 · OutTime 4 · FrontMax 2000 (cm; el óculo está a ~1805).

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (Variables|Default|SetDirector (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC_C")))

(event EventTick (DeltaSeconds)
  (Utilities|IsValid (Variables|Default|GetDirector)
    (:"Is Valid"
      (bind _dt (Math|Float|Min(Float) DeltaSeconds 0.0333))
      (bind _d (Variables|Default|GetDirector))
      (bind _m (Class|BPHallDirectorSC|GetMode _d))
      (bind _st (Class|BPHallDirectorSC|GetStep _d))
      (bind _f (Variables|Default|GetFront))
      (bind _tgt (select (== _m 1) (select (and (>= _st (Variables|Default|GetEnterStepIntro)) (< _st (Variables|Default|GetLeaveStepIntro))) 1.0 0.0) (select (== _m 2) (select (>= _st (Variables|Default|GetEnterStepReturn)) 1.0 0.0) (select (== _m 3) (select (>= _st (Variables|Default|GetLeaveStepExit)) 0.0 1.0) _f))))
      (bind _snap (and (or (== _m 1) (== _m 2)) (== _st 0)))
      (Variables|Default|SetFront (select _snap 0.0 (Math|Interpolation|FInterptoConstant _f _tgt _dt (/ 1.0 (Math|Float|Max(Float) (select (> _tgt _f) (Variables|Default|GetInTime) (Variables|Default|GetOutTime)) 0.1)))))
      (Rendering|Material|SetScalarParameterValue :Collection "/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC" :ParameterName "GrooveFront" :ParameterValue (* (Variables|Default|GetFront) (Variables|Default|GetFrontMax))))
    (:"Is Not Valid")))
