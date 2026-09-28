;; breath_air.dsl - los grafos de BP_BreathAir_SC (el ALIENTO VISIBLE de Entering). 2026-09-28, rev. 2.
;; Plan: docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md (seccion 11, receta del editor, pasos E1-E14).
;; Es la traduccion 1:1 de breath_air_model.AirBP (step / push / preview_push). scripts/dsl_sim.py EJECUTA este archivo
;; (con la semantica de los nodos puros: un bind se re-evalua en cada uso) y lo compara con el modelo:
;;     python dsl_sim.py aire      -> tiene que decir TODO OK antes de pegar nada en Unreal.
;;
;; COMO SE PEGA: un write_graph_dsl POR GRAFO, en el orden de las secciones. Cada bloque va entre las lineas
;; ";; ===== GRAFO: <nombre>" y se copia SIN los comentarios de cabecera. BP NUEVO: todos los grafos son nuevos o
;; vacios (regla de oro 2: nunca re-escribir un grafo existente). Antes de escribir:
;;   - las funciones con parametros ya creadas: add_function_graph + add_function_param (AirStep DT, AirTick DT);
;;   - las variables creadas y el BP compilado (tablas 5.4 y 5.5 del plan);
;;   - los type_id marcados VERIFICAR confirmados con find_node_types (lista en el plan, paso E9).
;; Categorias SIN espacios (A-Aliento, B-Prueba, Z-Aliento): con espacios el DSL no puede escribirlas (gotcha 466).
;; Bools: el getter/setter va SIN la b (bAir -> GetAir, bMounted -> GetMounted; gotcha 475).
;; Llamadas a funciones propias con argumentos: por KEYWORD (:DT DT), nunca posicional (gotchas 461, 654).
;; Funciones IMPURAS (GetActorOfClass, CallFunction|...) NUNCA inline como argumento de datos: primero un bind y despues
;; se usa el bind (gotcha "UNA FUNCION IMPURA INLINE COMO ARGUMENTO DE DATOS": el pin queda desconectado sin error).
;; Material sobre componente: Set{Scalar,Vector,Color}ParameterValueonMaterials con "on" MINUSCULA (gotcha 2258; la
;; "On" mayuscula que imprime el read NO es escribible).

;; ===== GRAFO: AirMPC  (funcion nueva, sin parametros)
;; PUENTE a MPC_Breath. El DSL agarra el GetScalarParameterValue de MID (gotcha 291): este cuerpo es solo el
;; esqueleto con los dos Set; despues, por cirugia, dos create_node 'Rendering|Material|GetScalarParameterValue' con
;; declaring_class /Script/Engine.KismetMaterialLibrary (Collection = MPC_Breath, ParameterName "Signed" / "On") y se
;; conectan sus ReturnValue a los pines de valor de los dos Set (paso E11 del plan). En dsl_sim.py lo reemplaza el MPC.
(fn AirMPC ()
  (Variables|Z-Aliento|SetAirSig 0.0)
  (Variables|Z-Aliento|SetAirGate 0.0))

;; ===== GRAFO: PushAir  (funcion nueva, sin parametros)
;; Los 8 vectores del cuadro, en local de la camara (= local de AirMesh). UNA funcion, el MISMO cuadro (gotcha 465).
;; La transform se guarda UNA vez en CamXf (un bind de GetWorldTransform se re-evaluaria en cada uso).
(fn PushAir ()
  (bind _mesh (Variables|Default|GetAirMesh))
  (Variables|Z-Aliento|SetCamXf (Transformation|GetWorldTransform _mesh))
  (bind _xf (Variables|Z-Aliento|GetCamXf))
  (bind _pa (Math|Float|Clamp(Float) (* (Variables|A-Aliento|GetPitchFollow) (Variables|Z-Aliento|GetPitchLag)) (Variables|A-Aliento|GetPitchMin) (Variables|A-Aliento|GetPitchMax)))
  (bind _r (Math|Rotator|MakeRotator :Roll 0.0 :Pitch _pa :Yaw (Variables|Z-Aliento|GetYawLag)))
  (Rendering|Material|SetColorParameterValueonMaterials _mesh "AirT" (Math|Color|MakeColor (Variables|Z-Aliento|GetTin) (Variables|Z-Aliento|GetTout) (Variables|Z-Aliento|GetFout) (Variables|Z-Aliento|GetGlob)))
  (Rendering|Material|SetColorParameterValueonMaterials _mesh "AirE" (Math|Color|MakeColor (Variables|Z-Aliento|GetEin) (Variables|Z-Aliento|GetEout) (Variables|Z-Aliento|GetInRate) (Variables|Z-Aliento|GetOutRate)))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "MouthL" (Math|Vector|MakeVector (Variables|A-Aliento|GetMouthFwd) 0.0 (neg (Variables|A-Aliento|GetMouthDown))))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "LagM" (Math|Transform|InverseTransformLocation _xf (Variables|Z-Aliento|GetMouthW)))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "LagA" (Math|Transform|InverseTransformDirection _xf (Math|Vector|GetForwardVector _r)))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "LagR" (Math|Transform|InverseTransformDirection _xf (Math|Vector|GetRightVector _r)))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "LagU" (Math|Transform|InverseTransformDirection _xf (Math|Vector|GetUpVector _r)))
  (Rendering|Material|SetVectorParameterValueonMaterials _mesh "UpL" (Math|Transform|InverseTransformDirection _xf (Math|Vector|MakeVector 0.0 0.0 1.0))))

;; ===== GRAFO: AirReset  (funcion nueva, sin parametros)  -> BeginPlay
(fn AirReset ()
  (Variables|Z-Aliento|SetTin 0.0)
  (Variables|Z-Aliento|SetTout 0.0)
  (Variables|Z-Aliento|SetFout 0.0)
  (Variables|Z-Aliento|SetEin 0.0)
  (Variables|Z-Aliento|SetEout 0.0)
  (Variables|Z-Aliento|SetInRate 0.0)
  (Variables|Z-Aliento|SetOutRate 0.0)
  (Variables|Z-Aliento|SetVel 0.0)
  (Variables|Z-Aliento|SetVelF 0.0)
  (Variables|Z-Aliento|SetFlow 0.0)
  (Variables|Z-Aliento|SetInhHold 0.0)
  (Variables|Z-Aliento|SetPrimed false)
  (Variables|Z-Aliento|SetClock 0.0)
  (Variables|Z-Aliento|SetOnset false)
  (Variables|Z-Aliento|SetLastOnset -1.0)
  (Variables|Z-Aliento|SetRateBpm 6.0)
  (Variables|Z-Aliento|SetRateCalm 1.0)
  (Variables|Z-Aliento|SetLagInit false)
  (Variables|Z-Aliento|SetTurnRate 0.0)
  (Variables|Z-Aliento|SetMoveFade 1.0)
  (Variables|Z-Aliento|SetGlobBase 0.0)
  (Variables|Z-Aliento|SetGlob 0.0)
  (Variables|Z-Aliento|SetMounted false)
  (Variables|Z-Aliento|SetPerfMode 0)
  (CallFunction|PushAir)
  (Rendering|SetVisibility (Variables|Default|GetAirMesh) false false)
  ;; gotchas 239 y 358: lo que viaja pegado a la camara, sin colision (tambien en la plantilla); la cabeza de
  ;; referencia es solo para la vista previa del editor
  (Collision|SetCollisionEnabled (Variables|Default|GetAirMesh) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetHeadGhost) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetMouthGhost) "NoCollision")
  (Development|SetHiddeninGame (Variables|Default|GetHeadGhost) true false)
  (Development|SetHiddeninGame (Variables|Default|GetMouthGhost) true false))

;; ===== GRAFO: AirStep  (funcion nueva; parametro de entrada DT float)
;; = AirBP.step del modelo. ORDEN IMPORTA: cada valor que se usa despues de pisar la variable que lo produce se
;; guarda primero en su propia variable (un bind de un nodo puro se re-evalua en cada uso).
(fn AirStep (DT)
  (bind _dt (Math|Float|Max(Float) DT 0.0001))
  ;; 1. velocidad = dS/dt de MPC_Breath.Signed, con tope (un escalon de Signed -el Retire del rig- no dispara la
  ;;    cinta) y SOLO con respiracion detectada (On > 0,05); despues un pasabajos VelTau
  (Variables|Z-Aliento|SetVel (Math|Float|Clamp(Float) (select (and (Variables|Z-Aliento|GetPrimed) (> (Variables|Z-Aliento|GetAirGate) 0.05)) (/ (- (Variables|Z-Aliento|GetAirSig) (Variables|Z-Aliento|GetSprev)) _dt) 0.0) (neg (Variables|A-Aliento|GetVelMax)) (Variables|A-Aliento|GetVelMax)))
  (Variables|Z-Aliento|SetSprev (Variables|Z-Aliento|GetAirSig))
  (Variables|Z-Aliento|SetPrimed true)
  (Variables|Z-Aliento|SetClock (+ (Variables|Z-Aliento|GetClock) _dt))
  (Variables|Z-Aliento|SetVelF (+ (Variables|Z-Aliento|GetVelF) (* (- (Variables|Z-Aliento|GetVel) (Variables|Z-Aliento|GetVelF)) (- 1.0 (Math|Float|Exp (neg (/ _dt (Variables|A-Aliento|GetVelTau))))))))
  (bind _vf (Variables|Z-Aliento|GetVelF))
  ;; 2. modo con HISTERESIS (+1 inhala, -1 exhala, 0 quieto): entra con |vf| > VelEnter, sigue mientras |vf| > VelStay.
  ;;    _new lee el modo VIEJO: se usa SOLO antes de SetFlow.
  (bind _old (Variables|Z-Aliento|GetFlow))
  (bind _new (select (> _old 0.5) (select (> _vf (Variables|A-Aliento|GetVelStay)) 1.0 0.0) (select (< _old -0.5) (select (< _vf (neg (Variables|A-Aliento|GetVelStay))) -1.0 0.0) (select (> _vf (Variables|A-Aliento|GetVelEnter)) 1.0 (select (< _vf (neg (Variables|A-Aliento|GetVelEnter))) -1.0 0.0)))))
  ;; 3. ritmo: un inicio de exhalacion cuenta SOLO si antes hubo una inhalacion sostenida (latch InhMin)
  (Variables|Z-Aliento|SetOnset (and (and (< _new -0.5) (> _old -0.5)) (>= (Variables|Z-Aliento|GetInhHold) (Variables|A-Aliento|GetInhMin))))
  (Variables|Z-Aliento|SetPer (- (Variables|Z-Aliento|GetClock) (Variables|Z-Aliento|GetLastOnset)))
  (bind _ok (and (and (Variables|Z-Aliento|GetOnset) (>= (Variables|Z-Aliento|GetLastOnset) 0.0)) (and (> (Variables|Z-Aliento|GetPer) 2.0) (< (Variables|Z-Aliento|GetPer) 30.0))))
  (Variables|Z-Aliento|SetRateBpm (select _ok (+ (Variables|Z-Aliento|GetRateBpm) (* (- (/ 60.0 (Math|Float|Max(Float) (Variables|Z-Aliento|GetPer) 0.01)) (Variables|Z-Aliento|GetRateBpm)) 0.5)) (Variables|Z-Aliento|GetRateBpm)))
  (Variables|Z-Aliento|SetLastOnset (select (Variables|Z-Aliento|GetOnset) (Variables|Z-Aliento|GetClock) (Variables|Z-Aliento|GetLastOnset)))
  (Variables|Z-Aliento|SetInhHold (select (Variables|Z-Aliento|GetOnset) 0.0 (select (> _new 0.5) (+ (Variables|Z-Aliento|GetInhHold) _dt) (select (< (Variables|Z-Aliento|GetInhHold) (Variables|A-Aliento|GetInhMin)) 0.0 (Variables|Z-Aliento|GetInhHold)))))
  (Variables|Z-Aliento|SetFlow _new)
  (bind _inh (> (Variables|Z-Aliento|GetFlow) 0.5))
  (bind _exh (< (Variables|Z-Aliento|GetFlow) -0.5))
  (bind _rt (Math|Float|Clamp(Float) (/ (- (Variables|Z-Aliento|GetRateBpm) (Variables|A-Aliento|GetCalmRate)) (Math|Float|Max(Float) (- (Variables|A-Aliento|GetFastRate) (Variables|A-Aliento|GetCalmRate)) 0.01)) 0.0 1.0))
  (Variables|Z-Aliento|SetRateCalm (+ (Variables|A-Aliento|GetFastFloor) (* (- 1.0 (Variables|A-Aliento|GetFastFloor)) (- 1.0 (* (* _rt _rt) (- 3.0 (* 2.0 _rt)))))))
  ;; 4. transporte integrado SOLO en su modo (gotcha 329): en las pausas la cinta no avanza
  (Variables|Z-Aliento|SetInRate (select _inh (* (* 0.5 (Variables|A-Aliento|GetInTravel)) (Math|Float|Max(Float) _vf 0.0)) 0.0))
  (Variables|Z-Aliento|SetOutRate (select _exh (* (* 0.5 (Variables|A-Aliento|GetOutTravel)) (Math|Float|Max(Float) (neg _vf) 0.0)) 0.0))
  (Variables|Z-Aliento|SetTin (Math|Float|Fraction (+ (Variables|Z-Aliento|GetTin) (* (Variables|Z-Aliento|GetInRate) _dt))))
  (Variables|Z-Aliento|SetTout (Math|Float|Fraction (+ (Variables|Z-Aliento|GetTout) (* (Variables|Z-Aliento|GetOutRate) _dt))))
  (Variables|Z-Aliento|SetFout (Math|Float|Min(Float) (+ (Variables|Z-Aliento|GetFout) (* (* (Variables|A-Aliento|GetFrontLead) (Variables|Z-Aliento|GetOutRate)) _dt)) 1.5))
  ;; 5. envolventes: sube la corriente activa; se cruza rapido; SUSPENDIDA en las pausas
  (bind _tauI (select _inh (Variables|A-Aliento|GetRiseTau) (select _exh (Variables|A-Aliento|GetCrossTau) (Variables|A-Aliento|GetHoldTau))))
  (bind _tauO (select _exh (Variables|A-Aliento|GetRiseTau) (select _inh (Variables|A-Aliento|GetCrossTau) (Variables|A-Aliento|GetHoldTau))))
  (Variables|Z-Aliento|SetEin (+ (Variables|Z-Aliento|GetEin) (* (- (select _inh 1.0 0.0) (Variables|Z-Aliento|GetEin)) (- 1.0 (Math|Float|Exp (neg (/ _dt _tauI)))))))
  (Variables|Z-Aliento|SetEout (+ (Variables|Z-Aliento|GetEout) (* (- (select _exh 1.0 0.0) (Variables|Z-Aliento|GetEout)) (- 1.0 (Math|Float|Exp (neg (/ _dt _tauO)))))))
  (Variables|Z-Aliento|SetFout (select (and (< (Variables|Z-Aliento|GetEout) 0.01) (not _exh)) 0.0 (Variables|Z-Aliento|GetFout)))
  ;; 6. marco del aire con retardo (MUNDO) + giro de la cabeza. La cabeza = la transform de AirMesh (en juego cuelga
  ;;    de la camara). _k usa MoveFade VIEJO: por eso los Set del marco van ANTES de SetMoveFade (misma cuenta que el
  ;;    modelo, que calcula k una vez al principio).
  (Variables|Z-Aliento|SetCamXf (Transformation|GetWorldTransform (Variables|Default|GetAirMesh)))
  (bind _xf (Variables|Z-Aliento|GetCamXf))
  (bind _rot (.rotation _xf))
  (bind _M (Math|Transform|TransformLocation _xf (Math|Vector|MakeVector (Variables|A-Aliento|GetMouthFwd) 0.0 (neg (Variables|A-Aliento|GetMouthDown)))))
  (bind _init (Variables|Z-Aliento|GetLagInit))
  (bind _still (not (or _inh _exh)))
  (bind _catch (+ (Variables|A-Aliento|GetTurnCatch) (* (- 1.0 (Variables|A-Aliento|GetTurnCatch)) (Variables|Z-Aliento|GetMoveFade))))
  (bind _k (- 1.0 (Math|Float|Exp (neg (/ _dt (* (* (Variables|A-Aliento|GetLagRot) (select _still (Variables|A-Aliento|GetHoldLagMul) 1.0)) _catch))))))
  (bind _dyh (Math|Rotator|NormalizeAxis (- (.yaw _rot) (Variables|Z-Aliento|GetYawPrev))))
  (bind _dph (- (.pitch _rot) (Variables|Z-Aliento|GetPitchPrev)))
  (bind _dyl (* (Math|Rotator|NormalizeAxis (- (.yaw _rot) (Variables|Z-Aliento|GetYawLag))) _k))
  (bind _dpl (* (* (Variables|A-Aliento|GetPitchFollow) (- (.pitch _rot) (Variables|Z-Aliento|GetPitchLag))) _k))
  (Variables|Z-Aliento|SetTurnRate (select _init (/ (Math|Float|Max(Float) (Math|Float|Max(Float) (Math|Float|Max(Float) _dyh (neg _dyh)) (Math|Float|Max(Float) _dph (neg _dph))) (Math|Float|Max(Float) (Math|Float|Max(Float) _dyl (neg _dyl)) (Math|Float|Max(Float) _dpl (neg _dpl)))) _dt) 0.0))
  (Variables|Z-Aliento|SetMouthW (select _init (+ (Variables|Z-Aliento|GetMouthW) (* (- _M (Variables|Z-Aliento|GetMouthW)) (- 1.0 (Math|Float|Exp (neg (/ _dt (Variables|A-Aliento|GetLagPos))))))) _M))
  (Variables|Z-Aliento|SetYawLag (select _init (Math|Rotator|NormalizeAxis (+ (Variables|Z-Aliento|GetYawLag) (* (Math|Rotator|NormalizeAxis (- (.yaw _rot) (Variables|Z-Aliento|GetYawLag))) _k))) (.yaw _rot)))
  (Variables|Z-Aliento|SetPitchLag (select _init (+ (Variables|Z-Aliento|GetPitchLag) (* (- (.pitch _rot) (Variables|Z-Aliento|GetPitchLag)) _k)) (.pitch _rot)))
  ;; apagado por giro: baja EN EL MISMO CUADRO y vuelve con TurnBack
  (bind _tt (Math|Float|Clamp(Float) (/ (- (Variables|Z-Aliento|GetTurnRate) (Variables|A-Aliento|GetTurnFade0)) (Math|Float|Max(Float) (- (Variables|A-Aliento|GetTurnFade1) (Variables|A-Aliento|GetTurnFade0)) 0.01)) 0.0 1.0))
  (bind _ft (- 1.0 (* (* _tt _tt) (- 3.0 (* 2.0 _tt)))))
  (Variables|Z-Aliento|SetMoveFade (select (< _ft (Variables|Z-Aliento|GetMoveFade)) _ft (+ (Variables|Z-Aliento|GetMoveFade) (* (- _ft (Variables|Z-Aliento|GetMoveFade)) (- 1.0 (Math|Float|Exp (neg (/ _dt (Variables|A-Aliento|GetTurnBack)))))))))
  (Variables|Z-Aliento|SetYawPrev (.yaw _rot))
  (Variables|Z-Aliento|SetPitchPrev (.pitch _rot))
  (Variables|Z-Aliento|SetLagInit true)
  ;; 7. presencia: deteccion (On) x perilla x ritmo x montado, SUAVIZADA (GlobTau), x el apagado por giro
  (Variables|Z-Aliento|SetGlobBase (+ (Variables|Z-Aliento|GetGlobBase) (* (- (* (* (* (Math|Float|Clamp(Float) (Variables|Z-Aliento|GetAirGate) 0.0 1.0) (select (Variables|A-Aliento|GetAir) (Variables|A-Aliento|GetAirAmount) 0.0)) (Variables|Z-Aliento|GetRateCalm)) (select (Variables|Z-Aliento|GetMounted) 1.0 0.0)) (Variables|Z-Aliento|GetGlobBase)) (- 1.0 (Math|Float|Exp (neg (/ _dt (Variables|A-Aliento|GetGlobTau))))))))
  (Variables|Z-Aliento|SetGlob (* (Variables|Z-Aliento|GetGlobBase) (Variables|Z-Aliento|GetMoveFade))))

;; ===== GRAFO: AirPerf  (funcion nueva, sin parametros)
;; Banco: PerfMode 2 = las dos corrientes llenas y quietas (la carga mas alta: nada colapsa salvo lo que tapa el confort).
(fn AirPerf ()
  (bind _f (== (Variables|Z-Aliento|GetPerfMode) 2))
  (Variables|Z-Aliento|SetGlob (select _f 1.0 (Variables|Z-Aliento|GetGlob)))
  (Variables|Z-Aliento|SetEin (select _f 1.0 (Variables|Z-Aliento|GetEin)))
  (Variables|Z-Aliento|SetEout (select _f 1.0 (Variables|Z-Aliento|GetEout)))
  (Variables|Z-Aliento|SetFout (select _f 1.5 (Variables|Z-Aliento|GetFout))))

;; ===== GRAFO: AirVisible  (funcion nueva, sin parametros)
;; Sin aire (Glob 0) el componente ni se dibuja: cero costo de vertices. PerfMode 1 = oculto (el A/B del banco).
(fn AirVisible ()
  (bind _pm (Variables|Z-Aliento|GetPerfMode))
  (Rendering|SetVisibility (Variables|Default|GetAirMesh) (and (!= _pm 1) (or (> (Variables|Z-Aliento|GetGlob) 0.0005) (== _pm 2))) false))

;; ===== GRAFO: AirMountCam  (funcion nueva, sin parametros)
;; La camara la da el RIG (el unico que conoce al pawn). SnapToTarget: el local de AirMesh pasa a ser el de la camara.
;; VERIFICAR type_id: Transformation|AttachComponentToComponent (target = AirMesh; mirar el pin self con
;; get_node_infos, gotcha 2522) y Actor|Tick|AddTickPrerequisiteActor (el aire tickea DESPUES del rig: lee el MPC de
;; este cuadro).
(fn AirMountCam ()
  (bind _cam (Class|BPBreathRigSC|GetCamRef (Variables|Z-Aliento|GetRig)))
  (Utilities|IsValid _cam
    (:"Is Valid"
      (Transformation|AttachComponentToComponent (Variables|Default|GetAirMesh) _cam :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "SnapToTarget")
      (Actor|Tick|AddTickPrerequisiteActor :PrerequisiteActor (Variables|Z-Aliento|GetRig))
      (Variables|Z-Aliento|SetLagInit false)
      (Variables|Z-Aliento|SetMounted true)
      (Development|PrintString "AIRE: montado en la camara del pawn (CamRef de BP_BreathRig_SC)"))))

;; ===== GRAFO: AirMount  (funcion nueva, sin parametros)
;; GetActorOfClass es IMPURO: bind primero, Set despues (nunca inline en el Set: el pin quedaria desconectado).
(fn AirMount ()
  (bind _found (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C"))
  (Variables|Z-Aliento|SetRig _found)
  (Utilities|IsValid (Variables|Z-Aliento|GetRig)
    (:"Is Valid" (CallFunction|AirMountCam))))

;; ===== GRAFO: AirTick  (funcion nueva; parametro de entrada DT float)
(fn AirTick (DT)
  (CallFunction|AirMPC)
  (CallFunction|AirStep :DT DT)
  (CallFunction|AirPerf)
  (CallFunction|PushAir)
  (CallFunction|AirVisible)
  (if (not (Variables|Z-Aliento|GetMounted)) (CallFunction|AirMount)))

;; ===== GRAFO: PreviewAir  (funcion nueva, sin parametros)  -> Construction Script
;; Sin Play: la cabeza es el actor colocado (a la altura de los ojos del usuario sentado). PreviewBreath > 0 = inhalar,
;; < 0 = la pluma, 0 = NADA (neutro). PreviewAirT arrastra la cinta.
(fn PreviewAir ()
  (bind _pb (Math|Float|Clamp(Float) (Variables|B-Prueba|GetPreviewBreath) -1.0 1.0))
  (bind _t (Variables|B-Prueba|GetPreviewAirT))
  (Variables|Z-Aliento|SetTin _t)
  (Variables|Z-Aliento|SetTout _t)
  (Variables|Z-Aliento|SetFout 1.5)
  (Variables|Z-Aliento|SetEin (Math|Float|Max(Float) _pb 0.0))
  (Variables|Z-Aliento|SetEout (Math|Float|Max(Float) (neg _pb) 0.0))
  (Variables|Z-Aliento|SetInRate 0.0)
  (Variables|Z-Aliento|SetOutRate 0.0)
  (Variables|Z-Aliento|SetGlob (select (Variables|A-Aliento|GetAir) (Variables|A-Aliento|GetAirAmount) 0.0))
  (Variables|Z-Aliento|SetCamXf (Transformation|GetWorldTransform (Variables|Default|GetAirMesh)))
  (bind _xf (Variables|Z-Aliento|GetCamXf))
  (Variables|Z-Aliento|SetMouthW (Math|Transform|TransformLocation _xf (Math|Vector|MakeVector (Variables|A-Aliento|GetMouthFwd) 0.0 (neg (Variables|A-Aliento|GetMouthDown)))))
  (Variables|Z-Aliento|SetYawLag (.yaw (.rotation _xf)))
  (Variables|Z-Aliento|SetPitchLag (.pitch (.rotation _xf)))
  (CallFunction|PushAir))

;; ===== GRAFO: ConstructionScript  (el Construction Script del BP nuevo esta vacio: se escribe con fn ConstructionScript)
;; El sort tambien desde el BP (red de seguridad de la gotcha 478).
(fn ConstructionScript ()
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetAirMesh) 20)
  (CallFunction|PreviewAir))

;; ===== GRAFO: EventGraph  (BP nuevo: borrar ANTES los 3 eventos fantasma que trae el EventGraph; los Custom primero)
;; Banco: los MISMOS nombres y ecos que BP_PerfEntering_SC ('ke * PerfEN' -> "PERF: entering modo N"), asi
;; scripts/quest_entering_perf.ps1 -Modos 0,4,5,6 mide el fondo y el aire en una sesion: aire = m5 - m6. PerfMode
;; interno: 0 normal · 1 oculto · 2 lleno. PerfE1..E4 (los modos del metaball, el pacer y el fondo) devuelven el aire a
;; normal SIN eco propio. BP_PerfEntering_SC NO tiene PerfE5/PerfE6: en las fases 5 y 6 el fondo queda como lo dejo el
;; modo anterior (en la ida y vuelta 0 4 5 6 6 5 4 0, OCULTO): el aire se mide sin el valle detras.
(event Custom|PerfE0 ()
  (Variables|Z-Aliento|SetPerfMode 0)
  (Development|PrintString "PERF: entering modo 0 (aire normal)"))
(event Custom|PerfE1 ()
  (Variables|Z-Aliento|SetPerfMode 0))
(event Custom|PerfE2 ()
  (Variables|Z-Aliento|SetPerfMode 0))
(event Custom|PerfE3 ()
  (Variables|Z-Aliento|SetPerfMode 0))
(event Custom|PerfE4 ()
  (Variables|Z-Aliento|SetPerfMode 0))
(event Custom|PerfE5 ()
  (Variables|Z-Aliento|SetPerfMode 2)
  (Development|PrintString "PERF: entering modo 5 (aire lleno)"))
(event Custom|PerfE6 ()
  (Variables|Z-Aliento|SetPerfMode 1)
  (Development|PrintString "PERF: entering modo 6 (sin aire)"))
;; Medir el ruido REAL de la senal en el visor (paso S3 del plan): cada 'ke * AirDbg' imprime UNA linea con la velocidad
;; filtrada, el modo y la senal. Con el usuario reteniendo el aire, std(v) de esas lineas decide VelEnter (>= 3 x std).
(event Custom|AirDbg ()
  (Development|PrintString (Utilities|String|Append (Utilities|String|Append (Utilities|String|Append "AIRE DBG v " (Utilities|String|ToString(Float) (Variables|Z-Aliento|GetVelF))) (Utilities|String|Append " modo " (Utilities|String|ToString(Float) (Variables|Z-Aliento|GetFlow)))) (Utilities|String|Append " S " (Utilities|String|ToString(Float) (Variables|Z-Aliento|GetAirSig))))))
(event EventBeginPlay
  (CallFunction|AirReset)
  (Development|PrintString "AIRE: listo, espera la camara de BP_BreathRig_SC"))
(event EventTick (DeltaSeconds)
  (CallFunction|AirTick :DT DeltaSeconds))
