;; hall_ambience.dsl — BP_HallAmbience_SC (Mechanics/Hall): el ambiente del Hall que depende del paso del director, SIN tocarlo.
;; Lee Mode/Step y escribe dos perillas de MPC_Hall_SC:
;;  · GrooveFront = Front × FrontMax — la ONDA de las líneas de luz (shader HallGrooveRevealPS): se encienden al ENTRAR
;;    (centro → piso → muros → óculo) y se apagan en reversa al SALIR. Front avanza lineal (propagación constante).
;;  · DustLight = ease(Dust) — las MOTAS del trayecto (NS_HallDust_SC en 3 volúmenes a lo largo de StopStart → StopDoor):
;;    M_HallDust_SC usa max(HallLight, DustLight), así se ven a oscuras mientras avanzamos (paralaje = sensación de avance).
;; Ventanas: HallIntro → motas encendidas en los pasos 0..5 (el viaje), líneas apagadas hasta EnterStepIntro (9) y encendidas
;; hasta LeaveStepIntro (27) · HallReturn → líneas desde EnterStepReturn (3), motas apagadas · HallExit → líneas se apagan
;; desde LeaveStepExit (1), motas desde DustExitStep (2, la niebla vuelve). Paso 0 de HallIntro/HallReturn (a oscuras): se
;; pone todo en su estado de arranque de golpe. Mode 0: conserva. Arranca con Front 1 y Dust 0 (= lo que se ve en el editor).
;; Variables: Director (BP_HallDirector_SC) · Front (1) · Dust (0) · editables: EnterStepIntro 9 · LeaveStepIntro 27 ·
;; EnterStepReturn 3 · LeaveStepExit 1 · DustLastStep 5 · DustExitStep 2 · InTime 6 · OutTime 4 · DustIn 2 · DustOut 3 ·
;; FrontMax 2000 (cm; el óculo está a ~1805).

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
      (bind _du (Variables|Default|GetDust))
      (bind _tgt (select (== _m 1) (select (and (>= _st (Variables|Default|GetEnterStepIntro)) (< _st (Variables|Default|GetLeaveStepIntro))) 1.0 0.0) (select (== _m 2) (select (>= _st (Variables|Default|GetEnterStepReturn)) 1.0 0.0) (select (== _m 3) (select (>= _st (Variables|Default|GetLeaveStepExit)) 0.0 1.0) _f))))
      (bind _dtg (select (== _m 1) (select (<= _st (Variables|Default|GetDustLastStep)) 1.0 0.0) (select (== _m 2) 0.0 (select (== _m 3) (select (>= _st (Variables|Default|GetDustExitStep)) 1.0 0.0) _du))))
      (bind _snap (and (or (== _m 1) (== _m 2)) (== _st 0)))
      (Variables|Default|SetFront (select _snap 0.0 (Math|Interpolation|FInterptoConstant _f _tgt _dt (/ 1.0 (Math|Float|Max(Float) (select (> _tgt _f) (Variables|Default|GetInTime) (Variables|Default|GetOutTime)) 0.1)))))
      (Variables|Default|SetDust (select _snap _dtg (Math|Interpolation|FInterptoConstant _du _dtg _dt (/ 1.0 (Math|Float|Max(Float) (select (> _dtg _du) (Variables|Default|GetDustIn) (Variables|Default|GetDustOut)) 0.1)))))
      (Rendering|Material|SetScalarParameterValue :Collection "/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC" :ParameterName "GrooveFront" :ParameterValue (* (Variables|Default|GetFront) (Variables|Default|GetFrontMax)))
      (Rendering|Material|SetScalarParameterValue :Collection "/Game/SoulCharger/Mechanics/Hall/MPC_Hall_SC.MPC_Hall_SC" :ParameterName "DustLight" :ParameterValue (Math|Float|FInterpEaseinOut 0.0 1.0 (Variables|Default|GetDust) 2.0)))
    (:"Is Not Valid")))
