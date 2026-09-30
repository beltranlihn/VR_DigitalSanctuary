;; BP_FluidMedium_SC — el MUNDO se activa con la ameba (2026-09-30, pedido directo de Beltrán: "cuando la actividad hace
;; que la ameba se mueva y se active, las partículas del mundo tengan más velocidad de movimiento también, para sentir que
;; todo el world se activa").
;; 1. FluidStep (REESCRITO = scripts/fluid_medium.dsl + esto): perilla nueva 0-EEG|ActiveBoost (CDO 0 = idéntico a antes).
;;    boost = 1 + ActiveBoost x a^2 (a = actividad = 1 - EEG suavizado; al cuadrado: en calma no toca nada, crece suave).
;;    Multiplica la CORRIENTE (EffCurrent: todas las motas y las medias se trasladan) y la velocidad de los REMOLINOS
;;    (EffFlowSpeed); las cáusticas corren a la mitad de ese factor. Todo por fases/derivas INTEGRADAS: cambiar la velocidad
;;    nunca salta una posición. Paso = min(DT, 1/30) (regla de la obra).
;;    Con los valores de Test_Fluid (CurrentSpeed 2,5, FlowSpeed 0,1, EEGFlow 1) y ActiveBoost 2: corriente 1,5 cm/s en calma ->
;;    ~10,4 cm/s activa (antes 3,5); remolinos x0,5 -> x5,4 (antes x1,8).
;; 2. BP_LovingCell_SC.StageCouple (REESCRITO): el acople con el fluido corre SIEMPRE que la célula vive (fases 0, 2, 3, 4; no escondida)
;;    y le pasa la MISMA medida de actividad que usa la ameba: EEG del fluido = SS(0,2; 0,9; S) (la actividad del fluido 1 - EEG es
;;    exactamente la de AgTarget). Apaga el falso propio del fluido (el tour lo prendía con otra fase: el agua y la ameba se
;;    activaban a destiempo).

;; ===== GRAFO: FluidStep
(fn FluidStep (DT Snap)
  (bind _dt (Math|Float|Min(Float) DT 0.0333333))
  (Variables|Z-Interno|SetClock (+ (Variables|Z-Interno|GetClock) _dt))
  (bind _tg (select (Variables|0-EEG|GetFakeEEG) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (/ (* 6.2831853 (Variables|Z-Interno|GetClock)) (Math|Float|Max(Float) (Variables|0-EEG|GetFakePeriod) 1.0))))) (Variables|0-EEG|GetEEG)))
  (Variables|Z-Interno|SetEEGS (select Snap _tg (+ (Variables|Z-Interno|GetEEGS) (* (- _tg (Variables|Z-Interno|GetEEGS)) (- 1.0 (Math|Float|Exp (/ (neg _dt) (Math|Float|Max(Float) (Variables|0-EEG|GetEEGSmoothing) 0.05))))))))
  (bind _c (Math|Float|Clamp(Float) (Variables|Z-Interno|GetEEGS) 0.0 1.0))
  (bind _a (- 1.0 _c))
  (bind _kf (Variables|0-EEG|GetEEGFlow))
  (bind _kc (Variables|0-EEG|GetEEGClarity))
  (bind _boost (+ 1.0 (* (Math|Float|Max(Float) (Variables|0-EEG|GetActiveBoost) 0.0) (* _a _a))))
  (Variables|Z-Interno|SetEffFlowSpeed (* (* (Variables|1-Movimiento|GetFlowSpeed) (+ 1.0 (* _kf (- (* 0.8 _a) (* 0.5 _c))))) _boost))
  (Variables|Z-Interno|SetEffTurb (* (Variables|1-Movimiento|GetTurbulence) (+ 1.0 (* _kf (- (* 0.6 _a) (* 0.7 _c))))))
  (Variables|Z-Interno|SetEffFlowAmp (* (Variables|1-Movimiento|GetFlowAmp) (+ 1.0 (* _kf (- (* 0.25 _a) (* 0.3 _c))))))
  (Variables|Z-Interno|SetEffCurrent (* (* (Variables|1-Movimiento|GetCurrentSpeed) (+ 1.0 (* _kf (- (* 0.4 _a) (* 0.4 _c))))) _boost))
  (Variables|Z-Interno|SetEffStreak (* (Variables|1-Movimiento|GetStreakTime) (+ 1.0 (* _kf (- (* 0.3 _a) (* 0.4 _c))))))
  (Variables|Z-Interno|SetEffAbsorb (* (Variables|2-Liquido|GetAbsorbDist) (+ 1.0 (* _kc (- (* 0.8 _c) (* 0.2 _a))))))
  (bind _t (Variables|Z-Interno|GetClock))
  (bind _yaw (Math|Trig|DegreesToRadians (+ (Variables|1-Movimiento|GetCurrentYaw) (/ (* (Variables|1-Movimiento|GetMeander) (+ (Math|Trig|Sin(Radians) (* _t 0.017)) (* 0.5 (Math|Trig|Sin(Radians) (+ (* _t 0.041) 1.0))))) 1.5))))
  (bind _pit (Math|Trig|DegreesToRadians (+ (Variables|1-Movimiento|GetCurrentPitch) (* (* 0.35 (Variables|1-Movimiento|GetMeander)) (Math|Trig|Sin(Radians) (+ (* _t 0.023) 2.0))))))
  (bind _cp (Math|Trig|Cos(Radians) _pit))
  (Variables|Z-Interno|SetDriftVel (* (Math|Vector|MakeVector (* _cp (Math|Trig|Cos(Radians) _yaw)) (* _cp (Math|Trig|Sin(Radians) _yaw)) (Math|Trig|Sin(Radians) _pit)) (Variables|Z-Interno|GetEffCurrent)))
  (Variables|Z-Interno|SetDrift (+ (Variables|Z-Interno|GetDrift) (* (Variables|Z-Interno|GetDriftVel) _dt)))
  (Variables|Z-Interno|SetFlowPhase (+ (Variables|Z-Interno|GetFlowPhase) (* _dt (Variables|Z-Interno|GetEffFlowSpeed))))
  (Variables|Z-Interno|SetCausticPhase (Math|Float|%(Float) (+ (Variables|Z-Interno|GetCausticPhase) (* _dt (* (Variables|5-Luz|GetCausticSpeed) (+ 1.0 (* 0.5 (- _boost 1.0)))))) 62.831853)))

;; ===== GRAFO: StageCouple
;; (BP_LovingCell_SC) El acople con el fluido corre SIEMPRE que la célula vive (no solo en la mecánica): el mundo se activa con ella.
(fn StageCouple ()
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (bind _u (Math|Float|Clamp(Float) (/ (- (Variables|Z-Interno|GetS) 0.2) 0.7) 0.0 1.0))
  (if (and (!= _ph 1) (!= _ph 5))
    (Utilities|IsValid (Variables|9-Etapa|GetFluid)
      (:"Is Valid"
        (Class|BPFluidMediumSC|SetFakeEEG :self (Variables|9-Etapa|GetFluid) :bFakeEEG false)
        (Class|BPFluidMediumSC|SetEEG :self (Variables|9-Etapa|GetFluid) :EEG (* (* _u _u) (- 3.0 (* 2.0 _u))))))))
