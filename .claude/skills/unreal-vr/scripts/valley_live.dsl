;; valley_live.dsl - la CAPA VIVA de BP_BreathValley_SC (la bruma, el resplandor y la sombra respiran). 2026-09-28, rev. 2.
;; Plan: docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md (seccion 6 y receta del editor, pasos V1-V14).
;; Es la traduccion 1:1 de valley_model.live_desde_S() y live_paso(). scripts/dsl_sim.py EJECUTA este archivo:
;;     python dsl_sim.py valle     -> tiene que decir TODO OK antes de pegar nada en Unreal.
;;
;; SOLO FUNCIONES NUEVAS (el EventGraph y el Construction Script del valle EXISTEN: no se re-escriben, regla de oro 2).
;; Despues de escribir estas funciones, dos cirugias de UN nodo cada una (pasos V10 y V11 del plan):
;;   - EventGraph, Tick: un nodo CallFunction|StepLive despues de StepShadow.
;;   - Construction Script: un nodo CallFunction|PreviewLive AL FINAL de la cadena (hoy: despues de ApplyLook, que otra
;;     sesion agrego el 2026-09-28 16:00 despues de PushShadow). Los parametros que escriben son disjuntos: el orden no
;;     cambia el resultado.
;; Variables nuevas, categoria L-Respira (sin espacios, gotcha 466), NINGUNA instance-editable: asi la instancia colocada
;; toma el valor del CDO y NO hay que tocar Entering_Valle (la puso Beltran). OJO: las perillas de LOOK del valle (36,
;; de ApplyLook) SI son instance-editable; las de la capa viva se ajustan en el CDO.
;; Los Live* los lee el material por preshader (Mul / Mix / Tint): con S = 0 todos quedan neutros y el valle es la v2
;; exacta. Material sobre componente: Set...ParameterValueonMaterials con "on" MINUSCULA (gotcha 2258).
;; Al CIELO van solo los 3 Live* que su rama usa (LiveWarm, LiveGlowAmt, LiveGlowPow); al SUELO los 9.

;; ===== GRAFO: LiveMPC  (funcion nueva, sin parametros)
;; PUENTE a MPC_Breath, igual que AirMPC (gotcha 291): esqueleto con los dos Set; despues dos create_node
;; 'Rendering|Material|GetScalarParameterValue' con declaring_class /Script/Engine.KismetMaterialLibrary
;; (Collection = MPC_Breath; ParameterName "Signed" y "On") conectados a los pines de valor (paso V9).
(fn LiveMPC ()
  (Variables|L-Respira|SetLiveSig 0.0)
  (Variables|L-Respira|SetLiveGate 0.0))

;; ===== GRAFO: PushLive  (funcion nueva; parametro de entrada S float)
;; m(S) = 1 + g * S * lerp(-Out, In, smoothstep((S + 1) / 2)). Tabla de In / Out en el plan (seccion 6.2).
;; Ground y Sky en la MISMA funcion y el MISMO cuadro: la niebla del suelo usa los Sky*/Glow* (costura, gotcha 465).
;; La sombra: Soft y Strength lineales (-5 % / +12 % al inhalar): densa al inhalar, abierta al exhalar, contornos quietos.
(fn PushLive (S)
  (bind _t (Math|Float|Clamp(Float) (* (+ S 1.0) 0.5) 0.0 1.0))
  (bind _u (* (* _t _t) (- 3.0 (* 2.0 _t))))
  (bind _gf (* S (Variables|L-Respira|GetFogBreath)))
  (bind _gg (* S (Variables|L-Respira|GetGlowBreath)))
  (bind _gs (* S (Variables|L-Respira|GetShadowBreath)))
  (bind _neg (Math|Float|Clamp(Float) (neg S) 0.0 1.0))
  (bind _fog (+ 1.0 (* _gf (Math|Float|Lerp 0.15 0.2 _u))))
  (bind _fall (+ 1.0 (* _gf (Math|Float|Lerp -0.35 -0.1 _u))))
  (bind _glow (+ 1.0 (* _gg (Math|Float|Lerp 0.25 0.15 _u))))
  (bind _ss (+ 1.0 (* _gs -0.05)))
  (bind _st (+ 1.0 (* _gs 0.12)))
  (bind _warm (* (* 0.25 (Variables|L-Respira|GetWarmBreath)) _neg))
  (bind _swarm (* (* 0.35 (Variables|L-Respira|GetShadowBreath)) _neg))
  (bind _g (Variables|Default|GetGround))
  (bind _k (Variables|Default|GetSky))
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveFogDist" _fog)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveHFogDist" _fog)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveHFogFall" _fall)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveWarm" _warm)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveGlowAmt" _glow)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveGlowPow" _glow)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveShadowSoft" _ss)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveShadowStrength" _st)
  (Rendering|Material|SetScalarParameterValueonMaterials _g "LiveShadowWarm" _swarm)
  (Rendering|Material|SetScalarParameterValueonMaterials _k "LiveWarm" _warm)
  (Rendering|Material|SetScalarParameterValueonMaterials _k "LiveGlowAmt" _glow)
  (Rendering|Material|SetScalarParameterValueonMaterials _k "LiveGlowPow" _glow))

;; ===== GRAFO: StepLive  (funcion nueva, sin parametros)  -> Tick, despues de StepShadow
;; S = Signed x clamp(On x LiveAmount), SEGUIDA con LiveTau (el Retire del rig manda Signed y On a 0 en UN cuadro: sin el
;; filtro el horizonte saltaria). Sin respiracion detectada (On 0) el valle vuelve solo, suave, a lo autoral.
;; El DT sale de GetWorldDeltaSeconds (VERIFICAR el type_id, paso V7): asi la cirugia del Tick es un solo nodo de exec.
(fn StepLive ()
  (CallFunction|LiveMPC)
  (bind _on (Math|Float|Clamp(Float) (* (Variables|L-Respira|GetLiveGate) (Variables|L-Respira|GetLiveAmount)) 0.0 1.0))
  (bind _tgt (select (Variables|L-Respira|GetLive) (* (Math|Float|Clamp(Float) (Variables|L-Respira|GetLiveSig) -1.0 1.0) _on) 0.0))
  (bind _dt (Math|Float|Max(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0001))
  (Variables|L-Respira|SetLiveS (+ (Variables|L-Respira|GetLiveS) (* (- _tgt (Variables|L-Respira|GetLiveS)) (- 1.0 (Math|Float|Exp (neg (/ _dt (Math|Float|Max(Float) (Variables|L-Respira|GetLiveTau) 0.01))))))))
  (CallFunction|PushLive :S (Variables|L-Respira|GetLiveS)))

;; ===== GRAFO: PreviewLive  (funcion nueva, sin parametros)  -> Construction Script, al final
;; Sin Play: PreviewBreath (CDO; -1 exhalado .. +1 inhalado), SIN filtro. 0 = empuja los neutros = el look tal cual.
(fn PreviewLive ()
  (Variables|L-Respira|SetLiveS (select (Variables|L-Respira|GetLive) (* (Math|Float|Clamp(Float) (Variables|L-Respira|GetPreviewBreath) -1.0 1.0) (Math|Float|Clamp(Float) (Variables|L-Respira|GetLiveAmount) 0.0 1.0)) 0.0))
  (CallFunction|PushLive :S (Variables|L-Respira|GetLiveS)))
