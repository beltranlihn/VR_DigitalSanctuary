;; BP_FluidMedium_SC — EL VIAJE: "que el vr pawn y la neurona avancen; hazlo moviendo las partículas, para no mover el pawn.
;; Que se sienta que vamos avanzando" (Beltrán, 2026-09-30, prueba de la Obra, vía Narrativa).
;; Nada se mueve en la escena: el fluido suma una velocidad de VIAJE a su deriva integrada (Drift/DriftVel), que ya
;; trasladan TODAS sus capas por shader (motas cerca/medio/lejos, amebas medias, siluetas lejanas, velos). El fondo está en
;; el infinito (dirección de cámara) -> el horizonte NO se mueve. La célula y su polvo no se tocan (viajan "con nosotros").
;; Costo GPU: cero (misma deriva, otro valor). CPU: ~25 nodos por cuadro.
;;   TravelStep(DT): TravelU va hacia la meta (bTravel ? 1 : 0) a ritmo LINEAL: 1/TravelEase por segundo al SUBIR y
;;     1/TravelEaseOut al BAJAR; la velocidad es TravelSpeed x smootherstep(TravelU): entrada y salida en ease, aceleración
;;     máxima = 1,875 x TravelSpeed / ease (25 cm/s: 11,7 cm/s² al arrancar en 4 s, 23 cm/s² al frenar en 2 s, sin tirón).
;;     Condición de Narrativa (09-30): el frenado TERMINA dentro de la pausa del runner tras StageOutro (2,5 s) -> EaseOut 2 s.
;;     Dirección fija de autor (TravelYaw/TravelPitch en espacio local del fluido;
;;     180/0 = hacia -X = hacia el usuario que mira +X). DriftVel += TravelVel · Drift += TravelVel · dt (integrado: cambiar la
;;     velocidad nunca salta una posición). Paso = min(DT, 1/30).
;; Empalmes por cirugía (no re-escribir grafos existentes):
;;   EventGraph Tick:        FluidStep -> TravelStep(DeltaSeconds) -> UpdateHead ...
;;   EventGraph BeginPlay:   FluidStep -> TravelBegin() -> UpdateHead ...   (TravelU = 0: arranca en reposo y entra en ease;
;;                           el CS dejó TravelU = 1 para la vista previa y PIE copia las propiedades del editor)
;;   ConstructionScript:     FluidStep -> TravelPreview() -> ApplyLayers ...   (vista previa en el editor SIEMPRE a TravelSpeed,
;;                           con bTravel o sin él: Live 0 usa DriftVel x T; así se ajusta la velocidad mirando el viewport)
;;   BP_LovingCell_SC: función NUEVA FluidTravel(On) (IsValid(Fluid) -> setter de bTravel), agregada al FINAL de la cadena de:
;;     TourWake (false) · TourSleep (false) · StageBegin (true) · StageOutro (false). FluidHands no se toca.
;;   => en la Obra: quieto mientras la etapa espera (TourWake), avanza desde StageBegin, frena en ease de 2 s AL EMPEZAR el
;;      outro (la pausa del runner es 2,5 s; el velo cierra mucho después: carga + despedida de Alma).
;;      bTravel queda FALSE en la instancia: lo prende SOLO el contrato (si la Obra no llamara TourWake, igual nada se mueve antes de Begin).
;; <GETTRAVEL>/<SETTRAVEL>: type_id del getter/setter de bTravel, resueltos en el turno con find_node_types (el DSL le quita la
;;   "b" a los bool: GetFakeEEG, SetHandStir).
;; Variables nuevas: 7-Viaje bTravel (false; lo maneja la célula) · TravelSpeed (25 cm/s) · TravelEase (4 s)
;;   · TravelEaseOut (2 s)
;;   · TravelYaw (180) · TravelPitch (0) · Z-Interno TravelU (float) · TravelVel (vector).

;; ===== GRAFO: TravelStep
(fn TravelStep (DT)
  (bind _dt (Math|Float|Min(Float) DT 0.0333333))
  (bind _goal (select (<GETTRAVEL>) 1.0 0.0))
  (bind _rate (/ _dt (Math|Float|Max(Float) (select (> _goal (Variables|Z-Interno|GetTravelU)) (Variables|7-Viaje|GetTravelEase) (Variables|7-Viaje|GetTravelEaseOut)) 0.1)))
  (Variables|Z-Interno|SetTravelU (Math|Float|Clamp(Float) (+ (Variables|Z-Interno|GetTravelU) (Math|Float|Clamp(Float) (- _goal (Variables|Z-Interno|GetTravelU)) (neg _rate) _rate)) 0.0 1.0))
  (bind _u (Variables|Z-Interno|GetTravelU))
  (bind _k (* (* (* _u _u) _u) (+ (* _u (- (* 6.0 _u) 15.0)) 10.0)))
  (bind _yaw (Math|Trig|DegreesToRadians (Variables|7-Viaje|GetTravelYaw)))
  (bind _pit (Math|Trig|DegreesToRadians (Variables|7-Viaje|GetTravelPitch)))
  (bind _cp (Math|Trig|Cos(Radians) _pit))
  (Variables|Z-Interno|SetTravelVel (* (Math|Vector|MakeVector (* _cp (Math|Trig|Cos(Radians) _yaw)) (* _cp (Math|Trig|Sin(Radians) _yaw)) (Math|Trig|Sin(Radians) _pit)) (* (Math|Float|Max(Float) (Variables|7-Viaje|GetTravelSpeed) 0.0) _k)))
  (Variables|Z-Interno|SetDriftVel (+ (Variables|Z-Interno|GetDriftVel) (Variables|Z-Interno|GetTravelVel)))
  (Variables|Z-Interno|SetDrift (+ (Variables|Z-Interno|GetDrift) (* (Variables|Z-Interno|GetTravelVel) _dt))))

;; ===== GRAFO: TravelBegin
(fn TravelBegin ()
  (Variables|Z-Interno|SetTravelU 0.0)
  (CallFunction|TravelStep :DT 0.0))

;; ===== GRAFO: TravelPreview
(fn TravelPreview ()
  (Variables|Z-Interno|SetTravelU 1.0)
  (CallFunction|TravelStep :DT 0.0))

;; ===== GRAFO: FluidTravel
;; (BP_LovingCell_SC)
(fn FluidTravel (On)
  (Utilities|IsValid (Variables|9-Etapa|GetFluid)
    (:"Is Valid" (<SETTRAVEL> :self (Variables|9-Etapa|GetFluid) :bTravel On))))
