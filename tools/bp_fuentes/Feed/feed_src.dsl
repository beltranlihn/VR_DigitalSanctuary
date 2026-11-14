;; BP_FeedDirector_SC (Test_Feed, 2026-10-29) - fuente de los grafos. (G X) = getter, (S X v) = setter; gen_feed_dsl.py
;; los expande con la categoria de cada variable y escribe feed_dsl.json. Un bloque ;;@ = un grafo.
;; Mecanica (Beltran 10-29): una ameba principal al frente (BP_LovingCell_SC) y una constelacion de amebitas de colores
;; (BP_ProtoSoul_SC), cada una con su nombre (Love, Awareness...). Se cargan sosteniendo la mirada; al cargarse, la amebita
;; desaparece y se vuelve particulas que viajan a la ameba principal, que se alimenta: crece, se agita y se ilumina.
;; El director nunca toca los grafos de la celula ni de la protoameba: les escribe variables y llama sus verbos (Appear,
;; Disappear). Copia de BP_FocusDirector_SC en la mirada, la carga, el punto y la ameba.

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|FdBoot))
(event EventTick (DeltaSeconds)
  (CallFunction|FdStep :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

;;@ FdBoot
;; La ameba principal (FdBootMain); por concepto: estado, su tamano, borde y giro propios (la carga los multiplica), su color
;; (CoreColor: el de sus particulas), su nube de particulas (apagada) y su titulo (plano con su MI de titulo liquido, debajo de
;; la amebita, mirando a EyePos, oculto). El punto de foco.
(fn FdBoot ()
  (CallFunction|FdBootMain)
  (for i (range (Utilities|Array|Length (G Concepts)))
    (bind p (Utilities|Array|Get(acopy) (G Concepts) i))
    (Utilities|Array|Add (G Charge) 0.0)
    (Utilities|Array|Add (G Consumed) false)
    (Utilities|Array|Add (G Reveal) 0.0)
    (Utilities|Array|Add (G RevealAt) -1.0)
    (Utilities|Array|Add (G ConsumeAt) -1.0)
    (Utilities|Array|Add (G FeedAt) -1.0)
    (Utilities|Array|Add (G FlyState) 0)
    (Utilities|Array|Add (G Excite) 0.0)
    (Utilities|Array|Add (G MoteF) 0.0)
    (Utilities|Array|Add (G MoteOn) false)
    (Utilities|Array|Add (G BaseSize) (Class|BPProtoSoulSC|GetSize p))
    (Utilities|Array|Add (G BaseEdge) (Class|BPProtoSoulSC|GetEdgeIntensity p))
    (Utilities|Array|Add (G BaseSpin) (Class|BPProtoSoulSC|GetSpinSpeed p))
    (Utilities|Array|Add (G CCol) (Class|BPProtoSoulSC|GetCoreColor p))
    (Utilities|Array|Add (G Motes) (Niagara|SpawnSystematLocation :SystemTemplate (G MoteSystem) :Location (Transformation|GetActorLocation :self p) :bAutoDestroy false :bAutoActivate false))
    (bind tl (- (Transformation|GetActorLocation :self p) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (G TitleDrop))))
    (bind t (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
    (Transformation|SetMobility t "Movable")
    (Transformation|SetAbsolute t true true true)
    (Components|StaticMesh|SetStaticMesh t (G TitleMesh))
    (Rendering|Material|SetMaterial t 0 (Utilities|Array|Get(acopy) (G TitleMats) i))
    (Collision|SetCollisionEnabled t "NoCollision")
    (Rendering|SetCastShadow t false)
    (Rendering|SetTranslucentSortPriority t 110)
    (Transformation|SetWorldLocationAndRotation t tl (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator :Roll 90.0 :Pitch 0.0 :Yaw 90.0) (Math|Rotator|MakeRotfromX (- tl (G EyePos)))))
    (Transformation|SetWorldScale3D t (Math|Vector|MakeVector :X (* 4.0 (G TitleScale)) :Y (G TitleScale) :Z 1.0))
    (Rendering|Material|SetScalarParameterValueonMaterials t "Reveal" 0.0)
    (Rendering|Material|SetScalarParameterValueonMaterials t "Out" 0.0)
    (Rendering|SetVisibility t false false)
    (Utilities|Array|Add (G TitleComps) t))
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
  (S HintI -1)
  (S Phase 0)
  (S Clock 0.0)
  (S MainRevealAt -1.0)
  (S LastFeedAt -1.0)
  (S LightP -1.0))

;;@ FdBootMain
;; La ameba principal: su lugar, giro, escala, vida propia (BaseLife = NoiseAmount, StrandCurl, OrganicMotion, FloatAmount de la
;; instancia; BasePulse), 6 colores (OrigCol) y su deriva sorteada (WF, WP). Nace oculta y dormida.
(fn FdBootMain ()
  (bind c (G Main))
  (Utilities|IsValid c
    (:"Is Valid"
      (S MainHome (Transformation|GetActorLocation :self c))
      (S MainRot (Transformation|GetActorRotation :self c))
      (S MainSc (Transformation|GetActorScale3D :self c))
      (S BaseLife (Math|Color|MakeColor (Class|BPLovingCellSC|GetNoiseAmount c) (Class|BPLovingCellSC|GetStrandCurl c) (Class|BPLovingCellSC|GetOrganicMotion c) (Class|BPLovingCellSC|GetFloatAmount c)))
      (S BasePulse (Class|BPLovingCellSC|GetPulseSpeed c))
      (S WF (Math|Vector|MakeVector :X (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5) :Y (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5) :Z (Math|Random|RandomFloatinRange :Min 0.6 :Max 1.5)))
      (S WP (Math|Vector|MakeVector :X (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853) :Y (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853) :Z (Math|Random|RandomFloatinRange :Min 0.0 :Max 6.2831853)))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetAmoebaColor1 c))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetAmoebaColor2 c))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetMembraneColor c))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetMembraneRim c))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetOuterColor c))
      (Utilities|Array|Add (G OrigCol) (Class|BPLovingCellSC|GetDustColor c))
      (Rendering|SetActorHiddenInGame :self c :bNewHidden true)
      (CallFunction|FdLook :L 0.0))))

;;@ FdStep
;; Un cuadro: mirada -> carga y fases -> cada concepto (aparicion, brillo, titulo, particulas) -> la ameba principal -> punto
;; -> el fluido sigue la luz de la ameba.
(fn FdStep (Dt)
  (S Clock (+ (G Clock) Dt))
  (S PhaseT (+ (G PhaseT) Dt))
  (CallFunction|FdGaze)
  (CallFunction|FdCharge :Dt Dt)
  (for i (range (Utilities|Array|Length (G Concepts)))
    (CallFunction|FdConcept :I i :Dt Dt))
  (CallFunction|FdMain :Dt Dt)
  (CallFunction|FdDot :Dt Dt)
  (Utilities|IsValid (G Fluid)
    (:"Is Valid"
      (Class|BPFluidMediumSC|SetFakeEEG :self (G Fluid) :bFakeEEG false)
      (Class|BPFluidMediumSC|SetEEG :self (G Fluid) :EEG (Math|Float|Lerp (G FluidCalm) (G FluidActive) (G LightSum))))))

;;@ FdGaze
;; Target = el concepto visible y sin consumir mas centrado dentro del cono (GazeDeg para entrar, GazeOut para el que ya se
;; mira). DebugTarget >= 0 lo fuerza. bDebugAuto (prueba sin visor): mira el de la pista 6 s de cada 8.
(fn FdGaze ()
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
          (for i (range (Utilities|Array|Length (G Concepts)))
            (bind d (Math|Vector|DotProduct (Math|Vector|Normalize (- (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Concepts) i)) cl)) fw))
            (if (and (and (>= (Utilities|Array|Get(acopy) (G Reveal) i) 0.9) (not (Utilities|Array|Get(acopy) (G Consumed) i))) (and (>= d (Math|Trig|Cos(Degrees) (select (== i (G Target)) (G GazeOut) (G GazeDeg)))) (> d (G GBestDot))))
              (S GBestDot d)
              (S GBest i)))
          (S Target (G GBest)))
        (:"Is Not Valid"
          (S Target -1)))))))

;;@ FdCharge
;; Sube la carga del concepto mirado en HoldTime s; los otros bajan FadeBack veces mas lento. Al 100 %: FdConsume. Excite = la
;; carga mientras se lo mira, suavizada (el latido de su brillo). La pista: el primer concepto visible sin consumir. Fases:
;; 0 espera StartDelay -> 1 aparece la ameba -> (ConceptDelay) 2 aparecen los conceptos -> todos comidos y absorbidos ->
;; 3 FinaleSound -> FinaleHold -> 4 bStageDone.
(fn FdCharge (Dt)
  (bind ht (Math|Float|Max(Float) (G HoldTime) 0.1))
  (S HintI -1)
  (for i (range (Utilities|Array|Length (G Concepts)))
    (bind cs (Utilities|Array|Get(acopy) (G Consumed) i))
    (bind rv (Utilities|Array|Get(acopy) (G Reveal) i))
    (bind c (Utilities|Array|Get(acopy) (G Charge) i))
    (bind on (and (== i (G Target)) (and (>= rv 0.9) (not cs))))
    (Utilities|Array|SetArrayElem (G Charge) i (select cs 1.0 (Math|Float|Clamp(Float) (select on (+ c (/ Dt ht)) (- c (/ (* Dt (G FadeBack)) ht))))) true)
    (Utilities|Array|SetArrayElem (G Excite) i (Math|Interpolation|FInterpTo :Current (Utilities|Array|Get(acopy) (G Excite) i) :Target (select on (Utilities|Array|Get(acopy) (G Charge) i) 0.0) :DeltaTime Dt :InterpSpeed (G ExciteSpeed)) true)
    (if (and (not cs) (>= (Utilities|Array|Get(acopy) (G Charge) i) 1.0))
      (CallFunction|FdConsume :I i)
      (elif (and (== (G HintI) -1) (and (not cs) (>= rv 0.9)))
        (S HintI i))))
  (S NoLook (select (>= (G Target) 0) 0.0 (+ (G NoLook) Dt)))
  (if (and (== (G Phase) 0) (>= (G Clock) (G StartDelay)))
    (S MainRevealAt (G Clock))
    (S Phase 1)
    (elif (and (== (G Phase) 1) (>= (G Clock) (+ (G MainRevealAt) (G ConceptDelay))))
      (CallFunction|FdRevealConcepts)
      (S Phase 2)
      (elif (and (== (G Phase) 2) (and (>= (G Fed) (Utilities|Array|Length (G Concepts))) (>= (G FedShown) (- (Math|Conversions|ToFloat(Integer) (G Fed)) 0.03))))
        (S Phase 3)
        (S PhaseT 0.0)
        (CallFunction|FdSound :Snd (G FinaleSound))
        (elif (and (== (G Phase) 3) (>= (G PhaseT) (G FinaleHold)))
          (S Phase 4)
          (S StageDone true))))))

;;@ FdRevealConcepts
;; Programa la aparicion de los conceptos, uno cada ConceptGap s.
(fn FdRevealConcepts ()
  (for i (range (Utilities|Array|Length (G Concepts)))
    (Utilities|Array|SetArrayElem (G RevealAt) i (+ (G Clock) (* (Math|Conversions|ToFloat(Integer) i) (G ConceptGap))) true)))

;;@ FdConsume
;; El concepto I se carga del todo: desaparece (su Disappear, ya animado) y su nube pasa a VUELO: el emisor viaja de la
;; amebita a la ameba principal (FdFly) a FlySpeed cm/s, en arco, dejando una estela de polvo de su color (FlyRate, vida
;; FlyTime s) que la ameba atrae (Push hacia ella). La comida llega (FeedAt) cuando el emisor arriba. Vibran los dos mandos.
;; (Pull NO sirve para esto: es radial desde el propio emisor, no hacia Target.)
(fn FdConsume (I)
  (bind p (Utilities|Array|Get(acopy) (G Concepts) I))
  (Utilities|Array|SetArrayElem (G Consumed) I true true)
  (Utilities|Array|SetArrayElem (G ConsumeAt) I (G Clock) true)
  (Class|BPProtoSoulSC|Disappear :self p)
  (Utilities|Array|SetArrayElem (G FeedAt) I (+ (G Clock) (Math|Float|Max(Float) (/ (Math|Vector|Distance(Vector) (Transformation|GetActorLocation :self p) (G MainHome)) (Math|Float|Max(Float) (G FlySpeed) 10.0)) 0.3)) true)
  (Utilities|Array|SetArrayElem (G FlyState) I 1 true)
  (Utilities|Array|SetArrayElem (G MoteOn) I false true)
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (Niagara|SetNiagaraVariable(Position) m "Target" (G MainHome))
  (Niagara|SetNiagaraVariable(Float) m "Push" (G FlyPush))
  (Niagara|SetNiagaraVariable(Float) m "Pull" 0.0)
  (Niagara|SetNiagaraVariable(Float) m "Radius" (G FlyRadius))
  (Niagara|SetNiagaraVariable(Float) m "Noise" (G FlyNoise))
  (Niagara|SetNiagaraVariable(Float) m "Life" (Math|Float|Max(Float) (G FlyTime) 0.2))
  (Niagara|SetNiagaraVariable(Float) m "SpawnRate" (G FlyRate))
  (Niagara|SetNiagaraVariable(Float) m "Fade" 1.0)
  (Niagara|SetNiagaraVariable(LinearColor) m "OrbColor" (Math|Color|NewOpacity(LinearColor) (Utilities|Array|Get(acopy) (G CCol) I) (G MoteAlpha)))
  (Niagara|SetNiagaraVariable(Float) m "SizeMin" (G MoteSize))
  (Niagara|SetNiagaraVariable(Float) m "SizeMax" (* 2.0 (G MoteSize)))
  (Components|Activation|Activate m false)
  (bind pc (Game|GetPlayerController 0))
  (Utilities|IsValid pc
    (:"Is Valid"
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left")
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right"))))

;;@ FdConcept
;; Un concepto por cuadro. Aparece a su hora (Appear de la protoameba, en el primer cuadro con Clock >= RevealAt: no se
;; compara contra Reveal porque el bind relee el arreglo despues de escribirlo, gotcha del bind); su titulo emerge TitleDelay s despues
;; (barrido liquido en TitleTime s) y se va con el (Out en TitleOutTime s). Mientras no se lo consume: crece (ConceptGrow,
;; en LifeSteps escalones: la protoameba reempuja sus anillos cuando cambia el tamano), enciende el borde (ConceptGlow, con el
;; latido de la carga y la pista) y gira mas rapido (ConceptSpin). Despues, sus particulas (FdMote).
(fn FdConcept (I Dt)
  (bind p (Utilities|Array|Get(acopy) (G Concepts) I))
  (bind ra (Utilities|Array|Get(acopy) (G RevealAt) I))
  (bind rv (select (or (< ra 0.0) (< (G Clock) ra)) 0.0 (Math|Float|Clamp(Float) (/ (- (G Clock) ra) (Math|Float|Max(Float) (G ConceptAppear) 0.1)))))
  (Utilities|Array|SetArrayElem (G Reveal) I rv true)
  (bind cs (Utilities|Array|Get(acopy) (G Consumed) I))
  (bind tc (Utilities|Array|Get(acopy) (G TitleComps) I))
  (bind to (select cs (Math|Float|Clamp(Float) (/ (- (G Clock) (Utilities|Array|Get(acopy) (G ConsumeAt) I)) (Math|Float|Max(Float) (G TitleOutTime) 0.1))) 0.0))
  (Rendering|SetVisibility tc (and (> rv 0.0) (< to 1.0)) false)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Reveal" (select (> rv 0.0) (Math|Float|Clamp(Float) (/ (- (- (G Clock) ra) (G TitleDelay)) (Math|Float|Max(Float) (G TitleTime) 0.1))) 0.0))
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Out" to)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "LT" (Math|Float|Max(Float) (- (G Clock) ra) 0.0))
  (CallFunction|FdMote :I I :Dt Dt)
  (if (and (>= ra 0.0) (and (>= (G Clock) ra) (< (- (G Clock) Dt) ra)))
    (Class|BPProtoSoulSC|Appear :self p)
    (elif (and (> rv 0.0) (not cs))
      (bind ch (Utilities|Array|Get(acopy) (G Charge) I))
      (bind e (* (* ch ch) (- 3.0 (* 2.0 ch))))
      (bind ns (Math|Float|Max(Float) (G LifeSteps) 1.0))
      (bind qe (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* e ns))) ns))
      (bind hp (* (G HintLight) (* (Math|Float|Clamp(Float) (/ (- (G NoLook) (G HintDelay)) 2.0)) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G HintHz) (G Clock)))))))))
      (bind cp (* (G ChargePulse) (* (Utilities|Array|Get(acopy) (G Excite) I) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G ChargePulseHz) (G Clock)))))))))
      (Class|BPProtoSoulSC|SetSize :self p :Size (* (Utilities|Array|Get(acopy) (G BaseSize) I) (+ 1.0 (* (G ConceptGrow) qe))))
      (Class|BPProtoSoulSC|SetEdgeIntensity :self p :EdgeIntensity (* (Utilities|Array|Get(acopy) (G BaseEdge) I) (+ 1.0 (* (G ConceptGlow) (+ (+ e cp) (select (== I (G HintI)) hp 0.0))))))
      (Class|BPProtoSoulSC|SetSpinSpeed :self p :SpinSpeed (+ (Utilities|Array|Get(acopy) (G BaseSpin) I) (* (G ConceptSpin) e))))))

;;@ FdMote
;; Las particulas del concepto I. Consumido: el vuelo (FdFly). Si no: la nube de la carga (la de Test_Focus): mientras se lo
;; mira nacen en una cascara de MoteRadius cm y MotePull las atrae a su centro, mas con mas carga; al apartar la vista se
;; sueltan (MoteRelease) y se apagan en MoteFade s. Solo trabaja el concepto con la nube prendida o apagandose.
(fn FdMote (I Dt)
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (bind want (and (== I (G Target)) (and (not (Utilities|Array|Get(acopy) (G Consumed) I)) (>= (Utilities|Array|Get(acopy) (G Reveal) I) 0.9))))
  (Utilities|IsValid m
    (:"Is Valid"
      (if (Utilities|Array|Get(acopy) (G Consumed) I)
        (CallFunction|FdFly :I I)
        (elif (or want (or (> (Utilities|Array|Get(acopy) (G MoteF) I) 0.0) (Utilities|Array|Get(acopy) (G MoteOn) I)))
          (CallFunction|FdMoteEdge :I I :Want want)
          (Utilities|Array|SetArrayElem (G MoteF) I (Math|Float|Clamp(Float) (+ (Utilities|Array|Get(acopy) (G MoteF) I) (/ (* Dt (select want 1.0 -1.0)) (Math|Float|Max(Float) (G MoteFade) 0.05)))) true)
          (bind f (Utilities|Array|Get(acopy) (G MoteF) I))
          (Niagara|SetNiagaraVariable(Float) m "SpawnRate" (select want (* (G MoteRate) (+ 0.3 (* 0.7 (Utilities|Array|Get(acopy) (G Charge) I)))) 0.0))
          (Niagara|SetNiagaraVariable(Float) m "Fade" (* (* f f) (- 3.0 (* 2.0 f))))
          (if (and (not want) (<= f 0.0))
            (Components|Activation|Deactivate m)))))))

;;@ FdMoteEdge
;; El cambio de estado de la nube de la carga: al prenderse copia las perillas (color del concepto, vida, tamanos, radio,
;; ruido, Target = el concepto) y la activa; al apagarse las suelta hacia afuera.
(fn FdMoteEdge (I Want)
  (bind was (Utilities|Array|Get(acopy) (G MoteOn) I))
  (if (or (and Want (not was)) (and (not Want) was))
    (Utilities|Array|SetArrayElem (G MoteOn) I Want true)
    (bind m (Utilities|Array|Get(acopy) (G Motes) I))
    (Niagara|SetNiagaraVariable(Float) m "Push" (select Want (G MotePull) (* -1.0 (G MoteRelease))))
    (if Want
      (Niagara|SetNiagaraVariable(Position) m "Target" (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Concepts) I)))
      (Niagara|SetNiagaraVariable(LinearColor) m "OrbColor" (Math|Color|NewOpacity(LinearColor) (Utilities|Array|Get(acopy) (G CCol) I) (G MoteAlpha)))
      (Niagara|SetNiagaraVariable(Float) m "Life" (Math|Float|Max(Float) (G MoteLife) 0.2))
      (Niagara|SetNiagaraVariable(Float) m "SizeMin" (G MoteSize))
      (Niagara|SetNiagaraVariable(Float) m "SizeMax" (* 2.0 (G MoteSize)))
      (Niagara|SetNiagaraVariable(Float) m "Radius" (G MoteRadius))
      (Niagara|SetNiagaraVariable(Float) m "Noise" (G MoteNoise))
      (if (or (not (Components|Activation|IsActive m)) (<= (Utilities|Array|Get(acopy) (G MoteF) I) 0.0))
        (Components|Activation|Activate m true)))))

;;@ FdFly
;; El vuelo del concepto I (FlyState): 1 el emisor viaja de la amebita a la ameba (smoothstep, arco de FlyArc cm hacia arriba)
;; -> llega en FeedAt: deja de nacer, Fed + 1, FeedSound, destello de la ameba -> 3 mueren las ultimas (FlyTime s) -> 4 se
;; apaga la nube.
(fn FdFly (I)
  (bind st (Utilities|Array|Get(acopy) (G FlyState) I))
  (bind ca (Utilities|Array|Get(acopy) (G ConsumeAt) I))
  (bind fa (Utilities|Array|Get(acopy) (G FeedAt) I))
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (if (== st 1)
    (bind t (Math|Float|Clamp(Float) (/ (- (G Clock) ca) (Math|Float|Max(Float) (- fa ca) 0.1))))
    (Transformation|SetWorldLocation m (+ (Math|Vector|Lerp(Vector) (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Concepts) I)) (G MainHome) (* (* t t) (- 3.0 (* 2.0 t)))) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (* (G FlyArc) (Math|Trig|Sin(Radians) (* 3.1415927 t))))))
    (if (>= t 1.0)
      (Niagara|SetNiagaraVariable(Float) m "SpawnRate" 0.0)
      (Utilities|Array|SetArrayElem (G FlyState) I 3 true)
      (S Fed (+ (G Fed) 1))
      (S LastFeedAt (G Clock))
      (CallFunction|FdSound :Snd (G FeedSound)))
    (elif (and (== st 3) (>= (G Clock) (+ fa (+ (G FlyTime) 0.4))))
      (Utilities|Array|SetArrayElem (G FlyState) I 4 true)
      (Components|Activation|Deactivate m))))

;;@ FdMain
;; La ameba principal se alimenta: e = smoothstep de lo comido (FedShown / conceptos, suavizado con FeedSpeed). Aparece con
;; ease-out-back en RevealTime s, crece de SleepScale a 1, pasa de SleepState a AwakeState y su Agitation de SleepAgit a
;; AwakeAgit. Cada comida que llega es un destello (bl, BloomTime s): luz BloomLight, escala BloomScale, agitacion FeedAgit y
;; vida FeedLife / FeedCurl. Su VIDA (ruido, OrganicMotion, FloatAmount, respiracion) se multiplica por 1 -> AwakeLife con e;
;; sus BRAZOS (StrandCurl) por 1 -> AwakeCurl; lo que va al shader en LifeSteps escalones. Deriva y se balancea con sus
;; frecuencias y fases (WF, WP), mas amplio despierta. El color se empuja solo si la luz cambio.
(fn FdMain (Dt)
  (bind c (G Main))
  (Utilities|IsValid c
    (:"Is Valid"
      (S FedShown (Math|Interpolation|FInterpTo :Current (G FedShown) :Target (Math|Conversions|ToFloat(Integer) (G Fed)) :DeltaTime Dt :InterpSpeed (G FeedSpeed)))
      (bind ch (Math|Float|Clamp(Float) (/ (G FedShown) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length (G Concepts))) 1.0))))
      (bind e (* (* ch ch) (- 3.0 (* 2.0 ch))))
      (bind ra (G MainRevealAt))
      (bind rv (select (< ra 0.0) 0.0 (Math|Float|Clamp(Float) (/ (- (G Clock) ra) (Math|Float|Max(Float) (G RevealTime) 0.1)))))
      (bind bt (select (< (G LastFeedAt) 0.0) 99.0 (- (G Clock) (G LastFeedAt))))
      (bind bk (Math|Float|Clamp(Float) (/ bt (Math|Float|Max(Float) (G BloomTime) 0.1))))
      (bind bl (* (* (- 1.0 bk) (- 1.0 bk)) (Math|Float|Clamp(Float) (/ bt 0.15))))
      (bind L (+ e (* (G BloomLight) bl)))
      (S LightSum e)
      (bind xr (- rv 1.0))
      (bind rb (Math|Float|Max(Float) (+ 1.0 (+ (* 1.8 (* (* xr xr) xr)) (* 0.8 (* xr xr)))) 0.001))
      (bind sc (* rb (* (Math|Float|Lerp (G SleepScale) 1.0 e) (+ 1.0 (* (G BloomScale) bl)))))
      (bind ns (Math|Float|Max(Float) (G LifeSteps) 1.0))
      (bind qe (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* e ns))) ns))
      (bind qx (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* bl ns))) ns))
      (bind ml (+ 1.0 (+ (* (- (G AwakeLife) 1.0) qe) (* (G FeedLife) qx))))
      (bind mk (+ 1.0 (+ (* (- (G AwakeCurl) 1.0) qe) (* (G FeedCurl) qx))))
      (bind mf (+ 1.0 (+ (* (- (G AwakeLife) 1.0) e) (* (G FeedLife) bl))))
      (bind (lN lK lM lF) (Utilities|Struct|BreakLinearColor (G BaseLife)))
      (bind wf (G WF))
      (bind wp (G WP))
      (bind tw (* (* 6.2831853 (G DriftHz)) (G Clock)))
      (bind amp (Math|Float|Lerp (G DriftSleep) 1.0 e))
      (bind dr (Math|Vector|MakeVector :X (+ (Math|Trig|Sin(Radians) (+ (* tw (.x wf)) (.x wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.x wf))) (* 2.0 (.y wp)))))) :Y (+ (Math|Trig|Sin(Radians) (+ (* tw (.y wf)) (.y wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.y wf))) (* 2.0 (.z wp)))))) :Z (* 0.7 (+ (Math|Trig|Sin(Radians) (+ (* tw (.z wf)) (.z wp))) (* 0.5 (Math|Trig|Sin(Radians) (+ (* tw (* 2.236 (.z wf))) (* 2.0 (.x wp)))))))))
      (Transformation|SetActorLocation :self c :NewLocation (+ (G MainHome) (* dr (* (G DriftAmp) amp))))
      (bind hr (G MainRot))
      (bind wr (* (G WanderRot) amp))
      (Transformation|SetActorRotation :self c :NewRotation (Math|Rotator|MakeRotator :Roll (+ (.roll hr) (* wr (Math|Trig|Sin(Radians) (+ (* tw (* 0.83 (.y wf))) (.z wp))))) :Pitch (+ (.pitch hr) (* (* 0.6 wr) (Math|Trig|Sin(Radians) (+ (* tw (* 0.71 (.z wf))) (.x wp))))) :Yaw (+ (.yaw hr) (* wr (Math|Trig|Sin(Radians) (+ (* tw (* 0.67 (.x wf))) (.y wp)))))))
      (Transformation|SetActorScale3D :self c :NewScale3D (* (G MainSc) sc))
      (Rendering|SetActorHiddenInGame :self c :bNewHidden (<= rv 0.0))
      (Class|BPLovingCellSC|SetGlobalState :self c :GlobalState (Math|Float|Lerp (G SleepState) (G AwakeState) e))
      (Class|BPLovingCellSC|SetAgitation :self c :Agitation (+ (Math|Float|Lerp (G SleepAgit) (G AwakeAgit) e) (* (G FeedAgit) bl)))
      (Class|BPLovingCellSC|SetNoiseAmount :self c :NoiseAmount (Math|Float|Min(Float) (* lN ml) 2.0))
      (Class|BPLovingCellSC|SetStrandCurl :self c :StrandCurl (Math|Float|Min(Float) (* lK mk) 2.0))
      (Class|BPLovingCellSC|SetOrganicMotion :self c :OrganicMotion (* lM ml))
      (Class|BPLovingCellSC|SetFloatAmount :self c :FloatAmount (* lF mf))
      (Class|BPLovingCellSC|SetPulseSpeed :self c :PulseSpeed (* (G BasePulse) mf))
      (if (> (Math|Float|Absolute(Float) (- L (G LightP))) 0.004)
        (S LightP L)
        (CallFunction|FdLook :L L)))))

;;@ FdLook
;; Pinta la ameba principal con luz L (0 dormida, 1 despierta, > 1 destello) sobre sus colores originales, con las perillas de
;; la celula y su propio PushLook; la envoltura y el polvo van directo al material.
(fn FdLook (L)
  (bind c (G Main))
  (Class|BPLovingCellSC|SetAmoebaColor1 :self c :AmoebaColor1 (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 0) :L L))
  (Class|BPLovingCellSC|SetAmoebaColor2 :self c :AmoebaColor2 (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 1) :L L))
  (Class|BPLovingCellSC|SetMembraneColor :self c :MembraneColor (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 2) :L L))
  (Class|BPLovingCellSC|SetMembraneRim :self c :MembraneRim (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 3) :L L))
  (Class|BPLovingCellSC|SetOuterColor :self c :OuterColor (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 4) :L L))
  (Class|BPLovingCellSC|SetDustColor :self c :DustColor (CallFunction|FdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 5) :L L))
  (Class|BPLovingCellSC|PushLook :self c)
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetOuterShell c) "OuterCol" (Math|Color|NewOpacity(LinearColor) (Class|BPLovingCellSC|GetOuterColor c) (Class|BPLovingCellSC|GetOuterOpacity c)))
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetDust c) "DustCol" (Class|BPLovingCellSC|GetDustColor c)))

;;@ FdMix
;; Color dormido = lerp(original, SleepTint, SleepMix) * SleepDim; con luz L vuelve al original (L > 1 lo pasa: destello). Conserva el alfa.
(fn FdMix (C L)
  (bind (r g b a) (Utilities|Struct|BreakLinearColor C))
  (return (Math|Color|NewOpacity(LinearColor) (Math|Color|Lerp(LinearColor) (* (Math|Color|Lerp(LinearColor) C (G SleepTint) (G SleepMix)) (G SleepDim)) C L) a)))

;;@ FdDot
;; El punto de foco: frente a la vista, a la distancia del concepto mirado (para no verlo doble), con angulo fijo DotAngle.
;; El anillo aparece al mirar un concepto y se cierra con su carga. Se va en el final.
(fn FdDot (Dt)
  (bind cm (Game|GetPlayerCameraManager 0))
  (Utilities|IsValid cm
    (:"Is Valid"
      (bind cl (Camera|GetCameraLocation cm))
      (bind fw (Math|Vector|GetForwardVector (Camera|GetCameraRotation cm)))
      (bind t (G Target))
      (bind ti (Math|Integer|Max(Integer) t 0))
      (bind on (and (>= t 0) (not (Utilities|Array|Get(acopy) (G Consumed) ti))))
      (S DotD (Math|Interpolation|FInterpTo :Current (G DotD) :Target (select (>= t 0) (Math|Float|Max(Float) (- (Math|Vector|Distance(Vector) cl (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Concepts) ti))) 15.0) 40.0) (G DotIdle)) :DeltaTime Dt :InterpSpeed 6.0))
      (S DotRing (Math|Interpolation|FInterpTo :Current (G DotRing) :Target (select on 1.0 0.0) :DeltaTime Dt :InterpSpeed 8.0))
      (bind dc (G DotComp))
      (Transformation|SetWorldLocationAndRotation dc (+ cl (* fw (G DotD))) (Math|Rotator|MakeRotfromZ (* fw -1.0)))
      (Transformation|SetWorldScale3D dc (* (Math|Vector|MakeVector :X 1.0 :Y 1.0 :Z 1.0) (* (G DotD) (* 0.01 (Math|Trig|Tan(Degrees) (G DotAngle))))))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Progress" (select (>= t 0) (Utilities|Array|Get(acopy) (G Charge) ti) 0.0))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Ring" (G DotRing))
      (Rendering|Material|SetScalarParameterValueonMaterials dc "Opacity" (Math|Float|Lerp (G DotIdleOpacity) (G DotOpacity) (G DotRing)))
      (Rendering|SetVisibility dc (< (G Phase) 3) false))))

;;@ FdSound
(fn FdSound (Snd)
  (Utilities|IsValid Snd
    (:"Is Valid"
      (Audio|PlaySound2D :Sound Snd :VolumeMultiplier (G SfxVol)))))
