;; stage_contract.dsl - contrato de etapa en BP_BreathStage_SC (StageIntro / StageBegin / StageOutro + bStageDone).
;; 2026-09-30 noche, sesion Breath (plan: docs/PLAN-NOCHE-2026-09-30.md). Los tres stubs los creo Narrativa (vacios).
;; Fases nuevas, inertes para el switch viejo de StageTick (solo las mueve ContractStep, llamado despues de StageTick):
;;   9 test esperando · 10 intro (metaball + herramienta) · 11 exploracion libre · 12 "three, two, one" ·
;;   2-3 pacer (las de siempre) · 4 -> 13 terminado (bStageDone) · 14 salida del metaball · 6 fin.
;; (Variables|Z-Estado|GetBlob) (Variables|Z-Estado|GetRig) (Variables|Z-Estado|GetPacer) = los getters reales de las refs (recon); (Class|BPBreathBlobSC|GetEnvT (Variables|Z-Estado|GetBlob)) = el GetEnvT del METABALL tal como lo
;; usa StageTick; (Actor|Tick|SetActorTickEnabled true) = el SetActorTickEnabled de TourWake; (bind _tour (Actor|GetAllActorswithTag "TOUR")) = el GetAllActorsWithTag de TourCheck.
;; Variables nuevas en Default al escribir; bools sin la b.

;; ===== GRAFO: StageIntro
(fn StageIntro ()
  (Actor|Tick|SetActorTickEnabled true)
  (CallFunction|StageFind)
  (CallFunction|StageLife :Awake true)
  (Variables|Default|SetStageDone false)
  (Variables|Default|SetContract true)
  (Variables|Default|SetToolDone false)
  (Variables|Default|SetContractTimer 0.0)
  (Variables|Z-Estado|SetPhase 10)
  (Variables|Z-Estado|SetPhaseTimer 0.0)
  (Class|BPBreathBlobSC|BlobAppear (Variables|Z-Estado|GetBlob))
  (Audio|PlaySound2D (Variables|Default|GetBlobInSound))
  (Development|PrintString "BREATHSTAGE: StageIntro (el metaball nace; el mando se va a convertir en el sensor)"))

;; ===== GRAFO: StageBegin
(fn StageBegin ()
  (Class|BPBreathRigSC|SetRigActive (Variables|Z-Estado|GetRig) true)
  (Variables|Default|SetContractTimer 0.0)
  (Variables|Z-Estado|SetPhase 11)
  (Development|PrintString "BREATHSTAGE: StageBegin (exploracion libre)"))

;; ===== GRAFO: StageOutro
(fn StageOutro ()
  (Variables|Z-Estado|SetPhase 14)
  (Variables|Default|SetContractTimer 0.0)
  (Class|BPBreathRigSC|SetRigActive (Variables|Z-Estado|GetRig) false)
  (Class|BPBreathBlobSC|BlobDisappear (Variables|Z-Estado|GetBlob))
  (Audio|PlaySound2D (Variables|Default|GetBlobOutSound))
  (CallFunction|StageHush :Target (Variables|Z-Estado|GetPacer))
  (Development|PrintString "BREATHSTAGE: StageOutro (el metaball se va; el sensor queda en la mano)")
  (if (Class|BPPacerSC|GetRunning (Variables|Z-Estado|GetPacer))
      (Class|BPPacerSC|PacerStop (Variables|Z-Estado|GetPacer))))

;; ===== GRAFO: StageEnv
;; pedido de Narrativa: la obra la llama al encender la celda detras del velo (~9 s antes de StageIntro): solo la capa
;; de vida (polvo y rafagas). El valle y el aliento no dependen de la etapa.
(fn StageEnv ()
  (CallFunction|StageLife :Awake true)
  (Development|PrintString "BREATHSTAGE: StageEnv (vida: polvo y rafagas)"))

;; ===== GRAFO: StageTool
(fn StageTool ()
  (bind _tool (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC.BP_UserTool_SC_C"))
  (Utilities|IsValid _tool
    (:"Is Valid"
      (Class|BPUserToolSC|ToSensor _tool :Color (Variables|Default|GetSensorColor))
      (Development|PrintString "BREATHSTAGE: UserTool.ToSensor (azulado)"))
    (:"Is Not Valid"
      (Development|PrintString "BREATHSTAGE: no hay BP_UserTool_SC en el nivel (sin sensor visible)"))))

;; ===== GRAFO: ContractTest   (param DT float)
;; bContractTest: Intro a 1,5 s, Begin 8 s despues, Outro al bStageDone. Con un actor TOUR en el mundo (recorrido, obra)
;; se apaga solo (TestStage 99) y no pisa la fase. (elif anidado: cada elif va DENTRO del cuerpo anterior, con su else)
(fn ContractTest (DT)
  (Variables|Default|SetTestClock (+ (Variables|Default|GetTestClock) DT))
  (if (and (Variables|Default|GetContractTest) (== (Variables|Default|GetTestStage) 0))
      (bind _tour (Actor|GetAllActorswithTag "TOUR"))
      (Variables|Default|SetTestStage (select (> (Utilities|Array|Length _tour) 0) 99 1))
      (Variables|Z-Estado|SetPhase (select (== (Variables|Default|GetTestStage) 1) 9 (Variables|Z-Estado|GetPhase)))
      (elif (and (== (Variables|Default|GetTestStage) 1) (>= (Variables|Default|GetTestClock) 1.5))
        (Variables|Default|SetTestStage 2)
        (CallFunction|StageIntro)
        (else
          (if (and (== (Variables|Default|GetTestStage) 2) (>= (Variables|Default|GetTestClock) 9.5))
              (Variables|Default|SetTestStage 3)
              (CallFunction|StageBegin)
              (elif (and (== (Variables|Default|GetTestStage) 3) (Variables|Default|GetStageDone))
                (Variables|Default|SetTestStage 4)
                (CallFunction|StageOutro)))))))

;; ===== GRAFO: ContractStep   (param DT float) -- se llama en el Tick DESPUES de StageTick
(fn ContractStep (DT)
  (bind _dt (Math|Float|Min(Float) DT 0.0333))
  (CallFunction|ContractTest :DT _dt)
  (Variables|Default|SetContractTimer (+ (Variables|Default|GetContractTimer) _dt))
  (if (and (== (Variables|Z-Estado|GetPhase) 10) (and (not (Variables|Default|GetToolDone)) (>= (Variables|Default|GetContractTimer) (Variables|Default|GetToolDelay))))
      (Variables|Default|SetToolDone true)
      (CallFunction|StageTool)
      (elif (and (== (Variables|Z-Estado|GetPhase) 11) (>= (Variables|Default|GetContractTimer) (Variables|Default|GetExploreTime)))
        (Variables|Z-Estado|SetPhase 12)
        (Variables|Default|SetContractTimer 0.0)
        (Audio|PlaySound2D (Variables|Default|GetCountSound))
        (Development|PrintString "BREATHSTAGE: three, two, one")
        (else
          (if (and (== (Variables|Z-Estado|GetPhase) 12) (>= (Variables|Default|GetContractTimer) (Variables|Default|GetCountTime)))
              (Variables|Z-Estado|SetPhase 2)
              (Variables|Z-Estado|SetPhaseTimer 0.0)
              (Class|BPPacerSC|PacerPlay (Variables|Z-Estado|GetPacer))
              (Development|PrintString "BREATHSTAGE: arranca el pacer")
              (elif (and (== (Variables|Z-Estado|GetPhase) 4) (Variables|Default|GetContract))
                (Variables|Z-Estado|SetPhase 13)
                (Variables|Default|SetStageDone true)
                (Default|CallOnBreathStageDone)
                (Development|PrintString "BREATHSTAGE: bStageDone (terminaron los ciclos)")
                (else
                  (if (and (== (Variables|Z-Estado|GetPhase) 14) (<= (Class|BPBreathBlobSC|GetEnvT (Variables|Z-Estado|GetBlob)) 0.0))
                      (Variables|Z-Estado|SetPhase 6)
                      (Development|PrintString "BREATHSTAGE: salida terminada")))))))))
