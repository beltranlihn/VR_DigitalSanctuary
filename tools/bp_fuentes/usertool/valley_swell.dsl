;; valley_swell.dsl - BP_BreathValley_SC: la ondulacion de las lomas se acelera al EXHALAR (pedido de Beltran 2026-09-30:
;; "las lomas siempre ondulando; al exhalar mas rapido; en los otros pasos vuelve a su velocidad normal").
;; La velocidad NO se cambia en vivo (SwellSpeed/MorphSpeed multiplican al tiempo: saltaria la fase). Se integra un tiempo
;; EXTRA: SwellOfs += dt * (SwellK - 1), y el material usa Tt = View.GameTime + SwellTimeOfs.
;;   v      = d(LiveSig)/dt, filtrada 0,3 s (LiveSig = MPC_Breath.Signed, lo lee StepLive este cuadro)
;;   k*     = 1 + (ExhaleSwell - 1) * clamp(-v / SwellVelRef) * clamp(LiveGate)      (exhalar = Signed baja)
;;   SwellK sigue a k* en SwellFollow s (sube y vuelve suave), paso limitado a 1/30 s (regla de la obra)
;; ORDEN: SwellVel se calcula ANTES de pisar SwellSigPrev (un bind se re-evaluaria con el valor nuevo).

;; ===== GRAFO: StepSwell   (param DT float) -- en el Tick, despues de StepLive
(fn StepSwell (DT)
  (bind _dt (Math|Float|Min(Float) DT 0.0333))
  ;; guarda: en una instancia ya colocada la variable nueva nace en 0 (gotcha 518); SwellK 0 haria correr el tiempo al reves
  (Variables|Default|SetSwellK (select (<= (Variables|Default|GetSwellK) 0.0) 1.0 (Variables|Default|GetSwellK)))
  (Variables|Default|SetSwellVel (+ (Variables|Default|GetSwellVel) (* (- (/ (- (Variables|L-Respira|GetLiveSig) (Variables|Default|GetSwellSigPrev)) (Math|Float|Max(Float) _dt 0.0001)) (Variables|Default|GetSwellVel)) (Math|Float|Min(Float) (/ _dt 0.3) 1.0))))
  (Variables|Default|SetSwellSigPrev (Variables|L-Respira|GetLiveSig))
  (Variables|Default|SetSwellK (+ (Variables|Default|GetSwellK) (* (- (+ 1.0 (* (- (Variables|Default|GetExhaleSwell) 1.0) (* (Math|Float|Clamp(Float) (/ (neg (Variables|Default|GetSwellVel)) (Math|Float|Max(Float) (Variables|Default|GetSwellVelRef) 0.01))) (Math|Float|Clamp(Float) (Variables|L-Respira|GetLiveGate))))) (Variables|Default|GetSwellK)) (Math|Float|Min(Float) (/ _dt (Math|Float|Max(Float) (Variables|Default|GetSwellFollow) 0.01)) 1.0))))
  (Variables|Default|SetSwellOfs (+ (Variables|Default|GetSwellOfs) (* _dt (- (Variables|Default|GetSwellK) 1.0))))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetGround) "SwellTimeOfs" (Variables|Default|GetSwellOfs)))
