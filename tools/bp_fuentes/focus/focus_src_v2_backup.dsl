;; BP_FocusDirector_SC (Test_Focus, 2026-10-29) - fuente de los grafos. (G X) = getter, (S X v) = setter; gen_focus_dsl.py
;; los expande con la categoria de cada variable y escribe focus_dsl.json. Un bloque ;;@ = un grafo.
;; Mecanica: 4 amebas (BP_LovingCell_SC en fase 0) que se cargan sosteniendo la mirada. El director les escribe el estado,
;; la escala, la posicion y el color; nunca toca sus grafos.

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|FcBoot))
(event EventTick (DeltaSeconds)
  (CallFunction|FcStep :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

;;@ FcBoot
;; Guarda de cada ameba su lugar, giro completo (el roll la hace distinta), escala y 6 colores (OrigCol, 6 por ameba); desfasa
;; su reloj (ClockSeed: cada una con su propio movimiento); las esconde dormidas; crea el punto de foco.
(fn FcBoot ()
  (bind n (Utilities|Array|Length (G Cells)))
  (for i (range n)
    (bind c (Utilities|Array|Get(acopy) (G Cells) i))
    (Utilities|Array|Add (G Charge) 0.0)
    (Utilities|Array|Add (G Locked) false)
    (Utilities|Array|Add (G Reveal) 0.0)
    (Utilities|Array|Add (G RevealAt) -1.0)
    (Utilities|Array|Add (G LockAt) -1.0)
    (Utilities|Array|Add (G LightP) 0.0)
    (Utilities|Array|Add (G Home) (Transformation|GetActorLocation :self c))
    (Utilities|Array|Add (G HomeRot) (Transformation|GetActorRotation :self c))
    (Class|BPLovingCellSC|SetClock :self c :Clock (* (Math|Conversions|ToFloat(Integer) i) (G ClockSeed)))
    (Utilities|Array|Add (G BaseSc) (Transformation|GetActorScale3D :self c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetAmoebaColor1 c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetAmoebaColor2 c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetMembraneColor c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetMembraneRim c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetOuterColor c))
    (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetDustColor c))
    (Rendering|SetActorHiddenInGame :self c :bNewHidden true)
    (CallFunction|FcLook :I i :L 0.0))
  (bind d (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|SetMobility d "Movable")
  (Transformation|SetAbsolute d true true true)
  (Components|StaticMesh|SetStaticMesh d (G DotMesh))
  (Rendering|Material|SetMaterial d 0 (G DotMat))
  (Collision|SetCollisionEnabled d "NoCollision")
  (Rendering|SetCastShadow d false)
  (Rendering|SetTranslucentSortPriority d 300)
  (Rendering|Material|SetVectorParameterValueonMaterials d "Color" (Math|Conversions|ToVector(LinearColor) (G DotColor)))
  (S DotComp d)
  (S DotD (G DotIdle))
  (S Target -1)
  (S ChargeOn -1)
  (S HintI -1)
  (S Phase 0)
  (S Clock 0.0))

;;@ FcStep
;; Un cuadro: mirada -> carga y fases -> cada ameba -> punto -> constelacion -> el fluido sigue la luz promedio.
(fn FcStep (Dt)
  (S Clock (+ (G Clock) Dt))
  (S PhaseT (+ (G PhaseT) Dt))
  (CallFunction|FcGaze)
  (CallFunction|FcCharge :Dt Dt)
  (S LightSum 0.0)
  (for i (range (Utilities|Array|Length (G Cells)))
    (CallFunction|FcCell :I i))
  (CallFunction|FcDot :Dt Dt)
  (CallFunction|FcFinale :Dt Dt)
  (Utilities|IsValid (G Fluid)
    (:"Is Valid"
      (Class|BPFluidMediumSC|SetFakeEEG :self (G Fluid) :bFakeEEG false)
      (Class|BPFluidMediumSC|SetEEG :self (G Fluid) :EEG (Math|Float|Lerp (G FluidCalm) (G FluidActive) (Math|Float|Clamp(Float) (/ (G LightSum) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length (G Cells))) 1.0))))))))

;;@ FcGaze
;; Target = la ameba visible mas centrada dentro del cono (GazeDeg para entrar, GazeOut para la que ya se mira). DebugTarget >= 0 la fuerza.
;; bDebugAuto (prueba sin visor): mira la ameba de la pista 6 s de cada 8 (los otros 2 s aparta la vista).
(fn FcGaze ()
  (bind cm (Game|GetPlayerCameraManager 0))
  (S GBest -1)
  (S GBestDot -2.0)
  (if (>= (G DebugTarget) 0)
    (S Target (G DebugTarget))
    (elif (G DebugAuto)
      (S Target (select (< (Math|Float|Fraction (/ (G Clock) 8.0)) 0.75) (G HintI) -1))
    (else
      (Utilities|IsValid cm
        (:"Is Valid"
          (bind cl (Camera|GetCameraLocation cm))
          (bind fw (Math|Vector|GetForwardVector (Camera|GetCameraRotation cm)))
          (for i (range (Utilities|Array|Length (G Cells)))
            (bind d (Math|Vector|DotProduct (Math|Vector|Normalize (- (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Cells) i)) cl)) fw))
            (if (and (>= (Utilities|Array|Get(acopy) (G Reveal) i) 0.9) (and (>= d (Math|Trig|Cos(Degrees) (select (== i (G Target)) (G GazeOut) (G GazeDeg)))) (> d (G GBestDot))))
              (S GBestDot d)
              (S GBest i)))
          (S Target (G GBest)))
        (:"Is Not Valid"
          (S Target -1)))))))

;;@ FcCharge
;; Sube la carga de la ameba mirada en HoldTime s; las otras bajan FadeBack veces mas lento (no se reinician). Al 100 %: FcLock.
;; Despues: sonido de carga, pista (la primera ameba visible sin activar), y las fases.
(fn FcCharge (Dt)
  (bind ht (Math|Float|Max(Float) (G HoldTime) 0.1))
  (S HintI -1)
  (for i (range (Utilities|Array|Length (G Cells)))
    (bind lk (Utilities|Array|Get(acopy) (G Locked) i))
    (bind rv (Utilities|Array|Get(acopy) (G Reveal) i))
    (bind c (Utilities|Array|Get(acopy) (G Charge) i))
    (bind on (and (== i (G Target)) (>= rv 0.9)))
    (Utilities|Array|SetArrayElem (G Charge) i (select lk 1.0 (Math|Float|Clamp(Float) (select on (+ c (/ Dt ht)) (- c (/ (* Dt (G FadeBack)) ht))))) true)
    (if (and (not lk) (>= (Utilities|Array|Get(acopy) (G Charge) i) 1.0))
      (CallFunction|FcLock :I i)
      (elif (and (== (G HintI) -1) (and (not lk) (>= rv 0.9)))
        (S HintI i))))
  (bind t (G Target))
  (bind tl (Utilities|Array|Get(acopy) (G Locked) (Math|Integer|Max(Integer) t 0)))
  (CallFunction|FcChargeSnd :W (select (and (>= t 0) (not tl)) t -1))
  (S NoLook (select (and (>= t 0) (not tl)) 0.0 (+ (G NoLook) Dt)))
  (if (and (== (G Phase) 0) (>= (G Clock) (G StartDelay)))
    (Utilities|Array|SetArrayElem (G RevealAt) 0 (G Clock) true)
    (S Phase 1)
    (elif (and (== (G Phase) 1) (>= (G LockedN) 1))
      (CallFunction|FcRevealRest)
      (S Phase 2)
      (elif (and (== (G Phase) 2) (>= (G LockedN) (Utilities|Array|Length (G Cells))))
        (S Phase 3)
        (S PhaseT 0.0)
        (CallFunction|FcSound :Snd (G FinaleSound))
        (elif (and (== (G Phase) 3) (>= (G PhaseT) (G FinaleHold)))
          (S Phase 4)
          (S StageDone true))))))

;;@ FcChargeSnd
;; El sonido de carga suena mientras se mira una ameba sin activar (W); cambia de ameba o se suelta -> se apaga en 0,4 s.
(fn FcChargeSnd (W)
  (if (!= W (G ChargeOn))
    (CallFunction|FcACFade)
    (S ChargeOn W)
    (if (>= W 0)
      (S ChargeAC (Audio|SpawnSound2D :Sound (G ChargeSound) :VolumeMultiplier (* (G SfxVol) 0.5))))))

;;@ FcACFade
;; El FadeOut del AudioComponent se agrega por cirugia (el DSL elige el de SynthComponent, gotcha 40/102).
(fn FcACFade ()
  (Utilities|IsValid (G ChargeAC)
    (:"Is Valid")))

;;@ FcLock
;; La activacion: queda encendida, suena el "completo" y vibran los dos mandos (la haptica de la Obra).
(fn FcLock (I)
  (Utilities|Array|SetArrayElem (G Locked) I true true)
  (Utilities|Array|SetArrayElem (G LockAt) I (G Clock) true)
  (S LockedN (+ (G LockedN) 1))
  (CallFunction|FcSound :Snd (G LockSound))
  (bind pc (Game|GetPlayerController 0))
  (Utilities|IsValid pc
    (:"Is Valid"
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left")
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right"))))

;;@ FcSound
(fn FcSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid"
      (Audio|PlaySound2D :Sound Snd :VolumeMultiplier (G SfxVol)))))

;;@ FcRevealRest
;; Tras la primera: las demas aparecen RevealDelay s despues, separadas RevealGap s.
(fn FcRevealRest ()
  (for i (range (Utilities|Array|Length (G Cells)))
    (if (> i 0)
      (Utilities|Array|SetArrayElem (G RevealAt) i (+ (+ (G Clock) (G RevealDelay)) (* (Math|Conversions|ToFloat(Integer) (- i 1)) (G RevealGap))) true))))

;;@ FcCell
;; Una ameba por cuadro. e = smoothstep de la carga. Aparece con ease-out-back (la curva de StageIntro de la celula), crece de
;; SleepScale a 1, pasa de SleepState (contraida) a AwakeState (activa) y su Agitation de SleepAgit a AwakeAgit; mientras se la
;; mira se agita de mas (ChargeAgit x carga) y late de luz (ChargePulse). Deriva suave y se mece con el final; conserva su giro propio.
;; La luz L = e + destello de activacion + pista + latido de carga; el color se empuja solo si L cambio.
(fn FcCell (I)
  (bind c (Utilities|Array|Get(acopy) (G Cells) I))
  (bind ra (Utilities|Array|Get(acopy) (G RevealAt) I))
  (bind rv (select (< ra 0.0) 0.0 (Math|Float|Clamp(Float) (/ (- (G Clock) ra) (Math|Float|Max(Float) (G RevealTime) 0.1)))))
  (S RevSnd (and (<= (Utilities|Array|Get(acopy) (G Reveal) I) 0.0) (> rv 0.0)))
  (Utilities|Array|SetArrayElem (G Reveal) I rv true)
  (bind ch (Utilities|Array|Get(acopy) (G Charge) I))
  (bind e (* (* ch ch) (- 3.0 (* 2.0 ch))))
  (bind la (Utilities|Array|Get(acopy) (G LockAt) I))
  (bind bt (select (< la 0.0) 99.0 (- (G Clock) la)))
  (bind bk (Math|Float|Clamp(Float) (/ bt (Math|Float|Max(Float) (G BloomTime) 0.1))))
  (bind bl (* (* (- 1.0 bk) (- 1.0 bk)) (Math|Float|Clamp(Float) (/ bt 0.15))))
  (bind hp (* (G HintLight) (* (Math|Float|Clamp(Float) (/ (- (G NoLook) (G HintDelay)) 2.0)) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G HintHz) (G Clock)))))))))
  (bind hnt (select (and (== I (G HintI)) (< (G Phase) 3)) hp 0.0))
  (bind on (and (== I (G Target)) (not (Utilities|Array|Get(acopy) (G Locked) I))))
  (bind cp (select on (* (G ChargePulse) (* ch (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G ChargePulseHz) (G Clock)))))))) 0.0))
  (bind L (+ (+ (+ e (* (G BloomLight) bl)) hnt) cp))
  (S LightSum (+ (G LightSum) e))
  (bind x (- rv 1.0))
  (bind rb (Math|Float|Max(Float) (+ 1.0 (+ (* 1.8 (* (* x x) x)) (* 0.8 (* x x)))) 0.001))
  (bind sc (* rb (* (Math|Float|Lerp (G SleepScale) 1.0 e) (+ 1.0 (* (G BloomScale) bl)))))
  (bind w (* 6.2831853 (G DriftHz)))
  (bind ph (* (Math|Conversions|ToFloat(Integer) I) 1.7))
  (bind dr (Math|Vector|MakeVector :X (Math|Trig|Sin(Radians) (+ (* w (G Clock)) ph)) :Y (* 0.8 (Math|Trig|Sin(Radians) (+ (* (* w 1.37) (G Clock)) (* ph 1.9)))) :Z (* 0.6 (Math|Trig|Sin(Radians) (+ (* (* w 0.73) (G Clock)) (* ph 0.6))))))
  (bind pv (Transformation|GetActorLocation))
  (bind p (+ (+ pv (Math|Vector|RotateVectorAroundAxis :InVect (- (Utilities|Array|Get(acopy) (G Home) I) pv) :AngleDeg (G OrbitYaw) :Axis (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 1.0))) (* dr (G DriftAmp))))
  (Transformation|SetActorLocation :self c :NewLocation p)
  (bind hr (Utilities|Array|Get(acopy) (G HomeRot) I))
  (Transformation|SetActorRotation :self c :NewRotation (Math|Rotator|MakeRotator :Roll (.roll hr) :Pitch (.pitch hr) :Yaw (+ (.yaw hr) (G OrbitYaw))))
  (Transformation|SetActorScale3D :self c :NewScale3D (* (Utilities|Array|Get(acopy) (G BaseSc) I) sc))
  (Rendering|SetActorHiddenInGame :self c :bNewHidden (<= rv 0.0))
  (Class|BPLovingCellSC|SetGlobalState :self c :GlobalState (Math|Float|Lerp (G SleepState) (G AwakeState) e))
  (Class|BPLovingCellSC|SetAgitation :self c :Agitation (+ (Math|Float|Lerp (G SleepAgit) (G AwakeAgit) e) (select on (* (G ChargeAgit) ch) 0.0)))
  (if (G RevSnd)
    (CallFunction|FcSound :Snd (G RevealSound))
    (elif (> (Math|Float|Absolute(Float) (- L (Utilities|Array|Get(acopy) (G LightP) I))) 0.004)
      (Utilities|Array|SetArrayElem (G LightP) I L true)
      (CallFunction|FcLook :I I :L L))))

;;@ FcLook
;; Pinta la ameba I con luz L (0 dormida, 1 despierta, > 1 destello) sobre sus colores originales, con las perillas de la celula
;; y su propio PushLook; la envoltura y el polvo van directo al material (la celula solo los empuja con StaticDirty).
(fn FcLook (I L)
  (bind c (Utilities|Array|Get(acopy) (G Cells) I))
  (bind k (* I 6))
  (Class|BPLovingCellSC|SetAmoebaColor1 :self c :AmoebaColor1 (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) k) :L L))
  (Class|BPLovingCellSC|SetAmoebaColor2 :self c :AmoebaColor2 (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) (+ k 1)) :L L))
  (Class|BPLovingCellSC|SetMembraneColor :self c :MembraneColor (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) (+ k 2)) :L L))
  (Class|BPLovingCellSC|SetMembraneRim :self c :MembraneRim (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) (+ k 3)) :L L))
  (Class|BPLovingCellSC|SetOuterColor :self c :OuterColor (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) (+ k 4)) :L L))
  (Class|BPLovingCellSC|SetDustColor :self c :DustColor (CallFunction|FcMix :C (Utilities|Array|Get(acopy) (G OrigCol) (+ k 5)) :L L))
  (Class|BPLovingCellSC|PushLook :self c)
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetOuterShell c) "OuterCol" (Math|Color|NewOpacity(LinearColor) (Class|BPLovingCellSC|GetOuterColor c) (Class|BPLovingCellSC|GetOuterOpacity c)))
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetDust c) "DustCol" (Class|BPLovingCellSC|GetDustColor c)))

;;@ FcMix
;; Color dormido = lerp(original, SleepTint, SleepMix) * SleepDim; con luz L vuelve al original (L > 1 lo pasa: destello). Conserva el alfa.
(fn FcMix (C L)
  (bind (r g b a) (Utilities|Struct|BreakLinearColor C))
  (return (Math|Color|NewOpacity(LinearColor) (Math|Color|Lerp(LinearColor) (* (Math|Color|Lerp(LinearColor) C (G SleepTint) (G SleepMix)) (G SleepDim)) C L) a)))

;;@ FcDot
;; El punto de foco: frente a la vista, a la distancia de la ameba mirada (para no verlo doble), con angulo fijo DotAngle.
;; El anillo aparece al mirar una ameba sin activar y se cierra con su carga.
(fn FcDot (Dt)
  (bind cm (Game|GetPlayerCameraManager 0))
  (Utilities|IsValid cm
    (:"Is Valid"
      (bind cl (Camera|GetCameraLocation cm))
      (bind fw (Math|Vector|GetForwardVector (Camera|GetCameraRotation cm)))
      (bind t (G Target))
      (bind ti (Math|Integer|Max(Integer) t 0))
      (bind on (and (>= t 0) (not (Utilities|Array|Get(acopy) (G Locked) ti))))
      (S DotD (Math|Interpolation|FInterpTo :Current (G DotD) :Target (select (>= t 0) (Math|Float|Max(Float) (- (Math|Vector|Distance(Vector) cl (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Cells) ti))) 25.0) 40.0) (G DotIdle)) :DeltaTime Dt :InterpSpeed 6.0))
      (S DotRing (Math|Interpolation|FInterpTo :Current (G DotRing) :Target (select on 1.0 0.0) :DeltaTime Dt :InterpSpeed 8.0))
      (bind dc (G DotComp))
      (Transformation|SetWorldLocationAndRotation dc (+ cl (* fw (G DotD))) (Math|Rotator|MakeRotfromZ (* fw -1.0)))
      (Transformation|SetWorldScale3D dc (* (Math|Vector|MakeVector :X 1.0 :Y 1.0 :Z 1.0) (* (G DotD) (* 0.01 (Math|Trig|Tan(Degrees) (G DotAngle))))))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Progress" (select (>= t 0) (Utilities|Array|Get(acopy) (G Charge) ti) 0.0))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Ring" (G DotRing))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Opacity" (Math|Float|Lerp (G DotIdleOpacity) (G DotOpacity) (G DotRing)))
      (Rendering|SetVisibility dc (< (G Phase) 3) false))))

;;@ FcFinale
;; Con las 4 activas la constelacion se mece +-OrbitAmp grados alrededor del usuario cada OrbitPeriod s, entrando en FinaleTime
;; tras FinaleDelay (acotado: la obra es sentada, nunca se van detras). Sin lineas entre ellas (Beltran 10-29: "horrorosas").
(fn FcFinale (Dt)
  (if (>= (G Phase) 3)
    (bind f0 (Math|Float|Clamp(Float) (/ (- (G PhaseT) (G FinaleDelay)) (Math|Float|Max(Float) (G FinaleTime) 0.1))))
    (bind f (* (* f0 f0) (- 3.0 (* 2.0 f0))))
    (S OrbitYaw (* f (* (G OrbitAmp) (Math|Trig|Sin(Radians) (* 6.2831853 (/ (G PhaseT) (Math|Float|Max(Float) (G OrbitPeriod) 1.0)))))))))
