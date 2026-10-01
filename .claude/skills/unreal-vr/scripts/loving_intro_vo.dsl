;; BP_LovingCell_SC — la neurona espera a que Alma se haga a un lado + las VO de Loving que no sonaban
;; (2026-10-01, prueba de la Obra de Beltrán, vía Narrativa: docs/PLAN-CORRECCIONES-2026-10-01.md C2 + A2).
;;
;; 1. ENTRADA DESPUÉS DE ALMA. Alma da la bienvenida (VO_20) en TP sc2_alma_in = (220, 0, +5), justo donde nace la neurona
;;    (200, 0, 115). La Obra (fase 4 → AlmaAside + CallIntro) y el runner (fase 1 → MoveTo(TagSide) + StageIntro) llaman
;;    StageIntro EN EL MISMO CUADRO en que Alma empieza a irse (MoveTo, TravelTime 3 s, EaseInOut): la neurona crecía
;;    (ease-out-back: 59 % del tamaño a los 0,6 s) con Alma todavía encima.
;;    → reloj propio de la entrada IntroClk (corre en las fases 2 y 3) y la curva de entrada empieza a los IntroDelay s
;;      (2,0: Alma ya recorrió ~80 % del camino, a más de 2 m de la neurona). El sonido de aparición se dispara en ese
;;      mismo instante (antes sonaba en StageIntro, con Alma todavía al frente).
;;    → mientras espera sigue OCULTA (como en la fase 1); se muestra recién cuando arranca la curva.
;;    → si StageBegin llega antes de que termine la entrada (DebugStart, otro InstrTime), la fase 3 SIGUE la curva desde
;;      donde iba: sin salto a escala 1 (antes la fase 3 era escala 1 fija). Con la entrada completa _ob = 1 exacto.
;;    Presupuesto: IntroDelay 2 + IntroTime 3 = 5 s ≤ InstrTime 6 (Obra y runner): la neurona termina de formarse 1 s
;;    antes de que arranque la mecánica.
;; 2. VO_22 y VO_23 (existían como asset, nadie las disparaba). Guion V5 §7.3: tres momentos de Alma separados por silencio;
;;    VO_20 ya trae el primero (VO_21 unida). Las dice ALMA (al costado durante la mecánica) con SayClip: reacciona a su voz.
;;    Alma = GetActorOfClass(BP_Alma_SC) (en la Obra, la suya; en el ensayo, Alma_Ensayo).
;;    Narrativa 10-01: Alma habla SOLO si está visible y no está diciendo otra VO (LovAlmaFree); si no, la VO espera hasta
;;    VOWait (8 s) y se salta. Sin Alma en el nivel no suena (regla A3: nunca voz sin verla).
;;    VO22At 15 s · VO23At 42 s de mecánica (VO_22 dura 7,07 s → 20 s de silencio → VO_23 2,59 s → ~15 s hasta bStageDone
;;    a los StageDuration s, cuando la Obra dice VO_23b). StageDuration 80 -> 60 (Narrativa 10-01, "nada demasiado largo").
;;    Solo en la fase 3 (la mecánica): con la salida (fase 4) no se dispara nada.
;; Grafos: StageIntro y StageVisual REESCRITOS desde esta fuente (vaciar + escribir; StageIntro no tenía empalmes);
;;   LovCues(DT) + LovCueSound + LovAlmaFree + LovCueVO22 + LovCueVO23 NUEVOS (prefijo Lov: colisión de nombres del DSL), LovCues empalmado por cirugía en StageStep después de StageCouple (DT = el DT de StageStep, ya ≤ 1/30).
;; Variables nuevas: 9-Etapa IntroDelay (2,0) · VO22 · VO23 (SoundBase) · VO22At (15) · VO23At (42) · VOWait (8)
;;   · Z-Interno IntroClk · IntroSndDone · VO22Done · VO23Done · AlmaReady.
;; <A_LEAVING>/<A_APPEART>/<A_VOCOMP>/<ISPLAYING>: type_id de los getters de BP_Alma_SC (bLeaving, AppearT, VOComp) y de
;;   AudioComponent.IsPlaying, resueltos en el turno con find_node_types (trampa 9 de la Obra: Audio|Components|... puede
;;   resolver a SynthComponent).
;; <DONE> = setter de bStageDone (type_id resuelto en el turno, como en el contrato).

;; ===== GRAFO: StageIntro
(fn StageIntro ()
  (Variables|Z-Interno|SetStagePhase 2)
  (Variables|Z-Interno|SetStageT 0.0)
  (<DONE> false)
  (Variables|Z-Interno|SetIntroClk 0.0)
  (Variables|Z-Interno|SetIntroSndDone false)
  (Variables|Z-Interno|SetVO22Done false)
  (Variables|Z-Interno|SetVO23Done false))

;; ===== GRAFO: LovCues
;; Reloj de la entrada (sin rama: select) + las tres señales. DT llega ya limitado a 1/30 (Simulate).
;; (dsl.md trampa 1: un if/IsValid termina la lista -> cada señal es su propia función)
(fn LovCues (DT)
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (Variables|Z-Interno|SetIntroClk (+ (Variables|Z-Interno|GetIntroClk) (select (or (== _ph 2) (== _ph 3)) DT 0.0)))
  (CallFunction|LovCueSound)
  (CallFunction|LovCueVO22)
  (CallFunction|LovCueVO23))

;; ===== GRAFO: LovCueSound
;; El sonido de aparición, una vez, cuando la neurona empieza a crecer (IntroClk = IntroDelay).
(fn LovCueSound ()
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (if (and (or (== _ph 2) (== _ph 3)) (and (not (Variables|Z-Interno|GetIntroSndDone)) (>= (Variables|Z-Interno|GetIntroClk) (Variables|9-Etapa|GetIntroDelay))))
    (Variables|Z-Interno|SetIntroSndDone true)
    (Audio|PlaySound2D :Sound (Variables|9-Etapa|GetSndIntro) :VolumeMultiplier (Variables|9-Etapa|GetSndVolume))))

;; ===== GRAFO: LovAlmaFree
;; AlmaReady = hay Alma, está VISIBLE (no se está yendo y su entrada llegó a 0,95) y NO está diciendo otra VO
;; (su VOComp no existe o no suena). Pedido de Narrativa 10-01.
(fn LovAlmaFree ()
  (bind _a (Actor|GetActorOfClass "/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C"))
  (Variables|Z-Interno|SetAlmaReady false)
  (Utilities|IsValid _a
    (:"Is Valid"
      (Variables|Z-Interno|SetAlmaReady (and (not (<A_LEAVING> :self _a)) (>= (<A_APPEART> :self _a) 0.95)))
      (bind _vc (<A_VOCOMP> :self _a))
      (Utilities|IsValid _vc
        (:"Is Valid" (Variables|Z-Interno|SetAlmaReady (and (Variables|Z-Interno|GetAlmaReady) (not (<ISPLAYING> :self _vc)))))))))

;; ===== GRAFO: LovCueVO22
;; Solo en la mecánica. Llegada la hora: si Alma está libre, la dice; si no, espera (cada cuadro) hasta VOWait s y la salta.
(fn LovCueVO22 ()
  (if (and (== (Variables|Z-Interno|GetStagePhase) 3) (and (not (Variables|Z-Interno|GetVO22Done)) (>= (Variables|Z-Interno|GetStageT) (Variables|9-Etapa|GetVO22At))))
    (CallFunction|LovAlmaFree)
    (if (Variables|Z-Interno|GetAlmaReady)
      (Variables|Z-Interno|SetVO22Done true)
      (bind _a (Actor|GetActorOfClass "/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C"))
      (Class|BPAlmaSC|SayClip :self _a :Clip (Variables|9-Etapa|GetVO22))
      (else
        (Variables|Z-Interno|SetVO22Done (>= (Variables|Z-Interno|GetStageT) (+ (Variables|9-Etapa|GetVO22At) (Variables|9-Etapa|GetVOWait))))))))

;; ===== GRAFO: LovCueVO23
(fn LovCueVO23 ()
  (if (and (== (Variables|Z-Interno|GetStagePhase) 3) (and (not (Variables|Z-Interno|GetVO23Done)) (>= (Variables|Z-Interno|GetStageT) (Variables|9-Etapa|GetVO23At))))
    (CallFunction|LovAlmaFree)
    (if (Variables|Z-Interno|GetAlmaReady)
      (Variables|Z-Interno|SetVO23Done true)
      (bind _a (Actor|GetActorOfClass "/Game/SoulCharger/Core/Alma/BP_Alma_SC.BP_Alma_SC_C"))
      (Class|BPAlmaSC|SayClip :self _a :Clip (Variables|9-Etapa|GetVO23))
      (else
        (Variables|Z-Interno|SetVO23Done (>= (Variables|Z-Interno|GetStageT) (+ (Variables|9-Etapa|GetVO23At) (Variables|9-Etapa|GetVOWait))))))))

;; ===== GRAFO: StageVisual
;; = la versión de loving_stage_contract.dsl con la entrada por IntroClk (espera IntroDelay) en las fases 2 Y 3.
(fn StageVisual ()
  (bind _ph (Variables|Z-Interno|GetStagePhase))
  (bind _t (Variables|Z-Interno|GetStageT))
  (bind _ki (Math|Float|Clamp(Float) (/ (- (Variables|Z-Interno|GetIntroClk) (Variables|9-Etapa|GetIntroDelay)) (Math|Float|Max(Float) (Variables|9-Etapa|GetIntroTime) 0.1)) 0.0 1.0))
  (bind _u (- _ki 1.0))
  (bind _ob (+ 1.0 (+ (* 1.8 (* (* _u _u) _u)) (* 0.8 (* _u _u)))))
  (bind _si (* (* (* _ki _ki) _ki) (+ (* _ki (- (* _ki 6.0) 15.0)) 10.0)))
  (bind _ko (Math|Float|Clamp(Float) (/ _t (Math|Float|Max(Float) (Variables|9-Etapa|GetOutroTime) 0.1)) 0.0 1.0))
  (bind _ka (Math|Float|Clamp(Float) (/ _ko 0.3) 0.0 1.0))
  (bind _sa (* (* _ka _ka) (- 3.0 (* 2.0 _ka))))
  (bind _kb (Math|Float|Clamp(Float) (/ (- _ko 0.3) 0.7) 0.0 1.0))
  (bind _sb (* (* (* _kb _kb) _kb) (+ (* _kb (- (* _kb 6.0) 15.0)) 10.0)))
  (bind _so (* (+ 1.0 (* 0.05 _sa)) (- 1.0 _sb)))
  (bind _wait (and (== _ph 2) (< (Variables|Z-Interno|GetIntroClk) (Variables|9-Etapa|GetIntroDelay))))
  (bind _hid (or (or (== _ph 1) (== _ph 5)) _wait))
  (bind _ent (or (== _ph 2) (== _ph 3)))
  (bind _s (select _hid 0.001 (select _ent (Math|Float|Max(Float) _ob 0.001) (select (== _ph 4) (Math|Float|Max(Float) _so 0.001) 1.0))))
  (bind _dz (select _ent (* -10.0 (- 1.0 _si)) (select (== _ph 4) (* 15.0 _sb) 0.0)))
  (if (!= _ph 0)
    (Transformation|SetActorScale3D :NewScale3D (* (Variables|Z-Interno|GetBaseScale) _s))
    (Transformation|SetActorLocation :NewLocation (+ (Variables|Z-Interno|GetBaseLoc) (Math|Vector|MakeVector 0.0 0.0 _dz)))
    (Rendering|SetActorHiddenInGame :bNewHidden _hid)))
