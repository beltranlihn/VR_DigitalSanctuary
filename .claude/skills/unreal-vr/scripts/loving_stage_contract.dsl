;; BP_LovingCell_SC — CONTRATO DE ETAPA + actividad más intensa (2026-09-30, noche; pedido de Beltrán en su
;; audio, dirigido por Narrativa: docs/PLAN-NOCHE-2026-09-30.md).
;;
;; Contrato (lo llama el director del nivel final BP_Obra_SC):
;;   TourWake()   al activar la celda: la célula se ESCONDE (escala 0,001 + oculta) y espera. Manos del fluido apagadas.
;;   StageIntro() entra: nace contraida y crece en IntroTime (3 s, ease-out-back suave + sube 10 cm) con SND_MindAppear.
;;   StageBegin() arranca la mecánica: señal de actividad desde "activa" (FakeStart = Clock), el fluido sigue el
;;                MISMO estado (EEG del fluido = S de la célula, sin su falso propio) y las manos revuelven las motas.
;;   bStageDone   true a los StageDuration (80 s) desde StageBegin.
;;   StageOutro() se va en OutroTime (3 s): anticipacion (se hincha 5 % y se contrae), se funde a 0 y sube 15 cm, con SND_MindVanish.
;;   TourSleep()  escondida, manos apagadas.
;; bContractTest (9-Etapa): en el test hace TourWake -> (1,5 s) Intro -> (IntroTime + TestGap) Begin -> (bStageDone) Outro.
;; Sin contrato (StagePhase 0) la célula se ve y vive igual que antes: nada de esto toca el actor.
;;
;; Actividad (Beltrán: "que se note mucho más: alta = se mueve, súper viva; baja = se contrae y se pone suave"):
;;   AgTarget = Agitation + ActivityDrive x (1 - SS(0,2; 0,9; S)). Reemplaza a Agitation en TODOS sus lectores
;;   (Simulate, LifeStep, CalmStep, GroupTarget: cirugía de getters). ActivityDrive 0 (CDO) = idéntico a antes.
;;   Con 1: a S = 0 Tempo x1,4, amplitud x1,35, ruido del objetivo x2,3, ameba +40 % (tope 0,85), curl +40 %,
;;   bolas que ruedan +50 %, respiración +40 %. La calma más quieta: LifeStep Tempo lerp(1,4 -> 0,45) (antes 0,7) y
;;   AmpS lerp(1,5 -> 0,35) (antes 0,55): cirugía de dos literales.
;;
;; Grafos NUEVOS: StageStep, StageVisual, StageCouple, FluidHands, TourWake, TourSleep. Los stubs de Narrativa
;; (StageIntro/StageBegin/StageOutro) se llenan con write_graph_dsl (grafos vacíos). REESCRITOS: Simulate, PushAll.
;; <DONE> = el setter de bStageDone (lo crea Narrativa; se resuelve el type_id en el turno).

;; Reglas de la obra (Narrativa, 2026-09-30): ninguna animacion arranca en BeginPlay ni en el cuadro de un encendido
;; (las entradas las dispara el director por evento); todo paso limitado a 1/30 s (Simulate: DT = min(DT, 1/30),
;; antes 0,05; lo reciben la vida y StageStep): un cuadro trabado no se come la entrada. La espera de prueba
;; (TestGap, 1,5 s antes de StageIntro) solo existe detras de bContractTest.

;; ===== GRAFO: FluidHands
(fn FluidHands (On)
  (Utilities|IsValid (Variables|9-Etapa|GetFluid)
    (:"Is Valid" (Class|BPFluidMediumSC|SetHandStir :self (Variables|9-Etapa|GetFluid) :bHandStir On))))

;; ===== GRAFO: TourWake
(fn TourWake ()
  (Variables|Z-Interno|SetStagePhase 1)
  (Variables|Z-Interno|SetStageT 0.0)
  (<DONE> false)
  (CallFunction|FluidHands :On false))

;; ===== GRAFO: TourSleep
(fn TourSleep ()
  (Variables|Z-Interno|SetStagePhase 5)
  (CallFunction|FluidHands :On false))

;; ===== GRAFO: StageIntro
(fn StageIntro ()
  (Variables|Z-Interno|SetStagePhase 2)
  (Variables|Z-Interno|SetStageT 0.0)
  (<DONE> false)
  (Audio|PlaySound2D :Sound (Variables|9-Etapa|GetSndIntro) :VolumeMultiplier (Variables|9-Etapa|GetSndVolume)))

;; ===== GRAFO: StageBegin
(fn StageBegin ()
  (Variables|Z-Interno|SetStagePhase 3)
  (Variables|Z-Interno|SetStageT 0.0)
  (<DONE> false)
  (Variables|Z-Interno|SetFakeStart (Variables|Z-Interno|GetClock))
  (Variables|1-Estado|SetFakeSignal true)
  (Utilities|IsValid (Variables|9-Etapa|GetFluid)
    (:"Is Valid"
      (Class|BPFluidMediumSC|SetFakeEEG :self (Variables|9-Etapa|GetFluid) :bFakeEEG false)
      (Class|BPFluidMediumSC|SetHandStir :self (Variables|9-Etapa|GetFluid) :bHandStir true))))

;; ===== GRAFO: StageOutro
(fn StageOutro ()
  (Variables|Z-Interno|SetStagePhase 4)
  (Variables|Z-Interno|SetStageT 0.0)
  (Audio|PlaySound2D :Sound (Variables|9-Etapa|GetSndOutro) :VolumeMultiplier (Variables|9-Etapa|GetSndVolume)))

;; ===== GRAFO: StageVisual
;; Escala / altura / oculta segun la fase. Fase 0 (sin contrato): no toca el actor. Curvas (estandar "estudio grande"):
;;   entrada (IntroTime 3 s): escala ease-out-back suave (sobrepasa 3,5 % y se asienta, velocidad 0 al final) y sube
;;     10 cm desde abajo con smootherstep; nace CONTRAIDA (Simulate fuerza S -> 1 en la fase 2) y se despliega con StageBegin.
;;   salida (OutroTime 3 s): 0-30 % anticipacion (se hincha 5 % mientras se contrae), 30-100 % se funde a 0 con
;;     smootherstep (sin frenazo) y sube 15 cm. Sonido sincronizado (SND_MindVanish: inhalacion 0-0,9 s).
(fn StageVisual ()
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (bind _t (Variables|Z-Interno|GetStageT))
  (bind _ki (Math|Float|Clamp(Float) (/ _t (Math|Float|Max(Float) (Variables|9-Etapa|GetIntroTime) 0.1)) 0.0 1.0))
  (bind _u (- _ki 1.0))
  (bind _ob (+ 1.0 (+ (* 1.8 (* (* _u _u) _u)) (* 0.8 (* _u _u)))))
  (bind _si (* (* (* _ki _ki) _ki) (+ (* _ki (- (* _ki 6.0) 15.0)) 10.0)))
  (bind _ko (Math|Float|Clamp(Float) (/ _t (Math|Float|Max(Float) (Variables|9-Etapa|GetOutroTime) 0.1)) 0.0 1.0))
  (bind _ka (Math|Float|Clamp(Float) (/ _ko 0.3) 0.0 1.0))
  (bind _sa (* (* _ka _ka) (- 3.0 (* 2.0 _ka))))
  (bind _kb (Math|Float|Clamp(Float) (/ (- _ko 0.3) 0.7) 0.0 1.0))
  (bind _sb (* (* (* _kb _kb) _kb) (+ (* _kb (- (* _kb 6.0) 15.0)) 10.0)))
  (bind _so (* (+ 1.0 (* 0.05 _sa)) (- 1.0 _sb)))
  (bind _hid (or (== _ph 1) (== _ph 5)))
  (bind _s (select _hid 0.001 (select (== _ph 2) (Math|Float|Max(Float) _ob 0.001) (select (== _ph 4) (Math|Float|Max(Float) _so 0.001) 1.0))))
  (bind _dz (select (== _ph 2) (* -10.0 (- 1.0 _si)) (select (== _ph 4) (* 15.0 _sb) 0.0)))
  (if (!= _ph 0)
    (Transformation|SetActorScale3D :NewScale3D (* (Variables|Z-Interno|GetBaseScale) _s))
    (Transformation|SetActorLocation :NewLocation (+ (Variables|Z-Interno|GetBaseLoc) (Math|Vector|MakeVector 0.0 0.0 _dz)))
    (Rendering|SetActorHiddenInGame :bNewHidden _hid)))

;; ===== GRAFO: StageCouple
;; Durante la mecánica y la salida, el fluido lee el MISMO estado que la célula (convención común: 0 activo, 1 calma).
(fn StageCouple ()
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (if (or (== _ph 3) (== _ph 4))
    (Utilities|IsValid (Variables|9-Etapa|GetFluid)
      (:"Is Valid" (Class|BPFluidMediumSC|SetEEG :self (Variables|9-Etapa|GetFluid) :EEG (Variables|Z-Interno|GetS))))))

;; ===== GRAFO: StageStep
;; Corre al principio de Simulate (cada Tick). Nada en Snap (Construction Script / BeginPlay).
(fn StageStep (DT Snap)
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (bind _t (Variables|Z-Interno|GetStageT))
  (bind _ct (Variables|9-Etapa|GetContractTest))
  (if (not Snap)
    (Variables|Z-Interno|SetBaseScale (select (Variables|Z-Interno|GetStageInit) (Variables|Z-Interno|GetBaseScale) (Transformation|GetActorScale3D)))
    (Variables|Z-Interno|SetBaseLoc (select (Variables|Z-Interno|GetStageInit) (Variables|Z-Interno|GetBaseLoc) (Transformation|GetActorLocation)))
    (Variables|Z-Interno|SetStageInit true)
    (Variables|Z-Interno|SetStageT (+ (Variables|Z-Interno|GetStageT) DT))
    (Variables|Z-Interno|SetTestT (select _ct (+ (Variables|Z-Interno|GetTestT) DT) 0.0))
    (CallFunction|StageVisual)
    (CallFunction|StageCouple)
    (if (and _ct (== _ph 0))
      (CallFunction|TourWake)
      (elif (and _ct (and (== _ph 1) (>= (Variables|Z-Interno|GetTestT) 1.5)))
        (CallFunction|StageIntro)
        (elif (and _ct (and (== _ph 2) (>= _t (+ (Variables|9-Etapa|GetIntroTime) (Variables|9-Etapa|GetTestGap)))))
          (CallFunction|StageBegin)
          (elif (and _ct (and (== _ph 3) (<DONEGET>)))
            (CallFunction|StageOutro)
            (elif (and (== _ph 3) (>= _t (Variables|9-Etapa|GetStageDuration)))
              (<DONE> true)
              (elif (and (== _ph 4) (>= _t (Variables|9-Etapa|GetOutroTime)))
                (Variables|Z-Interno|SetStagePhase 5)
                (CallFunction|FluidHands :On false)))))))))

;; ===== GRAFO: Simulate
;; = la versión de loving_tick_perf.dsl + StageStep al principio, sin simular mientras está escondida (fases 1 y 5),
;; FakeStart (la señal arranca "activa" en StageBegin), la salida fuerza la calma (S -> 1 rápido) y AgTarget.
(fn Simulate (DT Snap)
  (bind _dt (Math|Float|Min(Float) DT 0.0333333))
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _r (select (< (Variables|9-Rendimiento|GetSimDivider) 1) 1 (Variables|9-Rendimiento|GetSimDivider)))
  (bind _out (or (== (Variables|Z-Interno|GetStagePhase) 2) (== (Variables|Z-Interno|GetStagePhase) 4)))
  (bind _fake (select (Variables|1-Estado|GetFakeSignal) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (/ (* 6.2831853 (- (Variables|Z-Interno|GetClock) (Variables|Z-Interno|GetFakeStart))) (Math|Float|Max(Float) (Variables|1-Estado|GetFakePeriod) 1.0))))) (Variables|1-Estado|GetGlobalState)))
  (bind _tgt (select _out 1.0 _fake))
  (bind _u (Math|Float|Clamp(Float) (/ (- (Variables|Z-Interno|GetS) 0.2) 0.7) 0.0 1.0))
  (CallFunction|StageStep :DT _dt :Snap Snap)
  (if (or Snap (and (!= (Variables|Z-Interno|GetStagePhase) 1) (!= (Variables|Z-Interno|GetStagePhase) 5)))
    (Utilities|Array|Resize (Variables|Z-Interno|GetPos) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetVel) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetBridgeP) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetTgtA) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetSprW2A) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetSprDA) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetGroupDT) 10)
    (Utilities|Array|Resize (Variables|Z-Interno|GetDoRef) 10)
    (Variables|Z-Interno|SetClock (+ (Variables|Z-Interno|GetClock) _dt))
    (Variables|Z-Interno|SetS (select Snap _tgt (Math|Interpolation|FInterpTo (Variables|Z-Interno|GetS) _tgt _dt (select _out 3.0 (Variables|1-Estado|GetStateSmoothing)))))
    (Variables|Z-Interno|SetAgTarget (+ (Variables|1-Estado|GetAgitation) (* (Variables|1-Estado|GetActivityDrive) (- 1.0 (* (* _u _u) (- 3.0 (* 2.0 _u)))))))
    (Variables|Z-Interno|SetPhase (Math|Float|%(Float) (+ (Variables|Z-Interno|GetPhase) (/ (* 6.2831853 _dt) (/ 7.0 (* (Math|Float|Max(Float) (Variables|4-Vida|GetPulseSpeed) 0.05) (+ 1.0 (* 0.4 (Variables|Z-Interno|GetAgTarget))))))) 6.2831853))
    (Variables|Z-Interno|SetStaticDirty (or (Variables|Z-Interno|GetStaticDirty) Snap))
    (Variables|Z-Interno|SetSimFrame (select Snap 0 (+ (Variables|Z-Interno|GetSimFrame) 1)))
    (Variables|Z-Interno|SetNLast (- _n 1))
    (for _i (range _n)
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetDoRef) _i (or Snap (== (Math|Integer|%(Integer) (+ _i (Variables|Z-Interno|GetSimFrame)) _r) 0)))
      (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetGroupDT) _i (+ (Utilities|Array|Get(acopy) (Variables|Z-Interno|GetGroupDT) _i) _dt)))
    (CallFunction|LifeStep :DT _dt :Snap Snap)
    (CallFunction|CalmStep :DT _dt :Snap Snap)
    (for _index (range _n)
      (CallFunction|StepGroup :Index _index :DT _dt :Snap Snap))
    (if (Variables|2-Forma|GetBridges)
      (for _index_1 (range 10)
        (Utilities|Array|SetArrayElem (Variables|Z-Interno|GetBridgeP) _index_1 (Math|Float|MapRangeClamped (Variables|Z-Interno|GetS) (+ 0.54 (* 0.04 (Math|Conversions|ToFloat(Integer) _index_1))) (+ 0.74 (* 0.04 (Math|Conversions|ToFloat(Integer) _index_1))) 0.0 1.0)))
      (CallFunction|BridgeStep :DT _dt :Snap Snap)
      (CallFunction|BridgeGate)
      (else
        (if Snap
          (CallFunction|BridgeGate))))))

;; ===== GRAFO: PushAll
;; = la versión de loving_tick_perf.dsl, sin empujar nada mientras está escondida (fases 1 y 5).
(fn PushAll ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _p0 (Utilities|Array|Get(acopy) _pos 0))
  (bind _p1 (Utilities|Array|Get(acopy) _pos 1))
  (bind _p2 (Utilities|Array|Get(acopy) _pos 2))
  (bind _p3 (Utilities|Array|Get(acopy) _pos 3))
  (bind _p4 (Utilities|Array|Get(acopy) _pos 4))
  (bind _p5 (Utilities|Array|Get(acopy) _pos 5))
  (bind _lv2 (Math|Color|MakeColor (Variables|2-Forma|GetGroupSize) (Variables|2-Forma|GetGroupSpread) (Variables|2-Forma|GetCenterAttraction) (Variables|2-Forma|GetConnectionStrength)))
  (bind _lv3 (Math|Color|MakeColor (Variables|3-Membrana|GetMembraneThickness) (Variables|3-Membrana|GetMembraneOpacity) (Variables|4-Vida|GetNoiseAmount) (Variables|4-Vida|GetOrganicMotion)))
  (if (and (!= (Variables|Z-Interno|GetStagePhase) 1) (!= (Variables|Z-Interno|GetStagePhase) 5))
    (Variables|Z-Interno|SetStaticDirty (or (Variables|Z-Interno|GetStaticDirty) (or (not (Math|Color|NearEqual(LinearColor) _lv2 (Variables|Z-Interno|GetLV2P) 0.0)) (or (not (Math|Color|NearEqual(LinearColor) _lv3 (Variables|Z-Interno|GetLV3P) 0.0)) (or (not (Math|Color|NearEqual(LinearColor) (Variables|Default|GetLV5) (Variables|Z-Interno|GetLV5P) 0.0)) (!= _n (Variables|Z-Interno|GetNP)))))))
    (Variables|Default|SetLV2 _lv2)
    (Variables|Default|SetLV3 _lv3)
    (CallFunction|LifeLV)
    (CallFunction|PushGlobals :Comp (Variables|Default|GetCentre))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M0" (Math|Color|MakeColor (.x _p0) (.y _p0) (.z _p0) (select (> _n 0) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M1" (Math|Color|MakeColor (.x _p1) (.y _p1) (.z _p1) (select (> _n 1) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M2" (Math|Color|MakeColor (.x _p2) (.y _p2) (.z _p2) (select (> _n 2) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M3" (Math|Color|MakeColor (.x _p3) (.y _p3) (.z _p3) (select (> _n 3) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M4" (Math|Color|MakeColor (.x _p4) (.y _p4) (.z _p4) (select (> _n 4) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "M5" (Math|Color|MakeColor (.x _p5) (.y _p5) (.z _p5) (select (> _n 5) 1.0 0.0)))
    (CallFunction|PushGroupLive :Index 0 :Cluster (Variables|Default|GetCluster0) :Arm (Variables|Default|GetArm0) :Bridge (Variables|Default|GetBridge0))
    (CallFunction|PushGroupLive :Index 1 :Cluster (Variables|Default|GetCluster1) :Arm (Variables|Default|GetArm1) :Bridge (Variables|Default|GetBridge1))
    (CallFunction|PushGroupLive :Index 2 :Cluster (Variables|Default|GetCluster2) :Arm (Variables|Default|GetArm2) :Bridge (Variables|Default|GetBridge2))
    (CallFunction|PushGroupLive :Index 3 :Cluster (Variables|Default|GetCluster3) :Arm (Variables|Default|GetArm3) :Bridge (Variables|Default|GetBridge3))
    (CallFunction|PushGroupLive :Index 4 :Cluster (Variables|Default|GetCluster4) :Arm (Variables|Default|GetArm4) :Bridge (Variables|Default|GetBridge4))
    (CallFunction|PushGroupLive :Index 5 :Cluster (Variables|Default|GetCluster5) :Arm (Variables|Default|GetArm5) :Bridge (Variables|Default|GetBridge5))
    (CallFunction|PushCentreFilm)
    (CallFunction|PushMore)
    (Variables|Z-Interno|SetLV2P (Variables|Default|GetLV2))
    (Variables|Z-Interno|SetLV3P (Variables|Default|GetLV3))
    (Variables|Z-Interno|SetLV5P (Variables|Default|GetLV5))
    (Variables|Z-Interno|SetNP _n)
    (Variables|Z-Interno|SetStaticDirty false)))
