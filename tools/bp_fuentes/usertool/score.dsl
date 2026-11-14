;; score.dsl - CycleScores en BP_BreathStage_SC (pedido de Narrativa para el cuadro de resultados, aprobado 2026-09-30).
;; Un valor por ciclo del pacer, 0..1 = max(0, correlacion de Pearson) entre el PULMON DEL PACER (P, -1 exhalado .. +1
;; inhalado, leido del parametro "Lung" que el pacer empuja a su MID) y la respiracion del usuario (S = la senal del rig
;; que va a MPC_Breath.Signed). Si On nunca paso de 0,5 en toda la etapa, el array queda VACIO.
;; Limite de ciclo: P vuelve a subir despues de tocar el fondo (-0,95) = empieza la inhalacion siguiente. El ultimo ciclo
;; se cierra cuando el pacer deja de correr. Solo muestrea en la fase 3 (pacer en marcha).
;; __MID__ = el MID del panel del pacer (Class|BPPacerSC|GetMID o el que exista), __INH__ = GetInhaletoCenter del pacer,
;; __S__ = la senal del rig (BreathFollow = lo que va al MPC), __ON__ = BreathOn del rig. Variables nuevas en Default.

;; ===== GRAFO: ScoreSample
;; P = la guia del pacer desde SU reloj (T dentro del ciclo): inhala -1 -> +1 · sostiene +1 · exhala +1 -> -1 · sostiene -1
;; (la misma forma que dibuja; lineal en vez de su suavizado, no cambia la correlacion de forma apreciable).
(fn ScoreSample ()
  (bind _pac (Variables|Z-Estado|GetPacer))
  (bind _t (Class|BPPacerSC|GetT _pac))
  (bind _ih (Math|Float|Max(Float) (Class|BPPacerSC|GetInhaleTime _pac) 0.01))
  (bind _h1 (Class|BPPacerSC|GetHold1Time _pac))
  (bind _ex (Math|Float|Max(Float) (Class|BPPacerSC|GetExhaleTime _pac) 0.01))
  (Variables|Default|SetScP1 (select (< _t _ih) (- (* 2.0 (/ _t _ih)) 1.0) (select (< _t (+ _ih _h1)) 1.0 (select (< _t (+ (+ _ih _h1) _ex)) (- 1.0 (* 2.0 (/ (- _t (+ _ih _h1)) _ex))) -1.0))))
  (Variables|Default|SetScS1 (Class|BPBreathRigSC|GetBreathFollow (Variables|Z-Estado|GetRig)))
  (Variables|Default|SetSawOn (or (Variables|Default|GetSawOn) (> (Class|BPBreathRigSC|GetBreathOn (Variables|Z-Estado|GetRig)) 0.5)))
  (bind _p (Variables|Default|GetScP1))
  (bind _s (Variables|Default|GetScS1))
  (Variables|Default|SetScN (+ (Variables|Default|GetScN) 1.0))
  (Variables|Default|SetScP (+ (Variables|Default|GetScP) _p))
  (Variables|Default|SetScS (+ (Variables|Default|GetScS) _s))
  (Variables|Default|SetScPP (+ (Variables|Default|GetScPP) (* _p _p)))
  (Variables|Default|SetScSS (+ (Variables|Default|GetScSS) (* _s _s)))
  (Variables|Default|SetScPS (+ (Variables|Default|GetScPS) (* _p _s)))
  (if (and (Variables|Default|GetScArmed) (> _p -0.9))
      (Variables|Default|SetScArmed false)
      (CallFunction|ScoreFinish)
      (CallFunction|ScoreReset)
      (elif (< _p -0.95)
        (Variables|Default|SetScArmed true))))

;; ===== GRAFO: ScoreFinish
;; cierra el ciclo acumulado si tiene al menos 30 muestras (quien llama reinicia las sumas con ScoreReset)
(fn ScoreFinish ()
  (bind _n (Variables|Default|GetScN))
  (bind _num (- (* _n (Variables|Default|GetScPS)) (* (Variables|Default|GetScP) (Variables|Default|GetScS))))
  (bind _den (Math|Float|Sqrt (Math|Float|Max(Float) (* (- (* _n (Variables|Default|GetScPP)) (* (Variables|Default|GetScP) (Variables|Default|GetScP))) (- (* _n (Variables|Default|GetScSS)) (* (Variables|Default|GetScS) (Variables|Default|GetScS)))) 0.000001)))
  (bind _r (Math|Float|Clamp(Float) (/ _num _den)))
  (if (> _n 30.0)
      (Utilities|Array|Add (Variables|Default|GetCycleScores) _r)
      (Development|PrintString (Utilities|String|Append "BREATHSTAGE: puntaje del ciclo " (Utilities|String|ToString(Float) _r)))))

;; ===== GRAFO: ScoreReset
(fn ScoreReset ()
  (Variables|Default|SetScN 0.0)
  (Variables|Default|SetScP 0.0)
  (Variables|Default|SetScS 0.0)
  (Variables|Default|SetScPP 0.0)
  (Variables|Default|SetScSS 0.0)
  (Variables|Default|SetScPS 0.0))

;; ===== GRAFO: ScoreClear -- al empezar la etapa (fase 10)
(fn ScoreClear ()
  (Utilities|Array|Clear (Variables|Default|GetCycleScores))
  (CallFunction|ScoreReset)
  (Variables|Default|SetSawOn false)
  (Variables|Default|SetScArmed false))

;; ===== GRAFO: ScoreStep   (param DT float) -- en el Tick, despues de ContractStep
(fn ScoreStep (DT)
  (bind _pac (Variables|Z-Estado|GetPacer))
  (bind _ph (Variables|Z-Estado|GetPhase))
  (if (and (== _ph 3) (Class|BPPacerSC|GetRunning _pac))
      (CallFunction|ScoreSample)
      (elif (> (Variables|Default|GetScN) 30.0)
        (CallFunction|ScoreFinish)
        (CallFunction|ScoreReset)
        (else
          (if (== _ph 10)
              (CallFunction|ScoreClear)
              (elif (and (== _ph 13) (not (Variables|Default|GetSawOn)))
                (Utilities|Array|Clear (Variables|Default|GetCycleScores))))))))
