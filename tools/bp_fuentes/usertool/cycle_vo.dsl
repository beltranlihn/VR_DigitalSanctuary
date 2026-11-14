;; cycle_vo.dsl - BP_BreathStage_SC: la voz acompana el PRIMER ciclo (Beltran 2026-10-01, VO v2).
;;  (a) la cuenta "Three... two... one... inhale." (VO_12c, 4 tiempos): PacerPlay se dispara a InhaleCueAt - LeadIn del pacer
;;      despues de empezar la cuenta -> la pausa de entrada del pacer termina justo cuando Alma dice "inhale".
;;      Respaldo: si la etapa ya esta en fase 2 y el pacer no se lanzo, se lanza igual (nunca queda colgada).
;;  (b) primer ciclo: "Hold." / "Exhale." / "Hold." CueLead s antes de cada cambio de fase (4-3-4-3 o lo que tenga el pacer);
;;      un retencion de 0 s no dice nada. Ciclos 2+: silencio (VO_12b eliminada).
;; Solo en el flujo de contrato (bContract): el flujo viejo (bAutoStart, fase 1 -> PacerPlay) no se toca.
;; Variables nuevas en Default al escribir (y bContract se pasa a Default mientras se escribe) (despues se pasan a 0-Contrato / Z-Estado). Bools sin la b.
;;   0-Contrato: bCycleVO (true) · InhaleCueAt (3.48, segundo del clip en que empieza "inhale") · CueLead (0.3)
;;               HoldSound (VO_12f1) · ExhaleSound (VO_12f2)
;;   Z-Estado:   bPacerCued · CueStep (int)
;; Cirugia aparte en ContractStep: sacar PacerPlay de la rama 11->12 (su exec entra del PrintString "three, two, one") y
;; CountTime 3 -> 3.6 (la fase 2 llega despues de "inhale").

;; ===== GRAFO: StepCycleVO   (param DT float) -- en el Tick DESPUES de ContractStep
(fn StepCycleVO (DT)
  (bind _pac (Variables|Z-Estado|GetPacer))
  (if (== (Variables|Z-Estado|GetPhase) 11)
      (Variables|Default|SetPacerCued false)
      (Variables|Default|SetCueStep 0))
  (if (and (Variables|Default|GetContract) (and (not (Variables|Default|GetPacerCued)) (or (and (== (Variables|Z-Estado|GetPhase) 12) (>= (Variables|Z-Estado|GetContractTimer) (- (Variables|Default|GetInhaleCueAt) (Class|BPPacerSC|GetLeadIn _pac)))) (== (Variables|Z-Estado|GetPhase) 2))))
      (Variables|Default|SetPacerCued true)
      (Class|BPPacerSC|PacerPlay _pac)
      (Development|PrintString "BREATHSTAGE: pacer lanzado con la cuenta (inhale = fin de su pausa)"))
  (bind _t (Class|BPPacerSC|GetT _pac))
  (bind _h1 (Class|BPPacerSC|GetHold1Time _pac))
  (bind _b1 (Class|BPPacerSC|GetInhaleTime _pac))
  (bind _b2 (+ (Class|BPPacerSC|GetInhaleTime _pac) (Class|BPPacerSC|GetHold1Time _pac)))
  (bind _b3 (+ (+ (Class|BPPacerSC|GetInhaleTime _pac) (Class|BPPacerSC|GetHold1Time _pac)) (Class|BPPacerSC|GetExhaleTime _pac)))
  (bind _lead (Variables|Default|GetCueLead))
  (if (and (and (Variables|Default|GetContract) (Variables|Default|GetCycleVO)) (and (Class|BPPacerSC|GetRunning _pac) (== (Class|BPPacerSC|GetCycleIndex _pac) 0)))
      (if (and (== (Variables|Default|GetCueStep) 0) (>= _t (- _b1 _lead)))
          (Variables|Default|SetCueStep 1)
          (if (> _h1 0.05)
              (Audio|PlaySound2D (Variables|Default|GetHoldSound)))
          (elif (and (== (Variables|Default|GetCueStep) 1) (>= _t (- _b2 _lead)))
            (Variables|Default|SetCueStep 2)
            (Audio|PlaySound2D (Variables|Default|GetExhaleSound))
            (elif (and (== (Variables|Default|GetCueStep) 2) (>= _t (- _b3 _lead)))
              (Variables|Default|SetCueStep 3)
              (if (> (Class|BPPacerSC|GetHold2Time _pac) 0.05)
                  (Audio|PlaySound2D (Variables|Default|GetHoldSound))))))))
