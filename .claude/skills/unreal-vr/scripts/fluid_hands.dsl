;; BP_FluidMedium_SC — F4, las MANOS revuelven las partículas (2026-09-30, noche; pedido de Beltrán: "etapa sin
;; sensor: solo las manos, que mueven las partículas y generan turbulencia"). El shader ya lo tenía
;; (FluidLib::Stir en FluidMotesVS, rama uniforme por HandV.w): faltaba el lado del BP, que nunca se construyó.
;;   HandRefs(): toma los MotionController GRIP del pawn (BP_VRPawn_SC, accesores GetMotionController{Left,Right}Grip;
;;               un MotionController propio en un actor del nivel NO trackea, assets-existentes.md). Reintenta cada
;;               cuadro hasta tenerlos (en BeginPlay el pawn puede no existir todavía).
;;   HandStep(DT): posición de cada mano en espacio LOCAL del fluido -> Hand0/Hand1 = (pos, StirRadius);
;;               velocidad (diferencia de posiciones / DT, tope HandMaxSpeed 300 cm/s contra saltos del tracking,
;;               suavizada con VInterpTo a HandVelSpeed 5/s: al frenar la mano el remolino se apaga en ~0,3 s, no de
;;               golpe) -> HandV0/HandV1 = (vel, StirStrength). Con bHandStir false la velocidad objetivo es 0: el
;;               remolino se apaga con curva y recien entonces HandV.w = 0 (el shader salta la rama: costo cero).
;; Empalme por cirugía: EventGraph, Tick: ... -> PushCells -> HandStep(DeltaSeconds).
;; Variables nuevas: 6-Manos HandVelSpeed (5) · HandMaxSpeed (300) · Z-Interno HandL, HandR (SceneComponent: el grip del pawn)
;; · HandsReady · HandsPrimed · HandPL · HandPR · HandVL · HandVR.

;; ===== GRAFO: HandRefs
(fn HandRefs ()
  (bind _vp (Utilities|Casting|CastToBP_VRPawn_SC :Object (Game|GetPlayerPawn 0))
    (:then
      (bind _ml (Class|BPVRPawnSC|GetMotionControllerLeftGrip _vp))
      (bind _mr (Class|BPVRPawnSC|GetMotionControllerRightGrip _vp))
      (Variables|Z-Interno|SetHandL _ml)
      (Variables|Z-Interno|SetHandR _mr)
      (Variables|Z-Interno|SetHandsReady true))
    (:CastFailed)))

;; ===== GRAFO: HandStep
;; Sin saltos de un cuadro (estandar de la noche): con bHandStir false la velocidad objetivo es CERO y el remolino se
;; APAGA suavizado (VInterpTo); HandV.w baja a 0 recien cuando las dos velocidades quedan < 0,5 cm/s.
(fn HandStep (DT)
  (bind _xf (Transformation|GetActorTransform))
  (bind _pl (Math|Transform|InverseTransformLocation _xf (Transformation|GetWorldLocation (Variables|Z-Interno|GetHandL))))
  (bind _pr (Math|Transform|InverseTransformLocation _xf (Transformation|GetWorldLocation (Variables|Z-Interno|GetHandR))))
  (bind _dt (Math|Float|Clamp(Float) DT 0.001 0.0333333))
  (bind _go (and (Variables|6-Manos|GetHandStir) (Variables|Z-Interno|GetHandsPrimed)))
  (bind _mx (Variables|6-Manos|GetHandMaxSpeed))
  (bind _sp (Variables|6-Manos|GetHandVelSpeed))
  (bind _zero (Math|Vector|MakeVector 0.0 0.0 0.0))
  (bind _vl (Variables|Z-Interno|GetHandVL))
  (bind _vr (Variables|Z-Interno|GetHandVR))
  (bind _w (select (or (Variables|6-Manos|GetHandStir) (> (+ (Math|Vector|VectorLength (Variables|Z-Interno|GetHandVL)) (Math|Vector|VectorLength (Variables|Z-Interno|GetHandVR))) 0.5)) (Variables|6-Manos|GetStirStrength) 0.0))
  (if (not (Variables|Z-Interno|GetHandsReady))
    (CallFunction|HandRefs)
    (else
      (Variables|Z-Interno|SetHandVL (Math|Interpolation|VInterpTo _vl (select _go (Math|Vector|ClampVectorSize (/ (- _pl (Variables|Z-Interno|GetHandPL)) _dt) 0.0 _mx) _zero) _dt _sp))
      (Variables|Z-Interno|SetHandVR (Math|Interpolation|VInterpTo _vr (select _go (Math|Vector|ClampVectorSize (/ (- _pr (Variables|Z-Interno|GetHandPR)) _dt) 0.0 _mx) _zero) _dt _sp))
      (Variables|Z-Interno|SetHandPL _pl)
      (Variables|Z-Interno|SetHandPR _pr)
      (Variables|Z-Interno|SetHandsPrimed true)
      (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Hand0" :ParameterValue (Math|Color|MakeColor (.x _pl) (.y _pl) (.z _pl) (Variables|6-Manos|GetStirRadius)))
      (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "HandV0" :ParameterValue (Math|Color|MakeColor (.x (Variables|Z-Interno|GetHandVL)) (.y (Variables|Z-Interno|GetHandVL)) (.z (Variables|Z-Interno|GetHandVL)) _w))
      (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "Hand1" :ParameterValue (Math|Color|MakeColor (.x _pr) (.y _pr) (.z _pr) (Variables|6-Manos|GetStirRadius)))
      (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "HandV1" :ParameterValue (Math|Color|MakeColor (.x (Variables|Z-Interno|GetHandVR)) (.y (Variables|Z-Interno|GetHandVR)) (.z (Variables|Z-Interno|GetHandVR)) _w)))))
