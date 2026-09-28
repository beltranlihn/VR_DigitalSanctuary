;; vida.dsl - los grafos de BP_ValleyLife_SC (la CAPA DE VIDA del valle de Entering: polvo + rafagas). 2026-09-28, rev. 2.
;; Plan: docs/PLAN-VIDA-VALLE-2026-09-28.md (seccion 11, receta del editor, pasos B1-B14).
;; Es la traduccion 1:1 de vida_model.VidaBP (step / push_dust / push_valley / sound_pos / preview / bench_full).
;; scripts/vida_dsl_sim.py EJECUTA este archivo (con el interprete de dsl_sim.py: un bind se re-evalua en cada uso)
;; y lo compara con el modelo:   python vida_dsl_sim.py   -> tiene que decir TODO OK antes de pegar nada en Unreal.
;;
;; COMO SE PEGA: un write_graph_dsl POR GRAFO, en el orden de las secciones. Cada bloque va entre las lineas
;; ";; ===== GRAFO: <nombre>" y se copia SIN los comentarios de cabecera. BP NUEVO: todos los grafos son nuevos o vacios
;; (regla de oro 2). Antes de escribir:
;;   - las funciones creadas (add_function_graph; todas las 'fn' de este archivo menos ConstructionScript) con sus
;;     parametros (add_function_param float: DT, Sign, Pitch, Live; add_object_function_param Snd), tabla 5.6 del plan;
;;   - las variables creadas y el BP compilado (tablas 5.4 y 5.5 del plan);
;;   - los type_id marcados VERIFICAR confirmados con find_node_types (lista en el plan, paso B9).
;; Categorias SIN espacios (A-Vida, B-Rafagas, C-Soplo, D-Sonido, E-Prueba, Z-Vida): con espacios el DSL no puede
;; escribirlas (gotcha 466). Bools: el getter/setter va SIN la b (bVida -> GetVida, bGusting -> GetGusting; gotcha 475).
;; Nombres sin palabras que Unreal pasa a minuscula en el nombre visible (On, In, To, Of...): por eso bGusting y no
;; bGustOn (daria GetGuston).
;; Llamadas a funciones propias con argumentos: por KEYWORD (:DT DT), nunca posicional (gotchas 461, 654).
;; Funciones IMPURAS (GetActorOfClass, CallFunction|...) NUNCA inline como argumento de datos: bind primero.
;; Un solo nodo multi-exec (if / IsValid) por lista de sentencias, y AL FINAL (dsl.md, trampa 1): por eso las funciones
;; chicas (VidaEnd, VidaMaybe, VidaDue, VidaPlay...).
;; Material sobre componente: Set{Color}ParameterValueonMaterials con "on" MINUSCULA (gotcha 2258); para un float4
;; empaquetado, el de Color (gotcha 451: el de Vector pierde la cuarta componente).

;; ===== GRAFO: VidaMPC  (funcion nueva, sin parametros)
;; PUENTE a MPC_Breath (Signed, On). Esqueleto por DSL + dos nodos por cirugia (gotcha 291), igual que AirMPC del
;; aliento (paso B11 del plan). En vida_dsl_sim.py lo reemplaza el MPC.
(fn VidaMPC ()
  (Variables|Z-Vida|SetVSig 0.0)
  (Variables|Z-Vida|SetVGate 0.0))

;; ===== GRAFO: VidaBreath  (funcion nueva; parametro de entrada DT float)
;; El detector de exhalacion (= el del aliento con sus defaults): velocidad de Signed con tope y solo con deteccion,
;; pasabajos 0,15 s, modo con histeresis (entra 0,10/s, sigue 0,04/s), inicio de exhalacion con latch (>= 0,6 s de
;; inhalacion antes). _new lee el modo VIEJO: se usa SOLO antes de SetFlow.
(fn VidaBreath (DT)
  (Variables|Z-Vida|SetVel (Math|Float|Clamp(Float) (select (and (Variables|Z-Vida|GetPrimed) (> (Variables|Z-Vida|GetVGate) 0.05)) (/ (- (Variables|Z-Vida|GetVSig) (Variables|Z-Vida|GetSprev)) DT) 0.0) -2.0 2.0))
  (Variables|Z-Vida|SetSprev (Variables|Z-Vida|GetVSig))
  (Variables|Z-Vida|SetPrimed true)
  (Variables|Z-Vida|SetVelF (+ (Variables|Z-Vida|GetVelF) (* (- (Variables|Z-Vida|GetVel) (Variables|Z-Vida|GetVelF)) (- 1.0 (Math|Float|Exp (neg (/ DT 0.15)))))))
  (bind _vf (Variables|Z-Vida|GetVelF))
  (bind _old (Variables|Z-Vida|GetFlow))
  (bind _new (select (> _old 0.5) (select (> _vf 0.04) 1.0 0.0) (select (< _old -0.5) (select (< _vf -0.04) -1.0 0.0) (select (> _vf 0.1) 1.0 (select (< _vf -0.1) -1.0 0.0)))))
  (Variables|Z-Vida|SetExhOnset (and (and (< _new -0.5) (> _old -0.5)) (>= (Variables|Z-Vida|GetInhHold) 0.6)))
  (Variables|Z-Vida|SetInhHold (select (Variables|Z-Vida|GetExhOnset) 0.0 (select (> _new 0.5) (+ (Variables|Z-Vida|GetInhHold) DT) (select (< (Variables|Z-Vida|GetInhHold) 0.6) 0.0 (Variables|Z-Vida|GetInhHold)))))
  (Variables|Z-Vida|SetFlow _new))

;; ===== GRAFO: VidaGap  (funcion nueva, sin parametros)
;; La espera hasta la proxima rafaga: GapMin..GapMax por una secuencia de baja discrepancia (gotcha 355).
(fn VidaGap ()
  (Variables|Z-Vida|SetWait (+ (Variables|B-Rafagas|GetGapMin) (* (- (Variables|B-Rafagas|GetGapMax) (Variables|B-Rafagas|GetGapMin)) (Math|Float|Fraction (+ (* (Variables|Z-Vida|GetGustIdx) 0.618034) 0.5))))))

;; ===== GRAFO: VidaGo  (funcion nueva, sin parametros)
;; Lo comun al arrancar una rafaga: el frente arranca en e0 - 2W y termina en e1 + 2W (el remolino de cada mota es un
;; lazo cerrado: nada salta al empezar ni al terminar); la velocidad sale de la duracion.
(fn VidaGo ()
  (Variables|Z-Vida|SetFront0 (- (Variables|Z-Vida|GetE0) (* 2.0 (Variables|Z-Vida|GetGW))))
  (Variables|Z-Vida|SetFront1 (+ (Variables|Z-Vida|GetE1) (* 2.0 (Variables|Z-Vida|GetGW))))
  (Variables|Z-Vida|SetFront (Variables|Z-Vida|GetFront0))
  (Variables|Z-Vida|SetFrontV (/ (- (Variables|Z-Vida|GetFront1) (Variables|Z-Vida|GetFront0)) (Math|Float|Max(Float) (Variables|Z-Vida|GetLife) 1.0)))
  (Variables|Z-Vida|SetGusting true)
  (Variables|Z-Vida|SetAmp (Variables|B-Rafagas|GetGustAmount))
  (Variables|Z-Vida|SetHold 1.0)
  (Variables|Z-Vida|SetHoldPh 0.0)
  (Variables|Z-Vida|SetHoldV 0.0)
  (Variables|Z-Vida|SetForce false))

;; ===== GRAFO: VidaStartLat  (funcion nueva; parametro de entrada Sign float: +1 / -1, 0 = el que toque)
;; SOLO la geometria de una rafaga LATERAL: cruza el valle de un lado al otro y pasa por el usuario; el frente es una
;; linea a lo largo del eje adelante, centrada a _m delante (la franja se ve en el llano de enfrente).
;; EDITOR 2026-09-29: (* vector <salida de un operador float>) NO se puede escribir ("Could not connect pin ReturnValue
;; to B", gotcha 490): OrgW y SndOffW se arman por componentes con F = (cos yaw, sin yaw, 0).
(fn VidaStartLat (Sign)
  (bind _k (Variables|Z-Vida|GetGustIdx))
  (bind _yaw (.yaw (Transformation|GetActorRotation)))
  (bind _sg (select (== Sign 0.0) (select (< (Math|Float|Fraction (+ (* _k 0.7548777) 0.25)) 0.5) 1.0 -1.0) Sign))
  (bind _ang (+ (+ _yaw (* 90.0 _sg)) (* (Variables|B-Rafagas|GetJitterDeg) (- (* 2.0 (Math|Float|Fraction (+ (* _k 0.4142136) 0.1))) 1.0))))
  (bind _m (+ (Variables|B-Rafagas|GetOffsetMin) (* (- (Variables|B-Rafagas|GetOffsetMax) (Variables|B-Rafagas|GetOffsetMin)) (Math|Float|Fraction (+ (* _k 0.5698403) 0.3)))))
  (bind _loc (Transformation|GetActorLocation))
  (bind _cy (Math|Trig|Cos(Degrees) _yaw))
  (bind _sy (Math|Trig|Sin(Degrees) _yaw))
  (Variables|Z-Vida|SetDirW (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _ang) (Math|Trig|Sin(Degrees) _ang) 0.0))
  (Variables|Z-Vida|SetOrgW (Math|Vector|MakeVector (+ (.x _loc) (* _cy _m)) (+ (.y _loc) (* _sy _m)) 0.0))
  (bind _sf (- (Variables|D-Sonido|GetSndFwd) _m))
  (Variables|Z-Vida|SetSndOffW (Math|Vector|MakeVector (* _cy _sf) (* _sy _sf) 0.0))
  (Variables|Z-Vida|SetSndMin -1000000.0)
  (Variables|Z-Vida|SetGustKind 0.0)
  (Variables|Z-Vida|SetE0 (neg (Variables|B-Rafagas|GetPathHalf)))
  (Variables|Z-Vida|SetE1 (Variables|B-Rafagas|GetPathHalf))
  (Variables|Z-Vida|SetRamp (Variables|B-Rafagas|GetGustRamp))
  (Variables|Z-Vida|SetGW (Variables|B-Rafagas|GetGustW))
  (Variables|Z-Vida|SetLf0 (Variables|B-Rafagas|GetFrontHalf0))
  (Variables|Z-Vida|SetLf1 (Variables|B-Rafagas|GetFrontHalf1))
  (Variables|Z-Vida|SetLife (Variables|B-Rafagas|GetGustLife))
  (CallFunction|VidaGo))

;; ===== GRAFO: VidaStartBreath  (funcion nueva, sin parametros)
;; SOLO la geometria del SOPLO: la rafaga sale del usuario hacia adelante (un solo aire: la exhalacion sigue como
;; viento por el valle).
(fn VidaStartBreath ()
  (bind _k (Variables|Z-Vida|GetGustIdx))
  (bind _ang (+ (.yaw (Transformation|GetActorRotation)) (* (Variables|C-Soplo|GetBreathJitter) (- (* 2.0 (Math|Float|Fraction (+ (* _k 0.4142136) 0.1))) 1.0))))
  (bind _loc (Transformation|GetActorLocation))
  (Variables|Z-Vida|SetDirW (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _ang) (Math|Trig|Sin(Degrees) _ang) 0.0))
  (Variables|Z-Vida|SetOrgW (Math|Vector|MakeVector (.x _loc) (.y _loc) 0.0))
  (Variables|Z-Vida|SetSndOffW (Math|Vector|MakeVector 0.0 0.0 0.0))
  (Variables|Z-Vida|SetSndMin 150.0)
  (Variables|Z-Vida|SetGustKind 1.0)
  (Variables|Z-Vida|SetE0 0.0)
  (Variables|Z-Vida|SetE1 (Variables|C-Soplo|GetBreathLen))
  (Variables|Z-Vida|SetRamp (Variables|C-Soplo|GetBreathRamp))
  (Variables|Z-Vida|SetGW (Variables|C-Soplo|GetBreathW))
  (Variables|Z-Vida|SetLf0 (Variables|C-Soplo|GetBreathHalf0))
  (Variables|Z-Vida|SetLf1 (Variables|C-Soplo|GetBreathHalf1))
  (Variables|Z-Vida|SetLife (Variables|C-Soplo|GetBreathLife))
  (CallFunction|VidaGo))

;; ===== GRAFO: VidaSnd  (funcion nueva; parametros de entrada Snd SoundBase (add_object_function_param), Pitch float)
;; NO se escribe con write_graph_dsl: los nodos de audio resuelven al homonimo de SynthComponent (BP_Sequencer_SC.md:
;; SetVolumeMultiplier aparece DOS veces en find_node_types y el write elige el de SynthComponent, "Could not connect
;; pin ... to self"). Se arma DIRECTAMENTE por cirugia (paso B12): 4 create_node con declaring_class
;; /Script/Engine.AudioComponent + CallFunction|VidaAudio. Este bloque es la ESPECIFICACION (el simulador lo ejecuta).
;; La fuente se ubica ANTES de sonar.
(fn VidaSnd (Snd Pitch)
  (Audio|Components|Audio|SetSound (Variables|Default|GetGustAudio) Snd)
  (Audio|Components|Audio|SetPitchMultiplier (Variables|Default|GetGustAudio) Pitch)
  (Audio|Components|Audio|SetVolumeMultiplier (Variables|Default|GetGustAudio) (Variables|D-Sonido|GetGustVolume))
  (CallFunction|VidaAudio)
  (Audio|Components|Audio|Play (Variables|Default|GetGustAudio) 0.0))

;; ===== GRAFO: VidaNoSnd  (funcion nueva, sin parametros)
(fn VidaNoSnd ()
  (if (not (Variables|Z-Vida|GetSndWarned))
    (Variables|Z-Vida|SetSndWarned true)
    (Development|PrintString "VIDA: la rafaga no tiene sonido (GustSounds / BreathSounds vacios)" :bPrintToScreen false)))

;; ===== GRAFO: VidaPlayG  (funcion nueva; parametro de entrada Pitch float)
(fn VidaPlayG (Pitch)
  (bind _n (Utilities|Array|Length (Variables|D-Sonido|GetGustSounds)))
  (if (> _n 0)
    (CallFunction|VidaSnd :Snd (Utilities|Array|Get(acopy) (Variables|D-Sonido|GetGustSounds) (Math|Integer|%(Integer) (Math|Float|Truncate (Variables|Z-Vida|GetGustIdx)) _n)) :Pitch Pitch)
    (else (CallFunction|VidaNoSnd))))

;; ===== GRAFO: VidaPlayB  (funcion nueva; parametro de entrada Pitch float)
(fn VidaPlayB (Pitch)
  (bind _n (Utilities|Array|Length (Variables|D-Sonido|GetBreathSounds)))
  (if (> _n 0)
    (CallFunction|VidaSnd :Snd (Utilities|Array|Get(acopy) (Variables|D-Sonido|GetBreathSounds) (Math|Integer|%(Integer) (Math|Float|Truncate (Variables|Z-Vida|GetGustIdx)) _n)) :Pitch Pitch)
    (else (CallFunction|VidaNoSnd))))

;; ===== GRAFO: VidaLaunchLat  (funcion nueva, sin parametros)
;; Geometria + sonido + indice. El sonido usa el indice ANTES de sumarlo (la variante = indice mod cantidad). El pitch
;; estira el soplo grabado (SndLen s) a la duracion de la rafaga, dentro de 0,75-1,33.
(fn VidaLaunchLat ()
  (CallFunction|VidaStartLat :Sign 0.0)
  (CallFunction|VidaPlayG :Pitch (Math|Float|Clamp(Float) (/ (Variables|D-Sonido|GetSndLen) (Math|Float|Max(Float) (Variables|B-Rafagas|GetGustLife) 1.0)) 0.75 1.33))
  (Variables|Z-Vida|SetGustIdx (+ (Variables|Z-Vida|GetGustIdx) 1.0)))

;; ===== GRAFO: VidaLaunchBreath  (funcion nueva, sin parametros)
(fn VidaLaunchBreath ()
  (CallFunction|VidaStartBreath)
  (CallFunction|VidaPlayB :Pitch (Math|Float|Clamp(Float) (/ (Variables|D-Sonido|GetBreathSndLen) (Math|Float|Max(Float) (Variables|C-Soplo|GetBreathLife) 1.0)) 0.75 1.33))
  (Variables|Z-Vida|SetGustIdx (+ (Variables|Z-Vida|GetGustIdx) 1.0)))

;; ===== GRAFO: VidaDue  (funcion nueva, sin parametros)
;; Toca rafaga. Una de cada BreathEvery (si se detecta la respiracion) espera un INICIO DE EXHALACION y sale del
;; usuario; si no llega en BreathWait s, sale una lateral. Las demas, y la pedida con 'ke * GustNow': lateral ya.
;; EDITOR 2026-09-29: el DSL admite UN solo elif por if (es la rama falsa y va ultima): el segundo nivel va en un
;; (else (if ...)) anidado (gotcha 490).
(fn VidaDue ()
  (bind _ev (Math|Float|Max(Float) (Variables|C-Soplo|GetBreathEvery) 1.0))
  (bind _quiere (and (and (and (Variables|C-Soplo|GetBreathGusts) (> (Variables|Z-Vida|GetVGate) 0.5)) (> (* _ev (Math|Float|Fraction (/ (Variables|Z-Vida|GetGustIdx) _ev))) (- _ev 1.5))) (not (Variables|Z-Vida|GetForce))))
  (if (not _quiere)
    (CallFunction|VidaLaunchLat)
    (else
      (if (Variables|Z-Vida|GetExhOnset)
        (CallFunction|VidaLaunchBreath)
        (elif (< (Variables|Z-Vida|GetWait) (neg (Variables|C-Soplo|GetBreathWait)))
          (CallFunction|VidaLaunchLat))))))

;; ===== GRAFO: VidaMaybe  (funcion nueva, sin parametros)
;; Sale una rafaga cuando: la deriva de la anterior ya volvio (Hold 0), se cumplio la calma (o la pidieron con GustNow),
;; la capa esta prendida (bVida y VidaAmount > 0: el boton de panico corta TAMBIEN las rafagas nuevas), bGusts (o la
;; pidieron) y no es el banco sin rafagas (PerfMode 3).
(fn VidaMaybe ()
  (bind _f (Variables|Z-Vida|GetForce))
  (bind _ok (and (and (and (<= (Variables|Z-Vida|GetHold) 0.0) (or (<= (Variables|Z-Vida|GetWait) 0.0) _f)) (and (Variables|A-Vida|GetVida) (> (Variables|A-Vida|GetVidaAmount) 0.0))) (and (or (Variables|B-Rafagas|GetGusts) _f) (!= (Variables|Z-Vida|GetPerfMode) 3))))
  (if _ok
    (CallFunction|VidaDue)))

;; ===== GRAFO: VidaEnd  (funcion nueva, sin parametros)
;; El frente termino: empieza la calma y la RELAJACION de la deriva (dura DriftRelax, o la calma si es mas corta: la
;; agenda nunca se atrasa). Amp sigue hasta que Hold llega a 0 (VidaRelaxStep): el polvo vuelve a su lugar sin salto.
(fn VidaEnd ()
  (if (>= (Variables|Z-Vida|GetFront) (Variables|Z-Vida|GetFront1))
    (Variables|Z-Vida|SetGusting false)
    (CallFunction|VidaGap)
    (Variables|Z-Vida|SetHoldRate (/ 1.0 (Math|Float|Max(Float) (Math|Float|Min(Float) (Variables|B-Rafagas|GetDriftRelax) (Variables|Z-Vida|GetWait)) 1.0)))
    (Variables|Z-Vida|SetHoldPh 0.0)))

;; ===== GRAFO: VidaRelaxStep  (funcion nueva; parametro de entrada DT float)
;; Hold = 1 - S5(fase), fase integrada (gotcha 329); con GustNow pendiente la fase corre a 1/3 por segundo como minimo
;; (sigue continua). Al llegar a 1: Hold 0 EXACTO y recien ahi Amp 0 (el polvo ya esta en su lugar).
(fn VidaRelaxStep (DT)
  (bind _r (select (Variables|Z-Vida|GetForce) (Math|Float|Max(Float) (Variables|Z-Vida|GetHoldRate) 0.33333333) (Variables|Z-Vida|GetHoldRate)))
  (Variables|Z-Vida|SetHoldPh (Math|Float|Min(Float) (+ (Variables|Z-Vida|GetHoldPh) (* _r DT)) 1.0))
  (bind _p (Variables|Z-Vida|GetHoldPh))
  (Variables|Z-Vida|SetHold (- 1.0 (* (* (* _p _p) _p) (+ (* _p (- (* 6.0 _p) 15.0)) 10.0))))
  (Variables|Z-Vida|SetHoldV (neg (* (* 30.0 (* (* _p _p) (* (- 1.0 _p) (- 1.0 _p)))) _r)))
  (if (>= (Variables|Z-Vida|GetHoldPh) 1.0)
    (Variables|Z-Vida|SetHold 0.0)
    (Variables|Z-Vida|SetHoldV 0.0)
    (Variables|Z-Vida|SetAmp 0.0)))

;; ===== GRAFO: VidaRelax  (funcion nueva; parametro de entrada DT float)
(fn VidaRelax (DT)
  (if (> (Variables|Z-Vida|GetHold) 0.0)
    (CallFunction|VidaRelaxStep :DT DT)))

;; ===== GRAFO: VidaSchedule  (funcion nueva; parametro de entrada DT float)
;; EL RELOJ DE RAFAGAS (uno solo: polvo, franja y sonido leen este estado). Con rafaga: el frente avanza (fase
;; integrada: nunca una velocidad en caliente, gotcha 329) hasta Front1; sin rafaga: cuenta la espera, relaja la
;; deriva y ve si toca otra.
(fn VidaSchedule (DT)
  (if (Variables|Z-Vida|GetGusting)
    (Variables|Z-Vida|SetFront (Math|Float|Min(Float) (+ (Variables|Z-Vida|GetFront) (* (Variables|Z-Vida|GetFrontV) DT)) (Variables|Z-Vida|GetFront1)))
    (CallFunction|VidaEnd)
    (else
      (Variables|Z-Vida|SetWait (- (Variables|Z-Vida|GetWait) DT))
      (CallFunction|VidaRelax :DT DT)
      (CallFunction|VidaMaybe))))

;; ===== GRAFO: VidaState  (funcion nueva; parametro de entrada DT float)
;; La actividad de la rafaga 2 m delante del usuario (ActUser) agita el meandro (ritmo integrado en Tm, envuelto en
;; 1800 s: el VS usa un numero entero de vueltas por ventana, sin salto); la presencia sigue a bVida x VidaAmount con
;; GlobTau (aparece y se va suave).
;; EDITOR 2026-09-29: el punto 2 m delante va por componentes (sin vector x float, gotcha 490).
(fn VidaState (DT)
  (bind _yaw (.yaw (Transformation|GetActorRotation)))
  (bind _loc (Transformation|GetActorLocation))
  (bind _o (Variables|Z-Vida|GetOrgW))
  (bind _d (Variables|Z-Vida|GetDirW))
  (bind _rx (- (+ (.x _loc) (* 200.0 (Math|Trig|Cos(Degrees) _yaw))) (.x _o)))
  (bind _ry (- (+ (.y _loc) (* 200.0 (Math|Trig|Sin(Degrees) _yaw))) (.y _o)))
  (bind _x (+ (* _rx (.x _d)) (* _ry (.y _d))))
  (bind _eta (Math|Float|Absolute(Float) (+ (* _rx (neg (.y _d))) (* _ry (.x _d)))))
  (bind _rp (Math|Float|Max(Float) (Variables|Z-Vida|GetRamp) 1.0))
  (bind _ta (Math|Float|Clamp(Float) (/ (- _x (Variables|Z-Vida|GetE0)) _rp) 0.0 1.0))
  (bind _tb (Math|Float|Clamp(Float) (/ (- _x (- (Variables|Z-Vida|GetE1) _rp)) _rp) 0.0 1.0))
  (bind _th (Math|Float|Clamp(Float) (/ (- _eta (Variables|Z-Vida|GetLf0)) (Math|Float|Max(Float) (- (Variables|Z-Vida|GetLf1) (Variables|Z-Vida|GetLf0)) 1.0)) 0.0 1.0))
  (bind _tu (Math|Float|Clamp(Float) (* (+ (/ (- (Variables|Z-Vida|GetFront) _x) (Math|Float|Max(Float) (Variables|Z-Vida|GetGW) 1.0)) 2.0) 0.25) 0.0 1.0))
  (bind _sa (* (* (* _ta _ta) _ta) (+ (* _ta (- (* 6.0 _ta) 15.0)) 10.0)))
  (bind _sb (* (* (* _tb _tb) _tb) (+ (* _tb (- (* 6.0 _tb) 15.0)) 10.0)))
  (bind _sh (* (* (* _th _th) _th) (+ (* _th (- (* 6.0 _th) 15.0)) 10.0)))
  (bind _bl (* 16.0 (* (* _tu _tu) (* (- 1.0 _tu) (- 1.0 _tu)))))
  (Variables|Z-Vida|SetActUser (* (* (* (Variables|Z-Vida|GetAmp) (* _sa (- 1.0 _sb))) (- 1.0 _sh)) _bl))
  (Variables|Z-Vida|SetRate (* (Variables|A-Vida|GetMeanderRate) (+ 1.0 (* (Variables|B-Rafagas|GetGustStir) (Variables|Z-Vida|GetActUser)))))
  (Variables|Z-Vida|SetTm (* (Math|Float|Fraction (/ (+ (Variables|Z-Vida|GetTm) (* (Variables|Z-Vida|GetRate) DT)) 1800.0)) 1800.0))
  (Variables|Z-Vida|SetGlobBase (+ (Variables|Z-Vida|GetGlobBase) (* (- (select (Variables|A-Vida|GetVida) (Variables|A-Vida|GetVidaAmount) 0.0) (Variables|Z-Vida|GetGlobBase)) (- 1.0 (Math|Float|Exp (neg (/ DT (Math|Float|Max(Float) (Variables|A-Vida|GetGlobTau) 0.0001))))))))
  (Variables|Z-Vida|SetGlob (Variables|Z-Vida|GetGlobBase)))

;; ===== GRAFO: VidaPerf  (funcion nueva, sin parametros)
;; Banco: PerfMode 2 = polvo pleno y la rafaga quieta en la mitad (s = 0); 1 = sin vida (el polvo se oculta en
;; VidaVisible y la franja se apaga: Amp 0); 3 = sin rafagas (PerfE0..E4: el polvo normal, Amp 0, ninguna nueva).
(fn VidaPerf ()
  (bind _pm (Variables|Z-Vida|GetPerfMode))
  (Variables|Z-Vida|SetGlob (select (== _pm 2) 1.0 (Variables|Z-Vida|GetGlob)))
  (Variables|Z-Vida|SetFront (select (and (== _pm 2) (Variables|Z-Vida|GetGusting)) 0.0 (Variables|Z-Vida|GetFront)))
  (Variables|Z-Vida|SetAmp (select (or (== _pm 1) (== _pm 3)) 0.0 (Variables|Z-Vida|GetAmp))))

;; ===== GRAFO: VidaPushSoul  (funcion nueva, sin parametros)
;; El disco del metaball queda sin polvo: centro y radio (SoulR x la escala del metaball, que crece al aparecer).
(fn VidaPushSoul ()
  (Utilities|IsValid (Variables|Z-Vida|GetBlob)
    (:"Is Valid"
      (bind _s (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Transformation|GetActorLocation (Variables|Z-Vida|GetBlob))))
      (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetDustMesh) "VidaSoul" (Math|Color|MakeColor (.x _s) (.y _s) (.z _s) (* (Variables|A-Vida|GetSoulR) (Math|Float|Clamp(Float) (.x (Transformation|GetActorScale3D (Variables|Z-Vida|GetBlob))) 0.0 1.0)))))
    (:"Is Not Valid"
      (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetDustMesh) "VidaSoul" (Math|Color|MakeColor 0.0 0.0 0.0 0.0)))))

;; ===== GRAFO: VidaNoCam  (funcion nueva, sin parametros)
;; Sin camara (editor, o el rig todavia sin CamRef): VidaC.w = 0 -> cada ojo usa su propia camara.
(fn VidaNoCam ()
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetDustMesh) "VidaC" (Math|Color|MakeColor 0.0 0.0 0.0 0.0)))

;; ===== GRAFO: VidaCamC  (funcion nueva, sin parametros)
;; El punto CICLOPEO = la camara del pawn que da el rig (el unico que conoce al pawn), en el espacio del actor. El alfa
;; de cada mota se decide desde aca: los dos ojos ven lo mismo (sin rivalidad binocular en el borde del metaball).
(fn VidaCamC ()
  (bind _cam (Class|BPBreathRigSC|GetCamRef (Variables|Z-Vida|GetRig)))
  (Utilities|IsValid _cam
    (:"Is Valid"
      (bind _c (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (.location (Transformation|GetWorldTransform _cam))))
      (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetDustMesh) "VidaC" (Math|Color|MakeColor (.x _c) (.y _c) (.z _c) 1.0)))
    (:"Is Not Valid"
      (CallFunction|VidaNoCam))))

;; ===== GRAFO: VidaCamRig  (funcion nueva, sin parametros)
(fn VidaCamRig ()
  (Utilities|IsValid (Variables|Z-Vida|GetRig)
    (:"Is Valid" (CallFunction|VidaCamC))
    (:"Is Not Valid" (CallFunction|VidaNoCam))))

;; ===== GRAFO: VidaPushCam  (funcion nueva; parametro de entrada Live float)
;; En el editor (Live 0) no hay camara del pawn: cada ojo usa la suya.
(fn VidaPushCam (Live)
  (if (> Live 0.5)
    (CallFunction|VidaCamRig)
    (else (CallFunction|VidaNoCam))))

;; ===== GRAFO: VidaPushDust  (funcion nueva; parametro de entrada Live float: 1 en juego, 0 en el editor)
;; Los 7 vectores del polvo, en el espacio del actor, en la MISMA funcion (gotcha 465). La trayectoria de la rafaga se
;; empuja por punto y direccion: s, e0, e1, W, Lf0, Lf1 valen igual en cualquier espacio (solo yaw).
(fn VidaPushDust (Live)
  (bind _m (Variables|Default|GetDustMesh))
  (bind _xf (Transformation|GetActorTransform))
  (bind _o (Math|Transform|InverseTransformLocation _xf (Math|Vector|MakeVector (.x (Variables|Z-Vida|GetOrgW)) (.y (Variables|Z-Vida|GetOrgW)) 0.0)))
  (bind _d (Math|Transform|InverseTransformDirection _xf (Math|Vector|MakeVector (.x (Variables|Z-Vida|GetDirW)) (.y (Variables|Z-Vida|GetDirW)) 0.0)))
  (Rendering|Material|SetColorParameterValueonMaterials _m "VidaT" (Math|Color|MakeColor (Variables|Z-Vida|GetTm) (Variables|Z-Vida|GetRate) (Variables|Z-Vida|GetGlob) Live))
  (Rendering|Material|SetColorParameterValueonMaterials _m "VidaG" (Math|Color|MakeColor (.x _o) (.y _o) (.x _d) (.y _d)))
  (Rendering|Material|SetColorParameterValueonMaterials _m "VidaS" (Math|Color|MakeColor (Variables|Z-Vida|GetFront) (Variables|Z-Vida|GetGW) (Variables|Z-Vida|GetFrontV) (Variables|Z-Vida|GetAmp)))
  (Rendering|Material|SetColorParameterValueonMaterials _m "VidaE" (Math|Color|MakeColor (Variables|Z-Vida|GetE0) (Variables|Z-Vida|GetE1) (Variables|Z-Vida|GetRamp) (Variables|Z-Vida|GetHold)))
  (Rendering|Material|SetColorParameterValueonMaterials _m "VidaF" (Math|Color|MakeColor (Variables|Z-Vida|GetLf0) (Variables|Z-Vida|GetLf1) (Variables|Z-Vida|GetHoldV) 0.0))
  (CallFunction|VidaPushCam :Live Live)
  (CallFunction|VidaPushSoul))

;; ===== GRAFO: VidaPushValley  (funcion nueva, sin parametros)
;; La franja de la rafaga en el llano: 5 vectores al Ground del valle (M_BreathValley_SC, GustLeanVS), en el espacio del
;; valle. Sin valle en el nivel no hace nada. GustK = 0 (sin rafaga, y en la relajacion: el frente ya paso) -> la rama
;; del Custom se saltea y devuelve el gradiente sin tocar.
;; EDITOR 2026-09-29: la inclinacion por componentes (sin vector x float, gotcha 490).
(fn VidaPushValley ()
  (Utilities|IsValid (Variables|Z-Vida|GetValley)
    (:"Is Valid"
      (bind _v (Variables|Z-Vida|GetValley))
      (bind _g (Class|BPBreathValleySC|GetGround _v))
      (bind _xf (Transformation|GetActorTransform _v))
      (bind _o (Math|Transform|InverseTransformLocation _xf (Math|Vector|MakeVector (.x (Variables|Z-Vida|GetOrgW)) (.y (Variables|Z-Vida|GetOrgW)) 0.0)))
      (bind _d (Math|Transform|InverseTransformDirection _xf (Math|Vector|MakeVector (.x (Variables|Z-Vida|GetDirW)) (.y (Variables|Z-Vida|GetDirW)) 0.0)))
      (bind _s (Math|Transform|InverseTransformLocation _xf (Transformation|GetActorLocation)))
      (bind _gl (Variables|B-Rafagas|GetGustLean))
      (bind _ln (Math|Transform|InverseTransformDirection _xf (Math|Vector|MakeVector (* _gl (Math|Trig|Cos(Degrees) (Variables|B-Rafagas|GetLeanAz))) (* _gl (Math|Trig|Sin(Degrees) (Variables|B-Rafagas|GetLeanAz))) 0.0)))
      (bind _a (select (Variables|Z-Vida|GetGusting) (Variables|Z-Vida|GetAmp) 0.0))
      (Rendering|Material|SetColorParameterValueonMaterials _g "GustP" (Math|Color|MakeColor (.x _o) (.y _o) (.x _d) (.y _d)))
      (Rendering|Material|SetColorParameterValueonMaterials _g "GustQ" (Math|Color|MakeColor (Variables|Z-Vida|GetFront) (Variables|Z-Vida|GetGW) (Variables|Z-Vida|GetE0) (Variables|Z-Vida|GetE1)))
      (Rendering|Material|SetColorParameterValueonMaterials _g "GustR" (Math|Color|MakeColor (Variables|Z-Vida|GetRamp) (Variables|Z-Vida|GetLf0) (Variables|Z-Vida|GetLf1) (Variables|B-Rafagas|GetGustNear)))
      (Rendering|Material|SetColorParameterValueonMaterials _g "GustK" (Math|Color|MakeColor (* _a (Variables|B-Rafagas|GetGustLight)) (* _a (.x _ln)) (* _a (.y _ln)) (* _a (Variables|B-Rafagas|GetGustRuffle))))
      (Rendering|Material|SetColorParameterValueonMaterials _g "GustS" (Math|Color|MakeColor (.x _s) (.y _s) 0.0 0.0)))
    (:"Is Not Valid")))

;; ===== GRAFO: VidaAudio  (funcion nueva, sin parametros)
;; La fuente del soplo viaja con el frente: lateral, por una linea paralela a la trayectoria a SndFwd delante (el
;; paneo va de un lado al otro); soplo, sobre la trayectoria desde 1,5 m (se aleja). A la altura de los oidos.
;; EDITOR 2026-09-29: por componentes (sin vector x float ni cadenas de + vectoriales, gotcha 490).
(fn VidaAudio ()
  (bind _o (Variables|Z-Vida|GetOrgW))
  (bind _q (Variables|Z-Vida|GetSndOffW))
  (bind _d (Variables|Z-Vida|GetDirW))
  (bind _f (Math|Float|Max(Float) (Variables|Z-Vida|GetFront) (Variables|Z-Vida|GetSndMin)))
  (Transformation|SetWorldLocation (Variables|Default|GetGustAudio) (Math|Vector|MakeVector (+ (+ (.x _o) (.x _q)) (* (.x _d) _f)) (+ (+ (.y _o) (.y _q)) (* (.y _d) _f)) (+ (+ (+ (.z _o) (.z _q)) (* (.z _d) _f)) (.z (Transformation|GetActorLocation))))))

;; ===== GRAFO: VidaVisible  (funcion nueva, sin parametros)
;; Sin presencia el polvo ni se dibuja (cero costo de vertices). PerfMode 1 = oculto.
(fn VidaVisible ()
  (bind _pm (Variables|Z-Vida|GetPerfMode))
  (Rendering|SetVisibility (Variables|Default|GetDustMesh) (and (!= _pm 1) (or (> (Variables|Z-Vida|GetGlob) 0.0005) (== _pm 2))) false))

;; ===== GRAFO: VidaFind  (funcion nueva, sin parametros)
;; El valle, el metaball y el rig del nivel (pueden no estar: todo lo que los usa pregunta IsValid). GetActorOfClass es
;; IMPURO: bind y despues Set. En la miniatura de save_assets devuelve None (gotcha 467): por eso los IsValid.
(fn VidaFind ()
  (bind _v (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC.BP_BreathValley_SC_C"))
  (Variables|Z-Vida|SetValley _v)
  (bind _b (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC_C"))
  (Variables|Z-Vida|SetBlob _b)
  (bind _r (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C"))
  (Variables|Z-Vida|SetRig _r))

;; ===== GRAFO: VidaAfterRig  (funcion nueva, sin parametros)
;; Tickear DESPUES del rig (como AirMountCam del aliento): VidaBreath lee MPC_Breath del MISMO cuadro (sin el cuadro de
;; retraso ni velocidades 0x/2x si el orden variara). Solo en BeginPlay (no en el Construction Script).
(fn VidaAfterRig ()
  (Utilities|IsValid (Variables|Z-Vida|GetRig)
    (:"Is Valid" (Actor|Tick|AddTickPrerequisiteActor :PrerequisiteActor (Variables|Z-Vida|GetRig)))))

;; ===== GRAFO: VidaZero  (funcion nueva, sin parametros)
;; El estado inicial (= VidaBP.reset del modelo).
(fn VidaZero ()
  (Variables|Z-Vida|SetClock 0.0)
  (Variables|Z-Vida|SetWait (Variables|B-Rafagas|GetFirstGap))
  (Variables|Z-Vida|SetGusting false)
  (Variables|Z-Vida|SetGustIdx 0.0)
  (Variables|Z-Vida|SetGustKind 0.0)
  (Variables|Z-Vida|SetFront 0.0)
  (Variables|Z-Vida|SetFront0 0.0)
  (Variables|Z-Vida|SetFront1 0.0)
  (Variables|Z-Vida|SetFrontV 0.0)
  (Variables|Z-Vida|SetGW 700.0)
  (Variables|Z-Vida|SetE0 0.0)
  (Variables|Z-Vida|SetE1 0.0)
  (Variables|Z-Vida|SetRamp 1000.0)
  (Variables|Z-Vida|SetLf0 3000.0)
  (Variables|Z-Vida|SetLf1 5500.0)
  (Variables|Z-Vida|SetLife 22.0)
  (Variables|Z-Vida|SetOrgW (Math|Vector|MakeVector 0.0 0.0 0.0))
  (Variables|Z-Vida|SetDirW (Math|Vector|MakeVector 0.0 1.0 0.0))
  (Variables|Z-Vida|SetSndOffW (Math|Vector|MakeVector 0.0 0.0 0.0))
  (Variables|Z-Vida|SetSndMin -1000000.0)
  (Variables|Z-Vida|SetAmp 0.0)
  (Variables|Z-Vida|SetHold 0.0)
  (Variables|Z-Vida|SetHoldPh 0.0)
  (Variables|Z-Vida|SetHoldV 0.0)
  (Variables|Z-Vida|SetHoldRate 1.0)
  (Variables|Z-Vida|SetForce false)
  (Variables|Z-Vida|SetTm 0.0)
  (Variables|Z-Vida|SetRate (Variables|A-Vida|GetMeanderRate))
  (Variables|Z-Vida|SetGlobBase 0.0)
  (Variables|Z-Vida|SetGlob 0.0)
  (Variables|Z-Vida|SetActUser 0.0)
  (Variables|Z-Vida|SetVSig 0.0)
  (Variables|Z-Vida|SetVGate 0.0)
  (Variables|Z-Vida|SetSprev 0.0)
  (Variables|Z-Vida|SetPrimed false)
  (Variables|Z-Vida|SetVel 0.0)
  (Variables|Z-Vida|SetVelF 0.0)
  (Variables|Z-Vida|SetFlow 0.0)
  (Variables|Z-Vida|SetInhHold 0.0)
  (Variables|Z-Vida|SetExhOnset false)
  (Variables|Z-Vida|SetPerfMode 0)
  (Variables|Z-Vida|SetSndWarned false))

;; ===== GRAFO: VidaReset  (funcion nueva, sin parametros)  -> BeginPlay
(fn VidaReset ()
  (CallFunction|VidaZero)
  (Collision|SetCollisionEnabled (Variables|Default|GetDustMesh) "NoCollision")
  (CallFunction|VidaFind)
  (CallFunction|VidaAfterRig)
  (CallFunction|VidaPushDust :Live 1.0)
  (CallFunction|VidaPushValley)
  (Rendering|SetVisibility (Variables|Default|GetDustMesh) false false))

;; ===== GRAFO: VidaTick  (funcion nueva; parametro de entrada DT float)
;; MPC -> soplo -> reloj de rafagas -> estado -> banco -> empujes (polvo, valle) -> sonido -> visibilidad.
(fn VidaTick (DT)
  (bind _dt (Math|Float|Max(Float) DT 0.0001))
  (Variables|Z-Vida|SetClock (+ (Variables|Z-Vida|GetClock) _dt))
  (CallFunction|VidaMPC)
  (CallFunction|VidaBreath :DT _dt)
  (CallFunction|VidaSchedule :DT _dt)
  (CallFunction|VidaState :DT _dt)
  (CallFunction|VidaPerf)
  (CallFunction|VidaPushDust :Live 1.0)
  (CallFunction|VidaPushValley)
  (CallFunction|VidaAudio)
  (CallFunction|VidaVisible))

;; ===== GRAFO: VidaPreGeo  (funcion nueva, sin parametros)
(fn VidaPreGeo ()
  (if (> (Variables|E-Prueba|GetPreviewKind) 0.5)
    (CallFunction|VidaStartBreath)
    (else (CallFunction|VidaStartLat :Sign (select (>= (Variables|E-Prueba|GetPreviewDir) 0.0) 1.0 -1.0)))))

;; ===== GRAFO: VidaPreview  (funcion nueva, sin parametros)  -> Construction Script
;; Sin Play: el polvo en calma (el meandro anima con el reloj del editor: Live 0) y, con PreviewGust > 0, una rafaga de
;; muestra CONGELADA en esa fraccion del camino (0,5 = pasando por el usuario), con la franja en el valle. Sin sonido.
(fn VidaPreview ()
  (CallFunction|VidaZero)
  (CallFunction|VidaFind)
  (CallFunction|VidaPreGeo)
  (bind _pg (Math|Float|Clamp(Float) (Variables|E-Prueba|GetPreviewGust) 0.0 1.0))
  (Variables|Z-Vida|SetFront (+ (Variables|Z-Vida|GetFront0) (* (- (Variables|Z-Vida|GetFront1) (Variables|Z-Vida|GetFront0)) _pg)))
  (Variables|Z-Vida|SetAmp (select (> _pg 0.0) (Variables|B-Rafagas|GetGustAmount) 0.0))
  (Variables|Z-Vida|SetRate (Variables|A-Vida|GetMeanderRate))
  (Variables|Z-Vida|SetTm 0.0)
  (Variables|Z-Vida|SetGlob (select (Variables|A-Vida|GetVida) (Variables|A-Vida|GetVidaAmount) 0.0))
  (CallFunction|VidaPushDust :Live 0.0)
  (CallFunction|VidaPushValley)
  (CallFunction|VidaVisible))

;; ===== GRAFO: VidaBenchFull  (funcion nueva, sin parametros)
(fn VidaBenchFull ()
  (Variables|Z-Vida|SetPerfMode 2)
  (if (not (Variables|Z-Vida|GetGusting))
    (CallFunction|VidaStartLat :Sign 1.0)))

;; ===== GRAFO: ConstructionScript  (el Construction Script del BP nuevo esta vacio: se escribe con fn ConstructionScript)
;; El sort tambien desde el BP (red de seguridad de la gotcha 478).
(fn ConstructionScript ()
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetDustMesh) 5)
  (CallFunction|VidaPreview))

;; ===== GRAFO: EventGraph  (BP nuevo: borrar ANTES los 3 eventos fantasma que trae el EventGraph)
;; Banco (quest_entering_perf.ps1 -Modos 0,4,5,6, sin eco propio: el aliento ya eco a): PerfE0..E4 = modo 3 (el polvo
;; normal y NINGUNA rafaga: FONDO = m0 - m4 sin la franja al azar), PerfE5 = vida llena, PerfE6 = sin vida (en esa
;; sesion "AIRE" = m5 - m6 pasa a ser AIRE + VIDA), PerfEEnd (el cierre del script) = normal otra vez. Para aislarla:
;; 'ke * PerfV0/1/2' a mano (ecos "VIDA PERF modo N"). 'ke * GustNow' lanza una lateral apenas se puede (si hay una en
;; curso, al terminar ella; acelera la relajacion; no espera el soplo); 'ke * VidaDbg' imprime una linea de estado.
(event Custom|PerfE0 ()
  (Variables|Z-Vida|SetPerfMode 3))
(event Custom|PerfE1 ()
  (Variables|Z-Vida|SetPerfMode 3))
(event Custom|PerfE2 ()
  (Variables|Z-Vida|SetPerfMode 3))
(event Custom|PerfE3 ()
  (Variables|Z-Vida|SetPerfMode 3))
(event Custom|PerfE4 ()
  (Variables|Z-Vida|SetPerfMode 3))
(event Custom|PerfE5 ()
  (CallFunction|VidaBenchFull))
(event Custom|PerfE6 ()
  (Variables|Z-Vida|SetPerfMode 1))
(event Custom|PerfEEnd ()
  (Variables|Z-Vida|SetPerfMode 0))
(event Custom|PerfV0 ()
  (Variables|Z-Vida|SetPerfMode 0)
  (Development|PrintString "VIDA PERF modo 0 (normal)" :bPrintToScreen false))
(event Custom|PerfV1 ()
  (Variables|Z-Vida|SetPerfMode 1)
  (Development|PrintString "VIDA PERF modo 1 (sin vida)" :bPrintToScreen false))
(event Custom|PerfV2 ()
  (CallFunction|VidaBenchFull)
  (Development|PrintString "VIDA PERF modo 2 (vida llena)" :bPrintToScreen false))
(event Custom|GustNow ()
  (Variables|Z-Vida|SetForce true))
(event Custom|VidaDbg ()
  (Development|PrintString (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append "VIDA DBG rafaga " (Utilities|String|ToString(Float) (Variables|Z-Vida|GetFront))) (Utilities|String|Append " act " (Utilities|String|ToString(Float) (Variables|Z-Vida|GetActUser)))) (Utilities|String|Append (Utilities|String|Append " espera " (Utilities|String|ToString(Float) (Variables|Z-Vida|GetWait))) (Utilities|String|Append " deriva " (Utilities|String|ToString(Float) (Variables|Z-Vida|GetHold))))) :bPrintToScreen false))
(event EventBeginPlay
  (CallFunction|VidaReset)
  (Development|PrintString "VIDA: lista (polvo + rafagas; valle y metaball si estan en el nivel)" :bPrintToScreen false))
(event EventTick (DeltaSeconds)
  (CallFunction|VidaTick :DT DeltaSeconds))
