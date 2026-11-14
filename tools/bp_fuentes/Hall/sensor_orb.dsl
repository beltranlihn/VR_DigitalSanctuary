;; sensor_orb.dsl — BP_SensorOrb_SC (Mechanics/Hall). Pedido directo de Beltrán 2026-09-30: el mando que se toma por primera
;; vez flota y GIRA dentro de un ORBE transparente ("da la sensación de que hay que tomarlo"); al tomarlo, el orbe
;; ESTALLA sutil. NO toca al director: lee director.bSensorLive y director.Sensor (el BP_BioSensorArt_SC que spawnea);
;; lo único que hace sobre el sensor es girarlo en Z mientras espera. Sin TestOnly (va en la Obra).
;; Componente: Orb (SM_AlmaSphere r 50 → escala OrbSize; MI_SensorOrb_SC = M_Alma en blanco azulado, sin deriva:
;; burbuja con Fresnel y deformación suave en el shader; Beltrán la ajusta mirando la MI).
;; Variables: Director (BP_HallDirector_SC) · Amount · Burst (float) · bWasLive (bool) · editables: SpinDeg 20 ·
;; OrbSize 0,28 · AppearTime 0,8 · BurstTime 0,45 · BurstGrow 0,7 · OrbOpacityCore 0,06 · OrbOpacityRim 0,55 ·
;; BurstSound (SoundBase, ProtoSelect a 0,5).
;; Funciones (add_function_graph + params ANTES de escribir): OrbLive (DT float, S BP_BioSensorArt_SC) · OrbBurst (DT) · OrbPop ().

;; ===== GRAFO: EventGraph
(event EventBeginPlay
  (Collision|SetCollisionEnabled (Variables|Default|GetOrb) "NoCollision")
  (Variables|Default|SetDirector (Actor|GetActorOfClass :ActorClass "/Game/SoulCharger/Mechanics/Hall/BP_HallDirector_SC.BP_HallDirector_SC_C"))
  (Variables|Default|SetAmount 0.0)
  (Variables|Default|SetBurst 0.0)
  (Variables|Default|SetWasLive false)
  (Rendering|SetVisibility (Variables|Default|GetOrb) false false))

(event EventTick (DeltaSeconds)
  (Utilities|IsValid (Variables|Default|GetDirector)
    (:"Is Valid"
      (bind _dt (Math|Float|Min(Float) DeltaSeconds 0.0333))
      (bind _d (Variables|Default|GetDirector))
      (if (Class|BPHallDirectorSC|GetSensorLive _d)
        (CallFunction|OrbLive :DT _dt :S (Class|BPHallDirectorSC|GetSensor _d))
        (elif (Variables|Default|GetWasLive)
          (CallFunction|OrbPop)
          (CallFunction|OrbBurst :DT _dt))))
    (:"Is Not Valid")))

;; ===== GRAFO: OrbLive (DT float, S BP_BioSensorArt_SC) — nace (ease) en el sensor, lo acompaña y lo hace girar
(fn OrbLive (DT S)
  (Variables|Default|SetWasLive true)
  (Variables|Default|SetBurst 0.0)
  (Variables|Default|SetAmount (Math|Interpolation|FInterptoConstant (Variables|Default|GetAmount) 1.0 DT (/ 1.0 (Math|Float|Max(Float) (Variables|Default|GetAppearTime) 0.05))))
  (Transformation|SetActorLocation :NewLocation (Transformation|GetActorLocation :self S) :bSweep false :bTeleport true)
  (Transformation|AddActorWorldRotation :self S :DeltaRotation (Math|Rotator|MakeRotator :Yaw (* (Variables|Default|GetSpinDeg) DT)) :bSweep false :bTeleport true)
  (bind _e (Math|Float|FInterpEaseinOut 0.0 1.0 (Variables|Default|GetAmount) 2.0))
  (bind _sz (* (Variables|Default|GetOrbSize) _e))
  (Transformation|SetRelativeScale3D (Variables|Default|GetOrb) (Math|Vector|MakeVector _sz _sz _sz))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetOrb) "OpacityCore" (* (Variables|Default|GetOrbOpacityCore) _e))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetOrb) "OpacityRim" (* (Variables|Default|GetOrbOpacityRim) _e))
  (Rendering|SetVisibility (Variables|Default|GetOrb) (> _e 0.001) false))

;; ===== GRAFO: OrbPop () — el sonido, una sola vez, en el primer cuadro del estallido
(fn OrbPop ()
  (if (<= (Variables|Default|GetBurst) 0.0)
    (Audio|PlaySound2D :Sound (Variables|Default|GetBurstSound) :VolumeMultiplier 0.5)))

;; ===== GRAFO: OrbBurst (DT float) — crece ×(1+BurstGrow) con ease-out y se desvanece; al terminar se apaga y rearma
(fn OrbBurst (DT)
  (Variables|Default|SetBurst (Math|Interpolation|FInterptoConstant (Variables|Default|GetBurst) 1.0 DT (/ 1.0 (Math|Float|Max(Float) (Variables|Default|GetBurstTime) 0.05))))
  (bind _u (- 1.0 (Variables|Default|GetBurst)))
  (bind _e (- 1.0 (* _u _u)))
  (bind _sz (* (Variables|Default|GetOrbSize) (+ 1.0 (* (Variables|Default|GetBurstGrow) _e))))
  (Transformation|SetRelativeScale3D (Variables|Default|GetOrb) (Math|Vector|MakeVector _sz _sz _sz))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetOrb) "OpacityCore" (* (Variables|Default|GetOrbOpacityCore) (- 1.0 _e)))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetOrb) "OpacityRim" (* (Variables|Default|GetOrbOpacityRim) (- 1.0 _e)))
  (if (>= (Variables|Default|GetBurst) 1.0)
    (Variables|Default|SetWasLive false)
    (Variables|Default|SetAmount 0.0)
    (Rendering|SetVisibility (Variables|Default|GetOrb) false false)))
