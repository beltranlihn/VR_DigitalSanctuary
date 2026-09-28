;; tb_tour.dsl - CONTRATO TOUR de BP_TBDirector_NC (copia de SC, /Game/NeuralCanvas/TB/). 2026-09-29.
;; Pedido de Narrativa (orquestador del recorrido, delegado por Beltran):
;;   - BeginPlay con algun actor de tag "TOUR" (o bForceTour) -> DORMIDO: no se autoinstala, no oculta las manos, sin input,
;;     sin Tick. Sin TOUR, L_TBTest_SC queda igual (TourBegin -> TourWake -> CheckController, como hoy).
;;   - TourWake() / TourSleep(): publicas, sin parametros, IDEMPOTENTES (bAwake).
;;     TourWake instala como hoy (o reinstala input y muestra lo suyo si ya estaba instalado).
;;     TourSleep: suelta el trazo, corta sonidos y haptica, quita input + IMC, devuelve las manos del pawn (solo si el
;;     director las oculto: bHidePawnHands), oculta mesa, paleta, mallas de mando y punta, apaga el Tick (actor, TBTool y
;;     paleta). Los trazos ya dibujados quedan (Narrativa oculta la celda entera).
;; scripts/tb_tour_sim.py EJECUTA este archivo con el resto del director simulado (stubs) -> TODO OK antes de pegar.
;;
;; COMO SE PEGA (turno de editor; el director YA EXISTE -> regla de oro 2):
;;   1. LEER antes: EventGraph, DoInstall, MountHands, HandsStep, ChargeStop, LoopStep, HapticStep, SetHandedness y la
;;      lista de variables (nombre real del AudioComponent del loop: aca LoopComp, VERIFICAR).
;;   2. Variables nuevas (Default, sin categoria al escribir; gotcha 466): bTourMode, bAwake (internas),
;;      bForceTour (instance editable; despues categoria "08 TOUR"). Compilar. CDO e INSTANCIA de L_TBTest_SC: false.
;;   3. Funciones NUEVAS (grafos vacios -> write_graph_dsl uno por grafo): TourShow, TourPalette, TourTable (On bool),
;;      TourHands, TourQuiet, TourSleepNow, TourWakeNow, TourWake, TourSleep, TourBegin.
;;   4. EventGraph EXISTENTE -> cirugia: en EventBeginPlay reemplazar la llamada a CheckController por CallFunction|TourBegin.
;;      Nada mas cambia (el Tick sigue llamando CheckController: dormido no tickea).
;;   5. Verificados con find_node_types (2026-09-29): Actor|GetAllActorswithTag, Utilities|Array|Length, Actor|Tick|SetActorTickEnabled,
;;      Components|Tick|SetComponentTickEnabled, Input|DisableInput, Game|Feedback|SetHapticsByValue.
;; Bools: getter SIN la b (gotcha 475). Llamadas propias por KEYWORD (gotchas 461/654). Un solo if/IsValid por lista y AL
;; FINAL (dsl.md trampa 1). Impuros nunca inline como dato: bind primero (lint de dsl_sim).

;; ===== GRAFO: TourShow  (funcion nueva; parametro de entrada On bool)
;; Lo visible del sistema: mallas de mando y punta, paleta (y su Tick), mesa. Con el sistema cerrado (bSystemDone) nada
;; vuelve a aparecer (5r). Mostrar = volver a montar: InstallTip (punta) + ApplyHands (AddDrawIMC + FixHands = el mando de
;; la mano habil, visible y enganchado + MirrorPalette; los tres idempotentes, leidos 2026-09-29). La paleta: OutroStep
;; vuelve a escribir su Tick/oculto cada cuadro mientras el director tickea.
(fn TourShow (On)
  (bind _vis (and On (not (Variables|Default|GetSystemDone))))
  (Rendering|SetVisibility (Variables|Default|GetSMRHand) false false)
  (Rendering|SetVisibility (Variables|Default|GetSMLHand) false false)
  (Rendering|SetVisibility (Variables|Default|GetSMTip) false false)
  (CallFunction|TourPalette :On _vis)
  (CallFunction|TourTable :On _vis)
  (if _vis
    (CallFunction|InstallTip)
    (CallFunction|ApplyHands)))

;; ===== GRAFO: TourPalette  (funcion nueva; parametro de entrada On bool)
(fn TourPalette (On)
  (bind _p (Variables|Default|GetPalette))
  (Utilities|IsValid _p
    (:"Is Valid"
      (Rendering|SetActorHiddenInGame _p (not On))
      (Actor|Tick|SetActorTickEnabled _p On))))

;; ===== GRAFO: TourTable  (funcion nueva; parametro de entrada On bool)
(fn TourTable (On)
  (bind _t (Variables|03SKETCH|GetDrawTable))
  (Utilities|IsValid _t
    (:"Is Valid"
      (Rendering|SetActorHiddenInGame _t (not On)))))

;; ===== GRAFO: TourHands  (funcion nueva, sin parametros)
;; Devuelve las manos del pawn SOLO si las oculto el director (bHidePawnHands): lo que el pawn oculto por su cuenta no se
;; toca. Misma forma que HandsStep (COPIAR su for + cast al leerlo), con el valor fijo en true.
(fn TourHands ()
  (bind _pawn (Game|GetPlayerPawn 0))
  (if (Variables|00MANO|GetHidePawnHands)
    (for _c (Actor|GetComponentsByClass _pawn "/Script/Engine.SkeletalMeshComponent")
      (bind _sk (Utilities|Casting|CastToSkeletalMeshComponent _c))
      (Rendering|SetVisibility _sk true false))))

;; ===== GRAFO: TourQuiet  (funcion nueva, sin parametros)
;; Solo si el sistema esta instalado (dormido desde BeginPlay no hay herramienta armada). Suelta el trazo (como soltar el
;; gatillo), apaga la haptica de las dos manos (HapSend usa SetHapticsByValue), la carga del Guardar y el loop del pincel
;; (ChargeStop y LoopStop ya traen su IsValid).
(fn TourQuiet ()
  (bind _pc (Game|GetPlayerController 0))
  (if (Variables|Default|GetReady)
    (CallFunction|TBReleaseFrom :FromLeft (Variables|00MANO|GetLeftHanded))
    (Variables|Default|SetCharging false)
    (Game|Feedback|SetHapticsByValue _pc 0.0 0.0 "Left")
    (Game|Feedback|SetHapticsByValue _pc 0.0 0.0 "Right")
    (CallFunction|ChargeStop)
    (CallFunction|LoopStop)))

;; ===== GRAFO: TourSleepNow  (funcion nueva, sin parametros) - el cuerpo de TourSleep, sin la guarda
;; Las manos NO van aca: TourBegin tambien pasa por aca y en ese momento el director no oculto nada.
(fn TourSleepNow ()
  (bind _pc (Game|GetPlayerController 0))
  (Variables|Default|SetAwake false)
  (CallFunction|TourQuiet)
  (Input|DisableInput self _pc)
  (CallFunction|RemoveDrawIMC)
  (CallFunction|TourShow :On false)
  (Components|Tick|SetComponentTickEnabled (Variables|Default|GetTBTool) false)
  (Actor|Tick|SetActorTickEnabled self false))

;; ===== GRAFO: TourWakeNow  (funcion nueva, sin parametros) - el cuerpo de TourWake, sin la guarda
;; Sin instalar: el Tick (CheckController) instala solo, como hoy. Ya instalado (se durmio y vuelve): input + lo visible.
;; La mesa no depende de la instalacion: se muestra siempre al despertar (dormido desde BeginPlay quedaba oculta: bug
;; encontrado por tb_tour_sim.py).
(fn TourWakeNow ()
  (Variables|Default|SetAwake true)
  (Actor|Tick|SetActorTickEnabled self true)
  (Components|Tick|SetComponentTickEnabled (Variables|Default|GetTBTool) true)
  (CallFunction|TourTable :On (not (Variables|Default|GetSystemDone)))
  (if (Variables|Default|GetReady)
    (CallFunction|InstallInput)
    (CallFunction|TourShow :On true)
    (else
      (CallFunction|CheckController))))

;; ===== GRAFO: TourWake  (funcion nueva, sin parametros) - PUBLICA
(fn TourWake ()
  (if (not (Variables|Default|GetAwake))
    (CallFunction|TourWakeNow)))

;; ===== GRAFO: TourSleep  (funcion nueva, sin parametros) - PUBLICA
(fn TourSleep ()
  (if (Variables|Default|GetAwake)
    (CallFunction|TourSleepNow)
    (CallFunction|TourHands)))

;; ===== GRAFO: TourBegin  (funcion nueva, sin parametros) - la llama EventBeginPlay (cirugia, paso 4)
;; Con TOUR (o bForceTour): dormido desde el primer cuadro (TourSleepNow sin guarda: bAwake nace en false).
(fn TourBegin ()
  (bind _all (Actor|GetAllActorswithTag "TOUR"))
  (Variables|Default|SetTourMode (or (Variables|Default|GetForceTour) (> (Utilities|Array|Length _all) 0)))
  (if (Variables|Default|GetTourMode)
    (CallFunction|TourSleepNow)
    (else
      (CallFunction|TourWakeNow))))
