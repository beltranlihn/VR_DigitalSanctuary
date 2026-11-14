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
;; Guarda de cada ameba su lugar, giro completo (el roll la hace distinta), escala, su vida propia (BaseLife = NoiseAmount,
;; StrandCurl, OrganicMotion, FloatAmount de la instancia; BasePulse) y 6 colores (OrigCol, 6 por ameba); le sortea su deriva
;; (WF frecuencias, WP fases: ninguna se mueve como otra); le crea su nube de particulas (Motes, apagada); las esconde dormidas;
;; crea el punto de foco. El desfase del movimiento interno de cada celula es su PreviewTime (instancia).
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
    (Utilities|Array|Add (G Excite) 0.0)
    (Utilities|Array|Add (G MoteF) 0.0)
    (Utilities|Array|Add (G MoteOn) false)
    (Utilities|Array|Add (G Home) (Transformation|GetActorLocation :self c))
    (Utilities|Array|Add (G HomeRot) (Transformation|GetActorRotation :self c))
    (Utilities|Array|Add (G BaseLife) (Math|Color|MakeColor (Class|BPLovingCellSC|GetNoiseAmount c) (Class|BPLovingCellSC|GetStrandCurl c) (Class|BPLovingCellSC|GetOrganicMotion c) (Class|BPLovingCellSC|GetFloatAmount c)))
    (Utilities|Array|Add (G BasePulse) (Class|BPLovingCellSC|GetPulseSpeed c))
    (Utilities|Array|Add (G WF) (Math|Vector|MakeVector :X (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5) :Y (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5) :Z (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5)))
    (Utilities|Array|Add (G WP) (Math|Vector|MakeVector :X (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853) :Y (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853) :Z (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853)))
    (bind mo (Niagara|SpawnSystematLocation :SystemTemplate (G MoteSystem) :Location (Transformation|GetActorLocation :self c) :bAutoDestroy false :bAutoActivate false))
    (Utilities|Array|Add (G Motes) mo)
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
;; Un cuadro: mirada -> carga, excitacion, particulas y fases -> cada ameba -> color del lugar -> punto -> el fluido sigue la
;; luz promedio.
(fn FcStep (Dt)
  (S Clock (+ (G Clock) Dt))
  (S PhaseT (+ (G PhaseT) Dt))
  (CallFunction|FcGaze)
  (CallFunction|FcCharge :Dt Dt)
  (S LightSum 0.0)
  (for i (range (Utilities|Array|Length (G Cells)))
    (CallFunction|FcCell :I i))
  (CallFunction|FcEnv :Dt Dt)
  (CallFunction|FcDot :Dt Dt)
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
;; Excite = la carga mientras se la mira (sin activar), suavizada (ExciteSpeed): la agitacion extra de la carga; baja sola al
;; activarse o al apartar la vista. Despues: particulas, sonido de carga, pista (la primera ameba visible sin activar), y las fases.
(fn FcCharge (Dt)
  (bind ht (Math|Float|Max(Float) (G HoldTime) 0.1))
  (S HintI -1)
  (for i (range (Utilities|Array|Length (G Cells)))
    (bind lk (Utilities|Array|Get(acopy) (G Locked) i))
    (bind rv (Utilities|Array|Get(acopy) (G Reveal) i))
    (bind c (Utilities|Array|Get(acopy) (G Charge) i))
    (bind on (and (== i (G Target)) (>= rv 0.9)))
    (Utilities|Array|SetArrayElem (G Charge) i (select lk 1.0 (Math|Float|Clamp(Float) (select on (+ c (/ Dt ht)) (- c (/ (* Dt (G FadeBack)) ht))))) true)
    (Utilities|Array|SetArrayElem (G Excite) i (Math|Interpolation|FInterpTo :Current (Utilities|Array|Get(acopy) (G Excite) i) :Target (select (and on (not lk)) (Utilities|Array|Get(acopy) (G Charge) i) 0.0) :DeltaTime Dt :InterpSpeed (G ExciteSpeed)) true)
    (CallFunction|FcMote :I i :Dt Dt)
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

;;@ FcMote
;; La nube de la carga (NS_FocusMotes_SC = el halo de las esferas de Attracting): mientras se mira una ameba sin activar, nacen
;; particulas en una cascara de MoteRadius cm a su alrededor y MotePull las atrae a su centro (la ameba junta luz). Mas carga, mas
;; particulas. Al apartar la vista se sueltan (MoteRelease) y se apagan en MoteFade s; al activarse terminan de entrar y se apagan.
;; Solo trabaja la ameba que tiene la nube prendida o apagandose.
(fn FcMote (I Dt)
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (bind want (and (== I (G Target)) (and (not (Utilities|Array|Get(acopy) (G Locked) I)) (>= (Utilities|Array|Get(acopy) (G Reveal) I) 0.9))))
  (Utilities|IsValid m
    (:"Is Valid"
      (if (or want (or (> (Utilities|Array|Get(acopy) (G MoteF) I) 0.0) (Utilities|Array|Get(acopy) (G MoteOn) I)))
        (CallFunction|FcMoteEdge :I I :Want want)
        (Utilities|Array|SetArrayElem (G MoteF) I (Math|Float|Clamp(Float) (+ (Utilities|Array|Get(acopy) (G MoteF) I) (/ (* Dt (select want 1.0 -1.0)) (Math|Float|Max(Float) (G MoteFade) 0.05)))) true)
        (bind f (Utilities|Array|Get(acopy) (G MoteF) I))
        (bind c (Utilities|Array|Get(acopy) (G Cells) I))
        (Transformation|SetWorldLocation m (Transformation|GetActorLocation :self c))
        (Niagara|SetNiagaraVariable(Position) m "Target" (Transformation|GetActorLocation :self c))
        (Niagara|SetNiagaraVariable(Float) m "SpawnRate" (select want (* (G MoteRate) (+ 0.3 (* 0.7 (Utilities|Array|Get(acopy) (G Charge) I)))) 0.0))
        (Niagara|SetNiagaraVariable(Float) m "Fade" (* (* f f) (- 3.0 (* 2.0 f))))
        (if (and (not want) (<= f 0.0))
          (Components|Activation|Deactivate m))))))

;;@ FcMoteEdge
;; El cambio de estado de la nube: al prenderse copia las perillas (color de la ameba, vida, tamanos, radio, ruido) y la activa;
;; al apagarse corta el nacimiento y, si la ameba no se activo, las suelta hacia afuera.
(fn FcMoteEdge (I Want)
  (bind was (Utilities|Array|Get(acopy) (G MoteOn) I))
  (if (or (and Want (not was)) (and (not Want) was))
    (Utilities|Array|SetArrayElem (G MoteOn) I Want true)
    (bind m (Utilities|Array|Get(acopy) (G Motes) I))
    (Niagara|SetNiagaraVariable(Float) m "Push" (select (or Want (Utilities|Array|Get(acopy) (G Locked) I)) (G MotePull) (* -1.0 (G MoteRelease))))
    (if Want
      (Niagara|SetNiagaraVariable(LinearColor) m "OrbColor" (Math|Color|NewOpacity(LinearColor) (Utilities|Array|Get(acopy) (G OrigCol) (* I 6)) (G MoteAlpha)))
      (Niagara|SetNiagaraVariable(Float) m "Life" (Math|Float|Max(Float) (G MoteLife) 0.2))
      (Niagara|SetNiagaraVariable(Float) m "SizeMin" (G MoteSize))
      (Niagara|SetNiagaraVariable(Float) m "SizeMax" (* 2.0 (G MoteSize)))
      (Niagara|SetNiagaraVariable(Float) m "Radius" (G MoteRadius))
      (Niagara|SetNiagaraVariable(Float) m "Noise" (G MoteNoise))
      (if (or (not (Components|Activation|IsActive m)) (<= (Utilities|Array|Get(acopy) (G MoteF) I) 0.0))
        (Components|Activation|Activate m true)))))

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
;; Una ameba por cuadro. e = smoothstep de la carga; x = su excitacion (Excite, solo mientras se la carga). Aparece con
;; ease-out-back (la curva de StageIntro de la celula), crece de SleepScale a 1, pasa de SleepState a AwakeState y su Agitation
;; de SleepAgit a AwakeAgit (+ ChargeAgit x). Su VIDA (ruido del nucleo, OrganicMotion, FloatAmount, respiracion) se multiplica
;; por 1 -> AwakeLife con e, + ChargeLife con x; sus BRAZOS (StrandCurl) por 1 -> AwakeCurl, + ChargeCurl. Lo que va al shader
;; (NoiseAmount, StrandCurl, OrganicMotion) va en LifeSteps escalones: la celula reempuja sus materiales solo cuando cambia.
;; Deriva y se balancea con sus propias frecuencias y fases (WF, WP), mas amplio despierta (DriftSleep dormida).
;; La luz L = e + destello de activacion + pista + latido de carga; el color se empuja solo si L cambio.
(fn FcCell (I)
  (bind c (Utilities|Array|Get(acopy) (G Cells) I))
  (bind ra (Utilities|Array|Get(acopy) (G RevealAt) I))
  (bind rv (select (< ra 0.0) 0.0 (Math|Float|Clamp(Float) (/ (- (G Clock) ra) (Math|Float|Max(Float) (G RevealTime) 0.1)))))
  (S RevSnd (and (<= (Utilities|Array|Get(acopy) (G Reveal) I) 0.0) (> rv 0.0)))
  (Utilities|Array|SetArrayElem (G Reveal) I rv true)
  (bind ch (Utilities|Array|Get(acopy) (G Charge) I))
  (bind e (* (* ch ch) (- 3.0 (* 2.0 ch))))
  (bind x (Utilities|Array|Get(acopy) (G Excite) I))
  (bind la (Utilities|Array|Get(acopy) (G LockAt) I))
  (bind bt (select (< la 0.0) 99.0 (- (G Clock) la)))
  (bind bk (Math|Float|Clamp(Float) (/ bt (Math|Float|Max(Float) (G BloomTime) 0.1))))
  (bind bl (* (* (- 1.0 bk) (- 1.0 bk)) (Math|Float|Clamp(Float) (/ bt 0.15))))
  (bind hp (* (G HintLight) (* (Math|Float|Clamp(Float) (/ (- (G NoLook) (G HintDelay)) 2.0)) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G HintHz) (G Clock)))))))))
  (bind hnt (select (and (== I (G HintI)) (< (G Phase) 3)) hp 0.0))
  (bind cp (* (G ChargePulse) (* x (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G ChargePulseHz) (G Clock)))))))))
  (bind L (+ (+ (+ e (* (G BloomLight) bl)) hnt) cp))
  (S LightSum (+ (G LightSum) e))
  (bind xr (- rv 1.0))
  (bind rb (Math|Float|Max(Float) (+ 1.0 (+ (* 1.8 (* (* xr xr) xr)) (* 0.8 (* xr xr)))) 0.001))
  (bind sc (* rb (* (Math|Float|Lerp (G SleepScale) 1.0 e) (+ 1.0 (* (G BloomScale) bl)))))
  (bind ns (Math|Float|Max(Float) (G LifeSteps) 1.0))
  (bind qe (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* e ns))) ns))
  (bind qx (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* x ns))) ns))
  (bind ml (+ 1.0 (+ (* (- (G AwakeLife) 1.0) qe) (* (G ChargeLife) qx))))
  (bind mk (+ 1.0 (+ (* (- (G AwakeCurl) 1.0) qe) (* (G ChargeCurl) qx))))
  (bind mf (+ 1.0 (+ (* (- (G AwakeLife) 1.0) e) (* (G ChargeLife) x))))
  (bind (lN lK lM lF) (Utilities|Struct|BreakLinearColor (Utilities|Array|Get(acopy) (G BaseLife) I)))
  (bind wf (Utilities|Array|Get(acopy) (G WF) I))
  (bind wp (Utilities|Array|Get(acopy) (G WP) I))
  (bind tw (* (* 6.2831853 (G DriftHz)) (G Clock)))
  (bind amp (Math|Float|Lerp (G DriftSleep) 1.0 e))
  (bind dr (Math|Vector|MakeVector :X (+ (Math|Trig|Sin(Radians) (+ (* tw (.x wf)) (.x wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.x wf))) (* 2.0 (.y wp)))))) :Y (+ (Math|Trig|Sin(Radians) (+ (* tw (.y wf)) (.y wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.y wf))) (* 2.0 (.z wp)))))) :Z (* 0.7 (+ (Math|Trig|Sin(Radians) (+ (* tw (.z wf)) (.z wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.z wf))) (* 2.0 (.x wp)))))))))
  (Transformation|SetActorLocation :self c :NewLocation (+ (Utilities|Array|Get(acopy) (G Home) I) (* dr (* (G DriftAmp) amp))))
  (bind hr (Utilities|Array|Get(acopy) (G HomeRot) I))
  (bind wr (* (G WanderRot) amp))
  (Transformation|SetActorRotation :self c :NewRotation (Math|Rotator|MakeRotator :Roll (+ (.roll hr) (* wr (Math|Trig|Sin(Radians) (+ (* tw (* 0.83 (.y wf))) (.z wp))))) :Pitch (+ (.pitch hr) (* (* 0.6 wr) (Math|Trig|Sin(Radians) (+ (* tw (* 0.71 (.z wf))) (.x wp))))) :Yaw (+ (.yaw hr) (* wr (Math|Trig|Sin(Radians) (+ (* tw (* 0.67 (.x wf))) (.y wp)))))))
  (Transformation|SetActorScale3D :self c :NewScale3D (* (Utilities|Array|Get(acopy) (G BaseSc) I) sc))
  (Rendering|SetActorHiddenInGame :self c :bNewHidden (<= rv 0.0))
  (Class|BPLovingCellSC|SetGlobalState :self c :GlobalState (Math|Float|Lerp (G SleepState) (G AwakeState) e))
  (Class|BPLovingCellSC|SetAgitation :self c :Agitation (+ (Math|Float|Lerp (G SleepAgit) (G AwakeAgit) e) (* (G ChargeAgit) x)))
  (Class|BPLovingCellSC|SetNoiseAmount :self c :NoiseAmount (Math|Float|Min(Float) (* lN ml) 2.0))
  (Class|BPLovingCellSC|SetStrandCurl :self c :StrandCurl (Math|Float|Min(Float) (* lK mk) 2.0))
  (Class|BPLovingCellSC|SetOrganicMotion :self c :OrganicMotion (* lM ml))
  (Class|BPLovingCellSC|SetFloatAmount :self c :FloatAmount (* lF mf))
  (Class|BPLovingCellSC|SetPulseSpeed :self c :PulseSpeed (* (Utilities|Array|Get(acopy) (G BasePulse) I) mf))
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

;;@ FcEnv
;; El lugar se activa con las amebas (Beltran 10-29: "asi sentimos como vamos activando el lugar"): el progreso es la suma de
;; las cargas (LightSum = suma de e, la calculo FcCell), 0 -> 4, suavizado con EnvSpeed. Cargar una ameba ya empieza a virar el
;; color hacia la parada siguiente; si se aparta la vista, vuelve un poco. Solo repinta si cambio.
(fn FcEnv (Dt)
  (S EnvP (Math|Interpolation|FInterpTo :Current (G EnvP) :Target (G LightSum) :DeltaTime Dt :InterpSpeed (G EnvSpeed)))
  (bind nh (Utilities|Array|Length (G EnvHue)))
  (Utilities|IsValid (G Fluid)
    (:"Is Valid"
      (CallFunction|FcEnvBase)
      (if (and (> (Math|Float|Absolute(Float) (- (G EnvP) (G EnvShown))) 0.002) (and (>= nh 2) (and (== (Utilities|Array|Length (G EnvSat)) nh) (== (Utilities|Array|Length (G EnvBright)) nh))))
        (S EnvShown (G EnvP))
        (CallFunction|FcEnvPaint)))))

;;@ FcEnvBase
;; Una vez: guarda los colores del fluido tal como los dejo el autor (la parada 0 es ESA paleta): FluidTop, FluidMid,
;; FluidBottom, GlowColor, MoteColor, CellHigh, CellLow (alfa = CellContrast), CellFill.
(fn FcEnvBase ()
  (if (== (Utilities|Array|Length (G EnvBase)) 0)
    (bind f (G Fluid))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetFluidTop f))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetFluidMid f))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetFluidBottom f))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetGlowColor f))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetMoteColor f))
    (Utilities|Array|Add (G EnvBase) (Math|Color|NewOpacity(LinearColor) (Class|BPFluidMediumSC|GetCellHigh f) 1.0))
    (Utilities|Array|Add (G EnvBase) (Math|Color|NewOpacity(LinearColor) (Class|BPFluidMediumSC|GetCellLow f) (Class|BPFluidMediumSC|GetCellContrast f)))
    (Utilities|Array|Add (G EnvBase) (Class|BPFluidMediumSC|GetCellFill f))))

;;@ FcEnvPaint
;; Entre la parada k y k+1 (smoothstep): giro de tono EnvHue (grados), saturacion EnvSat y brillo EnvBright. Los colores del
;; medio, la luz y las motas van a las variables del fluido (las publica el en su Tick); las celulas lejanas, directo a
;; MPC_Fluid_SC (el fluido solo las publica al arrancar).
(fn FcEnvPaint ()
  (bind n (- (Utilities|Array|Length (G EnvHue)) 1))
  (bind p (Math|Float|Clamp(Float) (G EnvShown) 0.0 (Math|Conversions|ToFloat(Integer) n)))
  (bind k (Math|Integer|Min(Integer) (Math|Float|Floor p) (- n 1)))
  (bind t0 (Math|Float|Clamp(Float) (- p (Math|Conversions|ToFloat(Integer) k))))
  (bind t (* (* t0 t0) (- 3.0 (* 2.0 t0))))
  (S EnvH (Math|Float|Lerp (Utilities|Array|Get(acopy) (G EnvHue) k) (Utilities|Array|Get(acopy) (G EnvHue) (+ k 1)) t))
  (S EnvS (Math|Float|Lerp (Utilities|Array|Get(acopy) (G EnvSat) k) (Utilities|Array|Get(acopy) (G EnvSat) (+ k 1)) t))
  (S EnvB (Math|Float|Lerp (Utilities|Array|Get(acopy) (G EnvBright) k) (Utilities|Array|Get(acopy) (G EnvBright) (+ k 1)) t))
  (bind f (G Fluid))
  (Class|BPFluidMediumSC|SetFluidTop :self f :FluidTop (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 0)))
  (Class|BPFluidMediumSC|SetFluidMid :self f :FluidMid (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 1)))
  (Class|BPFluidMediumSC|SetFluidBottom :self f :FluidBottom (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 2)))
  (Class|BPFluidMediumSC|SetGlowColor :self f :GlowColor (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 3)))
  (Class|BPFluidMediumSC|SetMoteColor :self f :MoteColor (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 4)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellHigh" :ParameterValue (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 5)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellLow" :ParameterValue (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 6)))
  (Rendering|Material|SetVectorParameterValue :Collection "/Game/SoulCharger/Mechanics/Fluid/MPC_Fluid_SC.MPC_Fluid_SC" :ParameterName "CellFill" :ParameterValue (CallFunction|FcHue :C (Utilities|Array|Get(acopy) (G EnvBase) 7))))

;;@ FcHue
;; Gira el tono de C en EnvH grados, multiplica su saturacion por EnvS y su valor por EnvB. Conserva el alfa.
(fn FcHue (C)
  (bind (h s v a) (Utilities|Struct|BreakLinearColor (Math|Color|RGBtoHSV(LinearColor) C)))
  (return (Math|Color|HSVtoRGBlinearcolor (Math|Color|MakeColor (Math|Float|%(Float) (+ (+ h (G EnvH)) 720.0) 360.0) (Math|Float|Clamp(Float) (* s (G EnvS)) 0.0 1.0) (* v (G EnvB)) a))))
