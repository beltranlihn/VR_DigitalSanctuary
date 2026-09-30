;; tb_contract.dsl - CONTRATO DE ETAPA de BP_TBDirector_NC (Surrounding / dibujo). 2026-09-30, noche.
;; Pedido de Narrativa (director de la noche, delegado por Beltran) - docs/PLAN-NOCHE-2026-09-30.md:
;;   StageIntro() -> entran mesa, punta y paleta (la paleta con su aparicion "luz primero", AppearDelay 3 s). SIN dibujo.
;;   StageBegin() -> se puede dibujar.
;;   bStageDone   -> true cuando termino el cierre que ya existe: tinta agotada (o SAVE sostenido) -> SaveSketch -> el dibujo
;;                   va al frente y da sus vueltas (SketchPhase 1..5) -> SketchPhase vuelve a 0 con bSystemDone.
;;   StageOutro() -> mesa, punta y paleta se van (<= 3 s). El DIBUJO no se borra (lo usa el cuadro de resultados).
;;   bContractTest -> en L_TBTest_SC: nace dormido y corre solo Intro (1 s) -> Begin (+ContractBeginDelay) -> Outro (al terminar
;;                   o por cortafuegos ContractFirewall 240 s desde Begin).
;; NADA de estetica ni valores de Beltran (etapa aprobada). Solo logica de ciclo de vida.
;;
;; DECISIONES (leidas en el tracker, BP_TBStroke.md 5p/5r/5s/5t):
;; - El gatillo que dibuja llega por IA_Shoot_* (IMC_Weapon_* del pawn); RemoveDrawIMC NO los saca. bCanDraw tampoco sirve de
;;   candado (lo reescriben la paleta y OutroStep cada cuadro, orden de Tick no garantizado). CANDADO = DisableInput del director
;;   mientras bStageLock (cada cuadro: la instalacion del Tick puede volver a habilitarlo). StageBegin -> InstallInput.
;; - StageOutro forzado (cortafuegos, sin guardado): captura las escalas base y levanta bSystemDone -> el OutroStep de siempre
;;   encoge mando y punta, apaga el Tick de la paleta (-> su arte hace Vanish, 1,5 s) y TableEndStep oculta la mesa. Los trazos
;;   quedan donde estan. Con el cierre normal ya hecho, Outro es un no-op (idempotente).
;;
;; COMO SE PEGA (turno de editor; el director YA EXISTE -> regla de oro 2):
;;   0. LEER: TourBegin (comparar con tb_tour.dsl), DirectorStep, los stubs de Narrativa (StageIntro/StageBegin/StageOutro vacios,
;;      bStageDone: nombre y categoria reales -> getter/setter con find_node_types).
;;   1. Variables: bStageLock, bOutroCalled, bContractBegan (bool), ContractT0 (float) en "Z-Contrato";
;;      bContractTest (bool, false), ContractBeginDelay (float, 8), ContractFirewall (float, 240) en "11 CONTRATO", instance editable.
;;      Compilar. CDO: false / 8 / 240. INSTANCIA de L_TBTest_SC: nacen en 0 -> poner 8 y 240 (anotarlo en el tracker: son nuevas,
;;      no son valores de Beltran). bContractTest queda FALSE en la instancia (el nivel de Beltran se comporta igual que hoy).
;;   2. Verificar con find_node_types / get_node_type_pins: Utilities|Time|SetTimerbyFunctionName (pines Object, FunctionName, Time,
;;      bLooping), Utilities|Time|GetGameTimeinSeconds, Input|DisableInput (ya usado en TourSleepNow).
;;   3. Funciones nuevas (grafos vacios): ContractLock, ContractDone, ContractTestStep, ContractStep, ContractArm, ContractIntroT,
;;      ContractBeginT, IntroStep, IntroArm, IntroRun, IntroPalDelay, PalDelayStep. Llenar los stubs StageIntro/StageBegin/StageOutro
;;      (vacios -> write_graph_dsl). ORDEN de escritura: primero las hojas (IntroPalDelay, IntroArm, IntroRun, ContractLock,
;;      ContractDone, InkRelease ya existe...), despues las que las llaman (IntroStep, ContractTestStep -> StageOutro antes,
;;      ContractStep, StageIntro, StageBegin, ContractIntroT, ContractBeginT, ContractArm) y al final TourBegin y la cirugia
;;      de DirectorStep. Compilar despues de cada tanda.
;;      TableEndStep: leerla y reescribirla con el fundido (ver abajo). TableStep/TableFadeSet: solo leer (rampa lineal ->
;;      smoothstep, unico cambio permitido ahi).
;;   4. TourBegin: borrar nodos no-entrada y reescribir (version de abajo = la de tb_tour.dsl + bContractTest + ContractArm).
;;   5. DirectorStep: cirugia -> CallFunction|ContractStep despues de InkStep (connect then -> execute).
;;   6. PIE con bContractTest=true en la INSTANCIA (temporal; volver a false): a 0,5 s dormido; a ~1,5 s Intro (mesa y paleta
;;      visibles, input deshabilitado); a ~9 s Begin (input habilitado); InkMeters 1 + bSynth -> se agota -> presentacion ->
;;      bStageDone -> Outro. Devolver InkMeters 30, bSynth false, bContractTest false. Guardar BP con ruta explicita.

;; ESTANDAR HIGH END (Beltran via Narrativa, 2026-09-30): "toda entrada y salida con curva, sin saltos de un cuadro, con sonido".
;; Lo que hoy salta de golpe en el flujo del contrato y como se arregla (sin tocar la estetica aprobada):
;;   - MESA al entrar: TourTable la muestra con el TableFade que haya quedado (1) -> pop. Arreglo: en StageIntro,
;;     Tool.TableFadeSet(0) YA (sin esperar al Tick) + Tool.TableT = 0 -> la rampa de fase 0 que ya existe la funde en 1 s.
;;     LEER TableStep/TableFadeSet en el turno: si esa rampa es lineal, envolverla en smoothstep (curva, no linea).
;;   - MANDO y PUNTA al entrar: InstallTip/ApplyHands los prenden de golpe. Arreglo: IntroStep (espejo del OutroStep que los
;;     encoge): cuando el sistema esta instalado, captura su escala y los crece con smoothstep en IntroTime (0,8 s).
;;   - PALETA en el contrato (Narrativa, 2026-09-30, corregido tras aclaracion de Beltran: "los 3 s eran solo para probar,
;;     la animacion no se veia si pasaba apenas cargado el nivel"): StageIntro pone en el arte AppearDelay =
;;     ContractPaletteDelay (0,6 s) EN RUNTIME (no se guarda) -> escalon corto DESPUES de mesa y mandos, entrada por capas.
;;     El test suelto (sin TOUR ni bContractTest) sigue con los 3 s de la plantilla.
;;   - MESA en el Outro forzado (cortafuegos, sin guardado): TableEndStep la ocultaba de golpe con TableFade 1 -> pop.
;;     Arreglo: TableEndStep escribe TableFade = 1 - smooth(OutroT/OutroTime) mientras bSystemDone y fase 0 (despues del
;;     TableStep del mismo cuadro: gana la ultima escritura) y la oculta recien con OutroT >= OutroTime. En el cierre normal
;;     la fase 5 ya la dejo en 0 y OutroT ya es grande -> igual que hoy.
;; REGLAS DE LA OBRA (Narrativa, 2026-09-30, docs/PLAN-NOCHE-2026-09-30.md) aplicadas aca:
;;   3) Ninguna animacion en BeginPlay ni en el cuadro de un encendido: dormido en modo TOUR/contrato; las entradas las dispara
;;      StageIntro (evento del director). La paleta nace ContractPaletteDelay (0,6 s) despues, nunca en el mismo cuadro.
;;   4) Dt = min(DeltaTime, 1/30) en toda animacion:
;;      - UN punto para todo el director: EventTick -> DirectorStep(DT) pasa a DirectorStep(min(DeltaSeconds, 0.0333))
;;        (cirugia en el EventGraph: Math|Float|Min(Float) entre DeltaSeconds y el pin DT). Lo heredan SketchStep2 (la
;;        presentacion del dibujo), TableStep (fundidos de la mesa), OutroStep (encogido), HaloStep y HapticStep. A 72 fps
;;        (13,9 ms) no cambia nada; solo recorta los cuadros trabados (> 33 ms).
;;      - IntroRun: min(GetWorldDeltaSeconds, 0.0333).
;;      - BP_DrawPalette_SC.AppearGate: WantT += min(GetWorldDeltaSeconds, 0.0333) (reescribir la funcion, es chica).
;;      - El reloj de la aparicion es de Mesh 3D (BPC_AppearLuz_SC, Tick con DeltaSeconds): avisar, lo clampea el.
;;   5) Espera de diagnostico SOLO en el test suelto, detras de un flag: el flag es bTourMode (TOUR / bForceTour /
;;      bContractTest). PalDelayStep (en ContractStep): si bTourMode -> IntroPalDelay cada cuadro (un setter, barato):
;;      cubre StageIntro, TourWake viejo y la paleta creada tarde en DoInstall. Sin tour, la plantilla (3 s) manda.
;; Variables extra: bIntroPending, bIntroAnim (bool), IntroT, IntroR, IntroL, IntroTip (float/vector) en Z-Contrato;
;; IntroTime (0,8) y ContractPaletteDelay (0,6) en "11 CONTRATO" (instance editable; CDO + instancia de L_TBTest_SC).

;; ===== BUG del primer PIE de la Obra (Narrativa, 2026-09-30): 5.499 "Accessed None trying to read property Tip" en ~30 s.
;; BPC_TBTool_NC tickea sin Tip (en la Obra el director esta dormido o sin instalar y nadie llama TourWake). Arreglo:
;;   a) BPC_TBTool_NC.EventTick: LEER el grafo, ubicar que lee Tip (SynthStep / FeedStroke / GateStop...) y poner la guarda al
;;      frente: EventTick -> IsValid(Tip) -> (cadena de hoy). Cirugia: insertar el macro IsValid entre el evento y el primer
;;      nodo (romper then->execute, conectar evento->IsValid.exec, IsValid."Is Valid"->primer nodo, Tip->IsValid.InputObject).
;;   b) BP_TBTrail_NC.TrailRun: la estela es un actor aparte que tickea SIEMPRE y en TrailPush lee ToolRef.Tip -> mismo error.
;;      Condicion de TrailFeed: agregar Tip valido Y visible (dormido la punta esta oculta -> no hay estela fantasma).
;;      Pure IsValid: buscar el tipo con find_node_types("IsValid") (Kismet IsValid puro); IsVisible: Rendering|IsVisible.
;;   PRUEBAS (las dos que pidio Narrativa), contando errores en el log:
;;      1) bForceTour = true en la instancia (= tag TOUR) sin llamar nada, 15 s -> 0 "Accessed None". Volver a false.
;;      2) bContractTest = true, ciclo entero (con InkMeters 1 + bSynth para llegar al final) -> 0 errores. Volver todo.

;; ===== GRAFO: StageIntro  (stub de Narrativa, vacio)
(fn StageIntro ()
  (bind _tool (Variables|Default|GetTBTool))
  (bind _pal (Variables|Default|GetPalette))
  (Variables|Default|SetStageDone false)
  (Variables|Z-Contrato|SetStageLock true)
  (Variables|Z-Contrato|SetOutroCalled false)
  (Variables|Z-Contrato|SetIntroPending true)
  (Class|BPCTBToolNC|SetTableT :self _tool :TableT 0.0)
  (Class|BPCTBToolNC|TableFadeSet :self _tool :V 0.0)          ;; CONFIRMAR nombre del parametro al leer TableFadeSet
  (CallFunction|TourWake)
  (CallFunction|IntroPalDelay)
  (CallFunction|IntroStep))                                       ;; ya instalado: captura y achica EN ESTE instante (sin cuadro a escala llena)
;; ORDEN: el AppearDelay se escribe DESPUES de TourWake, pero el arte recien lo lee en su Tick (AppearGate) -> llega a tiempo.
;; Si el arte todavia no existe (primer despertar sin instalar: la paleta se crea en DoInstall con la plantilla, 3 s),
;; IntroArm lo vuelve a escribir en el primer cuadro con Ready -> WantT todavia es ~0 -> usa 0,6 s.

;; ===== GRAFO: IntroPalDelay  (nueva) - la espera corta de la paleta SOLO en el contrato (runtime, no se guarda)
(fn IntroPalDelay ()
  (bind _pal (Variables|Default|GetPalette))
  (Utilities|IsValid _pal
    (:"Is Valid"
      (bind _art (Class|BPTBPalette|GetArt _pal))
      (Utilities|IsValid _art
        (:"Is Valid"
          (Class|BPDrawPaletteSC|SetAppearDelay :self _art :AppearDelay (Variables|11CONTRATO|GetContractPaletteDelay)))))))

;; ===== GRAFO: IntroStep  (nueva, dentro de ContractStep) - el mando y la punta crecen con curva al entrar
;; ORDEN A VERIFICAR EN EL TURNO: en el EventTick, ¿CheckController (instala) corre ANTES que DirectorStep? Si corre DESPUES,
;; el cuadro de la instalacion se veria a escala llena -> llamar IntroStep tambien al final de DoInstall (cirugia de 1 nodo).
(fn IntroStep ()
  (CallFunction|IntroArm)
  (CallFunction|IntroRun))

(fn IntroArm ()
  (if (and (Variables|Z-Contrato|GetIntroPending) (Variables|Default|GetReady))
    (CallFunction|IntroPalDelay)
    (Variables|Z-Contrato|SetIntroPending false)
    (Variables|Z-Contrato|SetIntroAnim true)
    (Variables|Z-Contrato|SetIntroT 0.0)
    (Variables|Z-Contrato|SetIntroR (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMRHand)))
    (Variables|Z-Contrato|SetIntroL (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMLHand)))
    (Variables|Z-Contrato|SetIntroTip (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMTip)))))

(fn IntroRun ()
  (bind _x (Math|Float|Clamp(Float) (/ (Variables|Z-Contrato|GetIntroT) (Math|Float|Max(Float) (Variables|11CONTRATO|GetIntroTime) 0.01))))
  (bind _k (Math|Float|Max(Float) (* _x (* _x (- 3.0 (* 2.0 _x)))) 0.001))
  (if (Variables|Z-Contrato|GetIntroAnim)
    (Variables|Z-Contrato|SetIntroT (+ (Variables|Z-Contrato|GetIntroT) (Math|Float|Min(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0333)))
    (Transformation|SetRelativeScale3D (Variables|Default|GetSMRHand) (* (Variables|Z-Contrato|GetIntroR) _k))
    (Transformation|SetRelativeScale3D (Variables|Default|GetSMLHand) (* (Variables|Z-Contrato|GetIntroL) _k))
    (Transformation|SetRelativeScale3D (Variables|Default|GetSMTip) (* (Variables|Z-Contrato|GetIntroTip) _k))
    (Variables|Z-Contrato|SetIntroAnim (< _x 1.0))))
;; (ojo: el bind _x se reevalua por consumidor; el SetIntroT va ANTES de los SetRelativeScale3D -> los usa ya avanzado; en el
;;  ultimo cuadro _x = 1 -> k = 1 exacto y SetIntroAnim false. Correcto.)

;; ===== GRAFO: TableEndStep  (EXISTE -> LEER y reescribir; hoy: SetActorHiddenInGame(DrawTable, bSystemDone AND fase 0))
;; (fn TableEndStep ()
;;   (bind _tool (Variables|Default|GetTBTool))
;;   (bind _t (Variables|03SKETCH|GetDrawTable))
;;   (bind _end (and (Variables|Default|GetSystemDone) (== (Class|BPCTBToolNC|GetSketchPhase _tool) 0)))
;;   (bind _x (Math|Float|Clamp(Float) (/ (Variables|Default|GetOutroT) (Math|Float|Max(Float) (Variables|03SKETCH|GetOutroTime) 0.01))))
;;   (Utilities|IsValid _t
;;     (:"Is Valid"
;;       (if _end
;;         (Class|BPCTBToolNC|TableFadeSet :self _tool :V (- 1.0 (* _x (* _x (- 3.0 (* 2.0 _x))))))
;;         (Rendering|SetActorHiddenInGame _t (>= _x 1.0))
;;         (else
;;           (Rendering|SetActorHiddenInGame _t false))))))
;;   ^ CUIDADO: hoy el "else" NO escribe hidden=false (lo escribe con el valor del and). Mantener exactamente lo de hoy para el
;;     caso no-fin: SetActorHiddenInGame(_t, false) solo si hoy se escribia cada cuadro (leerlo). Dormido no tickea -> TourTable manda.

;; ===== GRAFO: StageBegin  (stub de Narrativa, vacio)
(fn StageBegin ()
  (Variables|Z-Contrato|SetStageLock false)
  (Variables|Z-Contrato|SetContractBegan true)
  (Variables|Z-Contrato|SetContractT0 (Utilities|Time|GetGameTimeinSeconds))
  (if (Variables|Default|GetReady)
    (CallFunction|InstallInput)))

;; ===== GRAFO: StageOutro  (stub de Narrativa, vacio)
(fn StageOutro ()
  (bind _pc (Game|GetPlayerController 0))
  (Variables|Z-Contrato|SetOutroCalled true)
  (Variables|Z-Contrato|SetStageLock false)
  (CallFunction|InkRelease)
  (Input|DisableInput self _pc)
  (CallFunction|RemoveDrawIMC)
  (if (not (Variables|Default|GetSystemDone))
    (Variables|Default|SetRHandS0 (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMRHand)))
    (Variables|Default|SetLHandS0 (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMLHand)))
    (Variables|Default|SetTipS0 (Class|SceneComponent|GetRelativeScale3D (Variables|Default|GetSMTip)))
    (Variables|Default|SetOutroT 0.0)
    (Variables|Default|SetSystemDone true)))

;; ===== GRAFO: ContractLock  (nueva) - candado del hueco de instrucciones
(fn ContractLock ()
  (bind _pc (Game|GetPlayerController 0))
  (if (and (Variables|Z-Contrato|GetStageLock) (Variables|Default|GetReady))
    (Input|DisableInput self _pc)))

;; ===== GRAFO: ContractDone  (nueva) - bStageDone pegajoso: el cierre de siempre termino (dibujo al frente, vueltas, fase 0)
;; bStageDone: stub de Narrativa, bool en categoria Default (confirmado 2026-09-30) -> Variables|Default|Get/SetStageDone.
(fn ContractDone ()
  (bind _tool (Variables|Default|GetTBTool))
  (Utilities|IsValid _tool
    (:"Is Valid"
      (Variables|Default|SetStageDone (or (Variables|Default|GetStageDone) (and (Variables|Default|GetSystemDone) (== (Class|BPCTBToolNC|GetSketchPhase _tool) 0)))))))

;; ===== GRAFO: ContractTestStep  (nueva) - solo con bContractTest: Outro al terminar o por cortafuegos
(fn ContractTestStep ()
  (if (and (Variables|11CONTRATO|GetContractTest) (and (Variables|Z-Contrato|GetContractBegan) (and (not (Variables|Z-Contrato|GetOutroCalled)) (or (Variables|Default|GetStageDone) (> (- (Utilities|Time|GetGameTimeinSeconds) (Variables|Z-Contrato|GetContractT0)) (Variables|11CONTRATO|GetContractFirewall))))))
    (CallFunction|StageOutro)))

;; ===== GRAFO: ContractStep  (nueva) - al final de DirectorStep (cirugia)
(fn ContractStep ()
  (bind _self self)
  (CallFunction|ContractLock _self)
  (CallFunction|PalDelayStep _self)
  (CallFunction|IntroStep _self)
  (CallFunction|ContractDone _self)
  (CallFunction|ContractTestStep _self))

;; ===== GRAFO: PalDelayStep  (nueva) - regla 5: la espera de 3 s de la paleta solo en el test suelto
(fn PalDelayStep ()
  (if (Variables|Default|GetTourMode)
    (CallFunction|IntroPalDelay)))

;; ===== BP_DrawPalette_SC.AppearGate  (EXISTE, la escribi hoy -> borrar nodos y reescribir; unico cambio: el paso de WantT)
;; (fn AppearGate (Want)
;;   (bind _self self)
;;   (CallFunction|AppearEnsure _self)
;;   (Variables|Z-Interno|SetWantT (select Want (+ (Variables|Z-Interno|GetWantT) (Math|Float|Min(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0333)) 0.0))
;;   (bind _desired (and Want (>= (Variables|Z-Interno|GetWantT) (Variables|Aparicion|GetAppearDelay))))
;;   (bind _c (Variables|Z-Interno|GetAppearComp))
;;   (Utilities|IsValid _c
;;     (:"Is Valid"
;;       (Class|BPCAppearLuzSC|SetDemo :self _c :Demo (Variables|Aparicion|GetAppearDemo))
;;       (Rendering|SetActorHiddenInGame _self (and (not _desired) (not (Class|BPCAppearLuzSC|GetPlaying _c))))
;;       (if (and (Variables|Z-Interno|GetArtReady) (!= _desired (Variables|Z-Interno|GetShown)))
;;         (CallFunction|AppearFlip _self _desired)))
;;     (:"Is Not Valid"
;;       (Rendering|SetActorHiddenInGame _self (not _desired)))))

;; ===== GRAFO: ContractArm  (nueva) - desde TourBegin, solo dormido por bContractTest
(fn ContractArm ()
  (if (Variables|11CONTRATO|GetContractTest)
    (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ContractIntroT" :Time 1.0 :bLooping false)))

;; ===== GRAFO: ContractIntroT  (nueva) - la llama el timer
(fn ContractIntroT ()
  (CallFunction|StageIntro)
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ContractBeginT" :Time (Variables|11CONTRATO|GetContractBeginDelay) :bLooping false))

;; ===== GRAFO: ContractBeginT  (nueva) - la llama el timer
(fn ContractBeginT ()
  (CallFunction|StageBegin))

;; ===== GRAFO: TourBegin  (EXISTE -> borrar nodos no-entrada y reescribir; LEERLA antes y comparar con tb_tour.dsl)
(fn TourBegin ()
  (bind _all (Actor|GetAllActorswithTag "TOUR"))
  (Variables|Default|SetTourMode (or (or (Variables|Default|GetForceTour) (Variables|11CONTRATO|GetContractTest)) (> (Utilities|Array|Length _all) 0)))
  (if (Variables|Default|GetTourMode)
    (CallFunction|TourSleepNow)
    (CallFunction|ContractArm)
    (else
      (CallFunction|TourWakeNow))))
