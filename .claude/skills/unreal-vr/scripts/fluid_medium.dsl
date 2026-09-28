;; BP_FluidMedium_SC (2026-09-28) — plan: docs/PLAN-FLUIDO-CEREBRAL.md. Funciones escritas enteras (grafos nuevos).
;; Llamadas a funciones propias SIEMPRE con argumentos por nombre (trampa del DSL). El nodo de la MPC es el de
;; coleccion (gotcha 407: el DSL resuelve SetVectorParameterValue a la version de coleccion).

;; FluidStep (DT Snap): la UNICA entrada es el EEG (0 activo, 1 calma, como GlobalState de la celula).
;; Suavizado exponencial (EEGSmoothing = constante de tiempo en s), perillas moduladas (Eff*), rumbo de la
;; corriente con cambio lento (Meander), y las INTEGRALES: arrastre (Drift) y fases (FlowPhase, CausticPhase).
;; Port de frame() del prototipo docs/prototipos/fluido-cerebral.html. CausticPhase se envuelve en 20 pi (la
;; caustica tiene ese periodo exacto): en half nunca pierde precision.
(fn FluidStep (DT Snap)
  (Variables|Z-Interno|SetClock (+ (Variables|Z-Interno|GetClock) DT))
  (bind _tg (select (Variables|0-EEG|GetFakeEEG) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (/ (* 6.2831853 (Variables|Z-Interno|GetClock)) (Math|Float|Max(Float) (Variables|0-EEG|GetFakePeriod) 1.0))))) (Variables|0-EEG|GetEEG)))
  (Variables|Z-Interno|SetEEGS (select Snap _tg (+ (Variables|Z-Interno|GetEEGS) (* (- _tg (Variables|Z-Interno|GetEEGS)) (- 1.0 (Math|Float|Exp (/ (neg DT) (Math|Float|Max(Float) (Variables|0-EEG|GetEEGSmoothing) 0.05))))))))
  (bind _c (Math|Float|Clamp(Float) (Variables|Z-Interno|GetEEGS) 0.0 1.0))
  (bind _a (- 1.0 _c))
  (bind _kf (Variables|0-EEG|GetEEGFlow))
  (bind _kc (Variables|0-EEG|GetEEGClarity))
  (Variables|Z-Interno|SetEffFlowSpeed (* (Variables|1-Movimiento|GetFlowSpeed) (+ 1.0 (* _kf (- (* 0.8 _a) (* 0.5 _c))))))
  (Variables|Z-Interno|SetEffTurb (* (Variables|1-Movimiento|GetTurbulence) (+ 1.0 (* _kf (- (* 0.6 _a) (* 0.7 _c))))))
  (Variables|Z-Interno|SetEffFlowAmp (* (Variables|1-Movimiento|GetFlowAmp) (+ 1.0 (* _kf (- (* 0.25 _a) (* 0.3 _c))))))
  (Variables|Z-Interno|SetEffCurrent (* (Variables|1-Movimiento|GetCurrentSpeed) (+ 1.0 (* _kf (- (* 0.4 _a) (* 0.4 _c))))))
  (Variables|Z-Interno|SetEffStreak (* (Variables|1-Movimiento|GetStreakTime) (+ 1.0 (* _kf (- (* 0.3 _a) (* 0.4 _c))))))
  (Variables|Z-Interno|SetEffAbsorb (* (Variables|2-Liquido|GetAbsorbDist) (+ 1.0 (* _kc (- (* 0.8 _c) (* 0.2 _a))))))
  (bind _t (Variables|Z-Interno|GetClock))
  (bind _yaw (Math|Trig|DegreesToRadians (+ (Variables|1-Movimiento|GetCurrentYaw) (/ (* (Variables|1-Movimiento|GetMeander) (+ (Math|Trig|Sin(Radians) (* _t 0.017)) (* 0.5 (Math|Trig|Sin(Radians) (+ (* _t 0.041) 1.0))))) 1.5))))
  (bind _pit (Math|Trig|DegreesToRadians (+ (Variables|1-Movimiento|GetCurrentPitch) (* (* 0.35 (Variables|1-Movimiento|GetMeander)) (Math|Trig|Sin(Radians) (+ (* _t 0.023) 2.0))))))
  (bind _cp (Math|Trig|Cos(Radians) _pit))
  (Variables|Z-Interno|SetDriftVel (* (Math|Vector|MakeVector (* _cp (Math|Trig|Cos(Radians) _yaw)) (* _cp (Math|Trig|Sin(Radians) _yaw)) (Math|Trig|Sin(Radians) _pit)) (Variables|Z-Interno|GetEffCurrent)))
  (Variables|Z-Interno|SetDrift (+ (Variables|Z-Interno|GetDrift) (* (Variables|Z-Interno|GetDriftVel) DT)))
  (Variables|Z-Interno|SetFlowPhase (+ (Variables|Z-Interno|GetFlowPhase) (* DT (Variables|Z-Interno|GetEffFlowSpeed))))
  (Variables|Z-Interno|SetCausticPhase (Math|Float|%(Float) (+ (Variables|Z-Interno|GetCausticPhase) (* DT (Variables|5-Luz|GetCausticSpeed))) 62.831853)))

;; UpdateHead (Live): la cabeza en espacio LOCAL del actor = centro de los cubos de particulas (igual para los
;; dos ojos). En juego: la camara del jugador. En el editor (Construction Script) no hay camara: el usuario
;; sentado en el origen, ojos a 120 cm.
(fn UpdateHead (Live)
  (if Live
    (Variables|Z-Interno|SetHeadL (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))))
    (else (Variables|Z-Interno|SetHeadL (Math|Vector|MakeVector 0.0 0.0 120.0)))))

;; PushFluid (Live): publica TODO en MPC_Fluid_SC (una escritura por vector). Live = 1 en juego (fases
;; integradas); 0 en el editor: el material usa su propio reloj con las velocidades (anima sin Play).
(fn PushFluid (Live)
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "FTop" :ParameterValue (Variables|2-Liquido|GetFluidTop))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "FMid" :ParameterValue (Variables|2-Liquido|GetFluidMid))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "FBot" :ParameterValue (Variables|2-Liquido|GetFluidBottom))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Glow" :ParameterValue (Math|Color|NewOpacity(LinearColor) (Variables|2-Liquido|GetGlowColor) (Variables|2-Liquido|GetGlowAmount)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Absorb" :ParameterValue (Math|Color|MakeColor (Variables|Z-Interno|GetEffAbsorb) (Variables|2-Liquido|GetAbsorbMax) (Variables|2-Liquido|GetAbsorbAlpha) (Variables|2-Liquido|GetGlowPower)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Caus" :ParameterValue (Math|Color|MakeColor (Variables|5-Luz|GetCausticAmount) (Variables|5-Luz|GetCausticScale) (Variables|5-Luz|GetCausticSpeed) (Variables|5-Luz|GetMoteSparkle)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Phase" :ParameterValue (Math|Color|MakeColor (Variables|Z-Interno|GetFlowPhase) (Variables|Z-Interno|GetCausticPhase) (Variables|Z-Interno|GetEffFlowSpeed) (select Live 1.0 0.0)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Flow" :ParameterValue (Math|Color|MakeColor (Variables|Z-Interno|GetEffFlowAmp) (Variables|1-Movimiento|GetFlowScale) 0.0 (Variables|Z-Interno|GetEffTurb)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Drift" :ParameterValue (Math|Color|MakeColor (.x (Variables|Z-Interno|GetDrift)) (.y (Variables|Z-Interno|GetDrift)) (.z (Variables|Z-Interno|GetDrift)) 0.0))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "DriftVel" :ParameterValue (Math|Color|MakeColor (.x (Variables|Z-Interno|GetDriftVel)) (.y (Variables|Z-Interno|GetDriftVel)) (.z (Variables|Z-Interno|GetDriftVel)) 0.0))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Head" :ParameterValue (Math|Color|MakeColor (.x (Variables|Z-Interno|GetHeadL)) (.y (Variables|Z-Interno|GetHeadL)) (.z (Variables|Z-Interno|GetHeadL)) 0.0))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "StirK" :ParameterValue (Math|Color|MakeColor (Variables|6-Manos|GetStirSwirl) (Variables|Z-Interno|GetEffStreak) 0.0 0.0))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Mote" :ParameterValue (Math|Color|NewOpacity(LinearColor) (Variables|3-Particulas|GetMoteColor) (Variables|3-Particulas|GetMoteBright))))

;; ApplyLayers (): parametros fijos de cada capa (MID por componente) + orden de dibujo como red de
;; seguridad (gotcha 478: una instancia colocada puede no heredar la plantilla del componente).
(fn ApplyLayers ()
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesNear) "LayerA" (Math|Color|MakeColor 360.0 (* 0.45 (Variables|3-Particulas|GetNearSize)) (Variables|3-Particulas|GetNearSize) (Variables|3-Particulas|GetNearAlpha)))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesNear) "LayerB" (Math|Color|MakeColor 12.0 26.0 (Variables|3-Particulas|GetBokehDist) (Variables|3-Particulas|GetBokeh)))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesMid) "LayerA" (Math|Color|MakeColor 1200.0 (* 0.45 (Variables|3-Particulas|GetMidSize)) (Variables|3-Particulas|GetMidSize) (Variables|3-Particulas|GetMidAlpha)))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesMid) "LayerB" (Math|Color|MakeColor 40.0 110.0 0.0 0.0))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesFar) "LayerA" (Math|Color|MakeColor 4000.0 (* 0.45 (Variables|3-Particulas|GetFarSize)) (Variables|3-Particulas|GetFarSize) (Variables|3-Particulas|GetFarAlpha)))
  (Rendering|Material|SetColorParameterValueonMaterials (Variables|Default|GetMotesFar) "LayerB" (Math|Color|MakeColor 250.0 600.0 0.0 0.0))
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetMotesFar) -9)
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetMotesMid) -8)
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetMotesNear) 50))

(fn ConstructionScript ()
  (CallFunction|FluidStep :DT 0.0 :Snap true)
  (CallFunction|ApplyLayers)
  (CallFunction|UpdateHead :Live false)
  (CallFunction|PushFluid :Live false)
  (CallFunction|PushCells))

(event EventBeginPlay
  (CallFunction|FluidStep :DT 0.0 :Snap true)
  (CallFunction|ApplyLayers)
  (CallFunction|UpdateHead :Live true)
  (CallFunction|PushFluid :Live true)
  (CallFunction|PushCells)
  (CallFunction|ApplyVisibility))

(event EventTick (DeltaSeconds)
  (CallFunction|FluidStep :DT DeltaSeconds :Snap false)
  (CallFunction|UpdateHead :Live true)
  (CallFunction|PushFluid :Live true)
  (CallFunction|PushCells))

;; ---- F2/F3 (2026-09-28): celulas, haces, velos ----
;; PushCells (): las perillas de F2/F3 a MPC_Fluid_SC (CellHigh/CellLow/CellFill/FarA/Light/Extras) + el orden de
;; dibujo de velos y haces. Corre en el Construction Script, en BeginPlay Y EN TICK (revisión INT-3: en PIE/VR
;; Preview el CS no se vuelve a correr al editar una perilla; son 6 escrituras por cuadro, lo mismo que PushFluid).
;; La visibilidad NO va aquí: ApplyVisibility, solo en BeginPlay (revisión INT-5).
;;   CellLow.a = contraste · FarA = (cubo 70 m, tamano lejanas, remolinos, cuantas de 64)
;;   Extras = (VeilAmount, ShaftAmount, MidCellCount, MidCellScale) · Light = (direccion de la luz -la de Loving-, MidCellRange)
;; Orden de dibujo del fluido (revisión INT-1): todo en NEGATIVO salvo las motas cercanas, para no pasar por
;; delante de las manos y del HUD (sort 0): velos -12 · haces -11 · motas lejanas -9 · medias -8 (ApplyLayers) ·
;; célula de Loving 4-40 · motas cercanas 50 (necesitan que manos y HUD pasen a 100: Core/, coordinar).
(fn PushCells ()
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellHigh" :ParameterValue (Math|Color|NewOpacity(LinearColor) (Variables|4-Celulas|GetCellHigh) 1.0))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellLow" :ParameterValue (Math|Color|NewOpacity(LinearColor) (Variables|4-Celulas|GetCellLow) (Variables|4-Celulas|GetCellContrast)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellFill" :ParameterValue (Variables|4-Celulas|GetCellFill))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "FarA" :ParameterValue (Math|Color|MakeColor 7000.0 (Variables|4-Celulas|GetFarCellSize) (Variables|4-Celulas|GetCellFlow) (Variables|4-Celulas|GetFarCellCount)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Light" :ParameterValue (Math|Color|MakeColor (.x (Variables|4-Celulas|GetCellLight)) (.y (Variables|4-Celulas|GetCellLight)) (.z (Variables|4-Celulas|GetCellLight)) (Variables|4-Celulas|GetMidCellRange)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Extras" :ParameterValue (Math|Color|MakeColor (Variables|5-Luz|GetVeilAmount) (Variables|5-Luz|GetShaftAmount) (Variables|4-Celulas|GetMidCellCount) (Variables|4-Celulas|GetMidCellScale)))
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetVeils) -12)
  (Rendering|SetTranslucentSortPriority (Variables|Default|GetShafts) -11))

;; ApplyVisibility (): capas en cero = componente OCULTO (costo cero en vértices Y píxeles: A/B exacto para medir).
;; Corre SOLO en BeginPlay (revisión INT-5): un SetVisibility desde el Construction Script se graba como
;; override de la instancia y deja el viewport trabado; en el editor alcanza con el área cero que ya dan los
;; shaders. Las motas no tenían interruptor (alfa 0 seguía pagando el VS entero, revisión INT-6).
(fn ApplyVisibility ()
  (Rendering|SetVisibility (Variables|Default|GetMidCells) (> (Variables|4-Celulas|GetMidCellCount) 0.5))
  (Rendering|SetVisibility (Variables|Default|GetFarCells) (> (Variables|4-Celulas|GetFarCellCount) 0.5))
  (Rendering|SetVisibility (Variables|Default|GetShafts) (> (Variables|5-Luz|GetShaftAmount) 0.0))
  (Rendering|SetVisibility (Variables|Default|GetVeils) (> (Variables|5-Luz|GetVeilAmount) 0.0))
  (Rendering|SetVisibility (Variables|Default|GetMotesNear) (> (Variables|3-Particulas|GetNearAlpha) 0.0))
  (Rendering|SetVisibility (Variables|Default|GetMotesMid) (> (Variables|3-Particulas|GetMidAlpha) 0.0))
  (Rendering|SetVisibility (Variables|Default|GetMotesFar) (> (Variables|3-Particulas|GetFarAlpha) 0.0)))
