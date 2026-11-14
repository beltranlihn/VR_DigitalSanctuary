;; BP_ThoughtsDirector_SC (Test_Thoughts, 2026-10-30) - fuente de los grafos. (G X) = getter, (S X v) = setter;
;; gen_thoughts_dsl.py los expande con la categoria de cada variable. Un bloque ;;@ = un grafo.
;; Propuesta de Loving sin sensor (Beltran 10-29/30: "observar para activar cosas", "etereo"), atada a las voces de Alma:
;;   VO_20 "There is nothing to do here... just let go."  -> la ameba se condensa; donde miras, el polvo se junta.
;;   VO_22 "Observe your thoughts like distant constellations... each one quietly forming, then fading."
;;         -> los pensamientos (protoamebas con su palabra) se forman y se desvanecen solos, en lugares al azar (Slots).
;;            Mirarlo: se aclara, emerge su palabra, junta polvo y no se va mientras lo miras. Soltarlo: se desvanece.
;;            Mirar le da luz a la ameba (AttnSum).
;;   VO_23 "Which thought carries a quiet wisdom today?" -> el proximo que sostengas hasta llenarlo es TU pensamiento:
;;   VO_23b "Let's gather all these thoughts..."             viaja en polvo a la ameba y los demas lo siguen; la ameba se
;;            llena y toma un poco de su color; su palabra queda bajo la ameba.
;; Sin anillo de progreso: la respuesta esta en el mundo. Nada se pierde ni se falla; la etapa termina por reloj.
;; Reusa BP_FeedDirector_SC (mirada, ameba, vuelo en polvo, titulos) y la protoameba (Appear/Disappear, su Tick).

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|TdBoot))
(event EventTick (DeltaSeconds)
  (CallFunction|TdStep :Dt (Math|Float|Min(Float) DeltaSeconds 0.05)))

;;@ TdBoot
;; Los lugares (Slots: sus posiciones, libres); por pensamiento: estado, su tamano, borde, giro y
;; color propios, su nube (apagada) y su titulo (plano con su MI, oculto; se ubica al formarse); el titulo del elegido
;; (oculto); el polvo de la mirada (activo, sin nacer). La ameba (TdBootMain) va DESPUES de los pensamientos: su TdLook lee
;; CCol (el color del elegido) y con el arreglo vacio avisa 'index 0 of length 0'.
(fn TdBoot ()
  (for s (range (Utilities|Array|Length (G Slots)))
    (Utilities|Array|Add (G SlotLoc) (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Slots) s)))
    (Utilities|Array|Add (G SlotBusy) false))
  (for i (range (Utilities|Array|Length (G Thoughts)))
    (bind p (Utilities|Array|Get(acopy) (G Thoughts) i))
    (Utilities|Array|Add (G TState) 0)
    (Utilities|Array|Add (G Obs) 0.0)
    (Utilities|Array|Add (G ObsTotal) 0.0)
    (Utilities|Array|Add (G Charge) 0.0)
    (Utilities|Array|Add (G Excite) 0.0)
    (Utilities|Array|Add (G NextAt) -1.0)
    (Utilities|Array|Add (G DieAt) -1.0)
    (Utilities|Array|Add (G ConsumeAt) -1.0)
    (Utilities|Array|Add (G FeedAt) -1.0)
    (Utilities|Array|Add (G FlyState) 0)
    (Utilities|Array|Add (G MoteF) 0.0)
    (Utilities|Array|Add (G MoteOn) false)
    (Utilities|Array|Add (G SlotOf) -1)
    (Utilities|Array|Add (G BaseSize) (Class|BPProtoSoulSC|GetSize p))
    (Utilities|Array|Add (G BaseEdge) (Class|BPProtoSoulSC|GetEdgeIntensity p))
    (Utilities|Array|Add (G BaseSpin) (Class|BPProtoSoulSC|GetSpinSpeed p))
    (Utilities|Array|Add (G CCol) (Class|BPProtoSoulSC|GetCoreColor p))
    (Utilities|Array|Add (G Motes) (Niagara|SpawnSystematLocation :SystemTemplate (G MoteSystem) :Location (Transformation|GetActorLocation :self p) :bAutoDestroy false :bAutoActivate false))
    (bind t (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
    (Transformation|SetMobility t "Movable")
    (Transformation|SetAbsolute t true true true)
    (Components|StaticMesh|SetStaticMesh t (G TitleMesh))
    (Rendering|Material|SetMaterial t 0 (Utilities|Array|Get(acopy) (G TitleMats) i))
    (Collision|SetCollisionEnabled t "NoCollision")
    (Rendering|SetCastShadow t false)
    (Rendering|SetTranslucentSortPriority t 110)
    (Transformation|SetWorldScale3D t (Math|Vector|MakeVector :X (* 4.0 (G TitleScale)) :Y (G TitleScale) :Z 1.0))
    (Rendering|Material|SetScalarParameterValueonMaterials t "Reveal" 0.0)
    (Rendering|Material|SetScalarParameterValueonMaterials t "Out" 0.0)
    (Rendering|SetVisibility t false false)
    (Utilities|Array|Add (G TitleComps) t))
  (CallFunction|TdBootMain)
  (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|SetMobility c "Movable")
  (Transformation|SetAbsolute c true true true)
  (Components|StaticMesh|SetStaticMesh c (G TitleMesh))
  (Collision|SetCollisionEnabled c "NoCollision")
  (Rendering|SetCastShadow c false)
  (Rendering|SetTranslucentSortPriority c 110)
  (Rendering|SetVisibility c false false)
  (S ChosenComp c)
  (bind d (Niagara|SpawnSystematLocation :SystemTemplate (G MoteSystem) :Location (G EyePos) :bAutoDestroy false :bAutoActivate false))
  (Niagara|SetNiagaraVariable(Float) d "Radius" (G DustRadius))
  (Niagara|SetNiagaraVariable(Float) d "Life" (Math|Float|Max(Float) (G MoteLife) 0.2))
  (Niagara|SetNiagaraVariable(Float) d "SizeMin" (G MoteSize))
  (Niagara|SetNiagaraVariable(Float) d "SizeMax" (* 2.0 (G MoteSize)))
  (Niagara|SetNiagaraVariable(Float) d "Noise" (G MoteNoise))
  (Niagara|SetNiagaraVariable(Float) d "Push" (G MotePull))
  (Niagara|SetNiagaraVariable(Float) d "Fade" 1.0)
  (Niagara|SetNiagaraVariable(Float) d "SpawnRate" 0.0)
  (Niagara|SetNiagaraVariable(LinearColor) d "OrbColor" (Math|Color|NewOpacity(LinearColor) (G DustColor) (G DustAlpha)))
  (Components|Activation|Activate d true)
  (S DustComp d)
  (S DustPos (+ (G EyePos) (Math|Vector|MakeVector :X (G DustDist) :Y 0.0 :Z 0.0)))
  (S Target -1)
  (S HintI -1)
  (S Chosen -1)
  (S Phase 0)
  (S Clock 0.0)
  (S MainRevealAt -1.0)
  (S LastFeedAt -1.0)
  (S LightP -1.0))

;;@ TdBootMain
;; La ameba: su lugar, giro, escala, vida propia (BaseLife = NoiseAmount, StrandCurl, OrganicMotion, FloatAmount de la
;; instancia; BasePulse), 6 colores (OrigCol) y su deriva sorteada (WF, WP). Nace oculta y dormida.
(fn TdBootMain ()
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
      (CallFunction|TdLook :L 0.0))))

;;@ TdStep
;; Un cuadro: fases y voces -> mirada -> atencion (mirar un pensamiento ilumina la ameba) -> cada pensamiento -> polvo de la
;; mirada -> la ameba -> el titulo del elegido -> el fluido sigue la luz de la ameba.
(fn TdStep (Dt)
  (S Clock (+ (G Clock) Dt))
  (CallFunction|TdPhase)
  (CallFunction|TdGaze)
  (S AttnSum (+ (G AttnSum) (select (>= (G Target) 0) Dt 0.0)))
  (for i (range (Utilities|Array|Length (G Thoughts)))
    (CallFunction|TdThought :I i :Dt Dt))
  (CallFunction|TdDust :Dt Dt)
  (CallFunction|TdMain :Dt Dt)
  (CallFunction|TdChosenTitle)
  (Utilities|IsValid (G Fluid)
    (:"Is Valid"
      (Class|BPFluidMediumSC|SetFakeEEG :self (G Fluid) :bFakeEEG false)
      (Class|BPFluidMediumSC|SetEEG :self (G Fluid) :EEG (Math|Float|Lerp (G FluidCalm) (G FluidActive) (G LightSum))))))

;;@ TdPhase
;; 0 espera -> StartDelay: se condensa la ameba + VO_20 -> 1 (desde DustAt, el polvo sigue la mirada) -> T22: VO_22, se
;; programan los pensamientos (FormDelay + i FormGap) -> 2 -> T23: VO_23 -> 3: la eleccion se abre ChoiceDelay s despues;
;; si en ChoiceTimeout s nadie eligio, TdAutoChoose -> 4 (TdChoose): se juntan; cuando llega el elegido, FinaleHold s
;; -> 5 bStageDone.
(fn TdPhase ()
  (if (and (== (G Phase) 0) (>= (G Clock) (G StartDelay)))
    (S MainRevealAt (G Clock))
    (CallFunction|TdSound :Snd (Utilities|Array|Get(acopy) (G VoLines) 0) :Vol (G VoVol))
    (S Phase 1)
    (elif (and (== (G Phase) 1) (>= (G Clock) (G T22)))
      (CallFunction|TdSound :Snd (Utilities|Array|Get(acopy) (G VoLines) 1) :Vol (G VoVol))
      (for i (range (Utilities|Array|Length (G Thoughts)))
        (Utilities|Array|SetArrayElem (G NextAt) i (+ (G Clock) (+ (G FormDelay) (* (Math|Conversions|ToFloat(Integer) i) (G FormGap)))) true))
      (S FormOn true)
      (S Phase 2)
      (elif (and (== (G Phase) 2) (>= (G Clock) (G T23)))
        (CallFunction|TdSound :Snd (Utilities|Array|Get(acopy) (G VoLines) 2) :Vol (G VoVol))
        (S Phase 3)
        (elif (== (G Phase) 3)
          (S ChoiceOn (>= (G Clock) (+ (G T23) (G ChoiceDelay))))
          (if (>= (G Clock) (+ (+ (G T23) (G ChoiceDelay)) (G ChoiceTimeout)))
            (CallFunction|TdAutoChoose))
          (elif (and (== (G Phase) 4) (and (G ChosenIn) (>= (G Clock) (+ (G ChosenInAt) (G FinaleHold)))))
            (S Phase 5)
            (S StageDone true)))))))

;;@ TdGaze
;; HintI = un pensamiento vivo, distinto cada 8 s (la prueba sin visor lo mira 6 s de cada 8). Target = el pensamiento vivo
;; y ya formado (AppearT >= 0,8) mas centrado dentro del cono (GazeDeg para entrar, GazeOut para el que ya se mira).
;; DebugTarget >= 0 lo fuerza.
(fn TdGaze ()
  (bind cm (Game|GetPlayerCameraManager 0))
  (bind n (Math|Integer|Max(Integer) (Utilities|Array|Length (G Thoughts)) 1))
  (S GBest -1)
  (S GBestDot -2.0)
  (S HintI -1)
  (for k (range (Utilities|Array|Length (G Thoughts)))
    (bind j (Math|Integer|%(Integer) (+ (Math|Integer|%(Integer) (Math|Float|Floor (/ (G Clock) 8.0)) n) k) n))
    (if (and (== (G HintI) -1) (and (== (Utilities|Array|Get(acopy) (G TState) j) 1) (>= (Class|BPProtoSoulSC|GetAppearT (Utilities|Array|Get(acopy) (G Thoughts) j)) 0.8)))
      (S HintI j)))
  (if (>= (G DebugTarget) 0)
    (S Target (G DebugTarget))
    (elif (G DebugAuto)
      (S Target (select (< (Math|Float|Fraction (/ (G Clock) 8.0)) 0.75) (G HintI) -1))
    (else
      (Utilities|IsValid cm
        (:"Is Valid"
          (bind cl (Camera|GetCameraLocation cm))
          (bind fw (Math|Vector|GetForwardVector (Camera|GetCameraRotation cm)))
          (for i (range (Utilities|Array|Length (G Thoughts)))
            (bind p (Utilities|Array|Get(acopy) (G Thoughts) i))
            (bind d (Math|Vector|DotProduct (Math|Vector|Normalize (- (Transformation|GetActorLocation :self p) cl)) fw))
            (if (and (and (== (Utilities|Array|Get(acopy) (G TState) i) 1) (>= (Class|BPProtoSoulSC|GetAppearT p) 0.8)) (and (>= d (Math|Trig|Cos(Degrees) (select (== i (G Target)) (G GazeOut) (G GazeDeg)))) (> d (G GBestDot))))
              (S GBestDot d)
              (S GBest i)))
          (S Target (G GBest)))
        (:"Is Not Valid"
          (S Target -1)))))))

;;@ TdThought
;; Un pensamiento por cuadro. Obs = la mirada suavizada (ObsSpeed). Mirado: no envejece (DieAt corre con el reloj). Soltado
;; despues de mirarlo: le quedan ReleaseLife s (soltar = dejarlo ir). En la eleccion, la mirada lo carga en HoldTime s y al
;; 100 % es el elegido (TdChoose). Su palabra emerge con la mirada (Reveal = smoothstep de Obs, el barrido liquido va y
;; vuelve) y se va con el (Out). Vivo: crece, enciende el borde y gira con la mirada (ObsGrow, ObsGlow, ObsSpin) y con la
;; carga (ChooseGrow, ChooseGlow + latido); el tamano en LifeSteps escalones. Se desvanece a su hora (TdFade) y se vuelve a
;; formar en otro lugar a la suya (TdForm).
(fn TdThought (I Dt)
  (bind p (Utilities|Array|Get(acopy) (G Thoughts) I))
  (bind st (Utilities|Array|Get(acopy) (G TState) I))
  (bind on (and (== I (G Target)) (== st 1)))
  (bind ht (Math|Float|Max(Float) (G HoldTime) 0.1))
  (bind c (Utilities|Array|Get(acopy) (G Charge) I))
  (Utilities|Array|SetArrayElem (G Obs) I (Math|Interpolation|FInterpTo :Current (Utilities|Array|Get(acopy) (G Obs) I) :Target (select on 1.0 0.0) :DeltaTime Dt :InterpSpeed (G ObsSpeed)) true)
  (Utilities|Array|SetArrayElem (G ObsTotal) I (+ (Utilities|Array|Get(acopy) (G ObsTotal) I) (select on Dt 0.0)) true)
  (Utilities|Array|SetArrayElem (G Charge) I (select (== st 3) 1.0 (Math|Float|Clamp(Float) (select (and on (G ChoiceOn)) (+ c (/ Dt ht)) (- c (/ (* Dt (G FadeBack)) ht))))) true)
  (Utilities|Array|SetArrayElem (G Excite) I (Math|Interpolation|FInterpTo :Current (Utilities|Array|Get(acopy) (G Excite) I) :Target (select (and on (G ChoiceOn)) (Utilities|Array|Get(acopy) (G Charge) I) 0.0) :DeltaTime Dt :InterpSpeed (G ExciteSpeed)) true)
  (Utilities|Array|SetArrayElem (G DieAt) I (select on (+ (Utilities|Array|Get(acopy) (G DieAt) I) Dt) (select (> (Utilities|Array|Get(acopy) (G Obs) I) 0.5) (Math|Float|Min(Float) (Utilities|Array|Get(acopy) (G DieAt) I) (+ (G Clock) (G ReleaseLife))) (Utilities|Array|Get(acopy) (G DieAt) I))) true)
  (bind ob (Utilities|Array|Get(acopy) (G Obs) I))
  (bind rv (* (* ob ob) (- 3.0 (* 2.0 ob))))
  (bind tc (Utilities|Array|Get(acopy) (G TitleComps) I))
  (bind to (select (== st 3) (Math|Float|Clamp(Float) (/ (- (G Clock) (Utilities|Array|Get(acopy) (G ConsumeAt) I)) (Math|Float|Max(Float) (G TitleOutTime) 0.1))) 0.0))
  (Rendering|SetVisibility tc (and (> rv 0.005) (< to 1.0)) false)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Reveal" rv)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Out" to)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "LT" (G Clock))
  (CallFunction|TdMote :I I :Dt Dt)
  (if (== st 1)
    (if (and (G ChoiceOn) (>= (Utilities|Array|Get(acopy) (G Charge) I) 1.0))
      (CallFunction|TdChoose :I I)
      (elif (>= (G Clock) (Utilities|Array|Get(acopy) (G DieAt) I))
        (CallFunction|TdFade :I I)
        (else
          (bind ch (Utilities|Array|Get(acopy) (G Charge) I))
          (bind ns (Math|Float|Max(Float) (G LifeSteps) 1.0))
          (bind qo (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* rv ns))) ns))
          (bind qc (/ (Math|Conversions|ToFloat(Integer) (Math|Float|Round (* ch ns))) ns))
          (bind cp (* (G ChargePulse) (* (Utilities|Array|Get(acopy) (G Excite) I) (- 0.5 (* 0.5 (Math|Trig|Cos(Radians) (* 6.2831853 (* (G ChargePulseHz) (G Clock)))))))))
          (Class|BPProtoSoulSC|SetSize :self p :Size (* (Utilities|Array|Get(acopy) (G BaseSize) I) (+ 1.0 (+ (* (G ObsGrow) qo) (* (G ChooseGrow) qc)))))
          (Class|BPProtoSoulSC|SetEdgeIntensity :self p :EdgeIntensity (* (Utilities|Array|Get(acopy) (G BaseEdge) I) (+ 1.0 (+ (* (G ObsGlow) rv) (* (G ChooseGlow) (+ ch cp))))))
          (Class|BPProtoSoulSC|SetSpinSpeed :self p :SpinSpeed (+ (Utilities|Array|Get(acopy) (G BaseSpin) I) (* (G ObsSpin) rv))))))
    (elif (and (== st 0) (and (G FormOn) (and (>= (Utilities|Array|Get(acopy) (G NextAt) I) 0.0) (>= (G Clock) (Utilities|Array|Get(acopy) (G NextAt) I)))))
      (CallFunction|TdForm :I I))))

;;@ TdForm
;; El pensamiento I se forma en un lugar libre al azar (Slots): lleva ahi a la protoameba, su titulo (debajo, mirando a
;; EyePos) y su nube; le devuelve su tamano y borde propios y llama su Appear. Vive entre LifeMin y LifeMax s. Si no hay
;; lugar libre, prueba en 1 s.
(fn TdForm (I)
  (bind n (Utilities|Array|Length (G SlotLoc)))
  (S PickStart (Math|Random|RandomIntegerinRange :Min 0 :Max (Math|Integer|Max(Integer) (- n 1) 0)))
  (S PickSlot -1)
  (for k (range n)
    (bind s (Math|Integer|%(Integer) (+ (G PickStart) k) (Math|Integer|Max(Integer) n 1)))
    (if (and (== (G PickSlot) -1) (not (Utilities|Array|Get(acopy) (G SlotBusy) s)))
      (S PickSlot s)))
  (if (>= (G PickSlot) 0)
    (bind p (Utilities|Array|Get(acopy) (G Thoughts) I))
    (bind loc (Utilities|Array|Get(acopy) (G SlotLoc) (G PickSlot)))
    (bind tl (- loc (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (G TitleDrop))))
    (Utilities|Array|SetArrayElem (G SlotBusy) (G PickSlot) true true)
    (Utilities|Array|SetArrayElem (G SlotOf) I (G PickSlot) true)
    (Transformation|SetActorLocation :self p :NewLocation loc)
    (Transformation|SetWorldLocationAndRotation (Utilities|Array|Get(acopy) (G TitleComps) I) tl (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator :Roll 90.0 :Pitch 0.0 :Yaw 90.0) (Math|Rotator|MakeRotfromX (- tl (G EyePos)))))
    (Transformation|SetWorldLocation (Utilities|Array|Get(acopy) (G Motes) I) loc)
    (Class|BPProtoSoulSC|SetSize :self p :Size (Utilities|Array|Get(acopy) (G BaseSize) I))
    (Class|BPProtoSoulSC|SetEdgeIntensity :self p :EdgeIntensity (Utilities|Array|Get(acopy) (G BaseEdge) I))
    (Class|BPProtoSoulSC|SetSpinSpeed :self p :SpinSpeed (Utilities|Array|Get(acopy) (G BaseSpin) I))
    (Class|BPProtoSoulSC|Appear :self p)
    (Utilities|Array|SetArrayElem (G TState) I 1 true)
    (Utilities|Array|SetArrayElem (G Obs) I 0.0 true)
    (Utilities|Array|SetArrayElem (G DieAt) I (+ (G Clock) (Math|Random|RandomFloatinRange :Min (G LifeMin) :Max (G LifeMax))) true)
    (else
      (Utilities|Array|SetArrayElem (G NextAt) I (+ (G Clock) 1.0) true))))

;;@ TdFade
;; El pensamiento I se desvanece (su Disappear): libera su lugar y vuelve a formarse entre GapMin y GapMax s despues.
(fn TdFade (I)
  (Class|BPProtoSoulSC|Disappear :self (Utilities|Array|Get(acopy) (G Thoughts) I))
  (Utilities|Array|SetArrayElem (G TState) I 0 true)
  (Utilities|Array|SetArrayElem (G SlotBusy) (Math|Integer|Max(Integer) (Utilities|Array|Get(acopy) (G SlotOf) I) 0) false true)
  (Utilities|Array|SetArrayElem (G NextAt) I (+ (G Clock) (Math|Random|RandomFloatinRange :Min (G GapMin) :Max (G GapMax))) true)
  (Utilities|Array|SetArrayElem (G Charge) I 0.0 true))

;;@ TdChoose
;; I es el pensamiento elegido: se cierra la eleccion y no se forman mas; su palabra va a quedar bajo la ameba (ChosenComp,
;; ChosenDrop cm, ChosenScale); suena VO_23b ("Let's gather all these thoughts..."); el y todos los vivos se vuelven polvo y
;; viajan a la ameba (TdConsume). Vibran los dos mandos.
(fn TdChoose (I)
  (S Chosen I)
  (S ChosenAt (G Clock))
  (S ChoiceOn false)
  (S FormOn false)
  (S Phase 4)
  (bind cc (G ChosenComp))
  (bind tl (- (G MainHome) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (G ChosenDrop))))
  (Rendering|Material|SetMaterial cc 0 (Utilities|Array|Get(acopy) (G TitleMats) I))
  (Transformation|SetWorldLocationAndRotation cc tl (Math|Rotator|CombineRotators (Math|Rotator|MakeRotator :Roll 90.0 :Pitch 0.0 :Yaw 90.0) (Math|Rotator|MakeRotfromX (- tl (G EyePos)))))
  (Transformation|SetWorldScale3D cc (Math|Vector|MakeVector :X (* 4.0 (G ChosenScale)) :Y (G ChosenScale) :Z 1.0))
  (Rendering|Material|SetScalarParameterValueonMaterials cc "Reveal" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials cc "Out" 0.0)
  (CallFunction|TdSound :Snd (Utilities|Array|Get(acopy) (G VoLines) 3) :Vol (G VoVol))
  (for j (range (Utilities|Array|Length (G Thoughts)))
    (if (== (Utilities|Array|Get(acopy) (G TState) j) 1)
      (CallFunction|TdConsume :I j)))
  (bind pc (Game|GetPlayerController 0))
  (Utilities|IsValid pc
    (:"Is Valid"
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left")
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right"))))

;;@ TdAutoChoose
;; Nadie eligio a tiempo: queda el pensamiento vivo que mas se miro (ObsTotal). Si no hay ninguno vivo, se cierra igual.
(fn TdAutoChoose ()
  (S GBest -1)
  (S GBestDot -1.0)
  (for j (range (Utilities|Array|Length (G Thoughts)))
    (if (and (== (Utilities|Array|Get(acopy) (G TState) j) 1) (> (Utilities|Array|Get(acopy) (G ObsTotal) j) (G GBestDot)))
      (S GBestDot (Utilities|Array|Get(acopy) (G ObsTotal) j))
      (S GBest j)))
  (if (>= (G GBest) 0)
    (CallFunction|TdChoose :I (G GBest))
    (else
      (S ChoiceOn false)
      (S FormOn false)
      (S Phase 4)
      (S ChosenIn true)
      (S ChosenInAt (G Clock)))))

;;@ TdConsume
;; El pensamiento I se vuelve polvo: se disuelve (Disappear) y su nube pasa a VUELO: el emisor viaja a la ameba (TdFly) a
;; FlySpeed cm/s, en arco, dejando una estela de su color (FlyRate, vida FlyTime s) que la ameba atrae (Push). Llega en FeedAt.
(fn TdConsume (I)
  (bind p (Utilities|Array|Get(acopy) (G Thoughts) I))
  (Utilities|Array|SetArrayElem (G TState) I 3 true)
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
  (Components|Activation|Activate m false))

;;@ TdMote
;; Las particulas del pensamiento I. Hecho polvo: el vuelo (TdFly). Si no: su nube (la de Test_Focus): mientras se lo mira
;; nacen en una cascara de MoteRadius cm y MotePull las atrae a su centro; al soltarlo se sueltan (MoteRelease) y se apagan
;; en MoteFade s. Solo trabaja el pensamiento con la nube prendida o apagandose.
(fn TdMote (I Dt)
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (bind st (Utilities|Array|Get(acopy) (G TState) I))
  (bind want (and (== I (G Target)) (== st 1)))
  (Utilities|IsValid m
    (:"Is Valid"
      (if (== st 3)
        (CallFunction|TdFly :I I)
        (elif (or want (or (> (Utilities|Array|Get(acopy) (G MoteF) I) 0.0) (Utilities|Array|Get(acopy) (G MoteOn) I)))
          (CallFunction|TdMoteEdge :I I :Want want)
          (Utilities|Array|SetArrayElem (G MoteF) I (Math|Float|Clamp(Float) (+ (Utilities|Array|Get(acopy) (G MoteF) I) (/ (* Dt (select want 1.0 -1.0)) (Math|Float|Max(Float) (G MoteFade) 0.05)))) true)
          (bind f (Utilities|Array|Get(acopy) (G MoteF) I))
          (Niagara|SetNiagaraVariable(Float) m "SpawnRate" (select want (* (G MoteRate) (+ 0.4 (* 0.6 (Utilities|Array|Get(acopy) (G Obs) I)))) 0.0))
          (Niagara|SetNiagaraVariable(Float) m "Fade" (* (* f f) (- 3.0 (* 2.0 f))))
          (if (and (not want) (<= f 0.0))
            (Components|Activation|Deactivate m)))))))

;;@ TdMoteEdge
;; El cambio de estado de la nube: al prenderse copia las perillas (color del pensamiento, vida, tamanos, radio, ruido,
;; Target = el pensamiento) y la activa; al apagarse las suelta hacia afuera.
(fn TdMoteEdge (I Want)
  (bind was (Utilities|Array|Get(acopy) (G MoteOn) I))
  (if (or (and Want (not was)) (and (not Want) was))
    (Utilities|Array|SetArrayElem (G MoteOn) I Want true)
    (bind m (Utilities|Array|Get(acopy) (G Motes) I))
    (Niagara|SetNiagaraVariable(Float) m "Push" (select Want (G MotePull) (* -1.0 (G MoteRelease))))
    (if Want
      (Niagara|SetNiagaraVariable(Position) m "Target" (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Thoughts) I)))
      (Niagara|SetNiagaraVariable(LinearColor) m "OrbColor" (Math|Color|NewOpacity(LinearColor) (Utilities|Array|Get(acopy) (G CCol) I) (G MoteAlpha)))
      (Niagara|SetNiagaraVariable(Float) m "Life" (Math|Float|Max(Float) (G MoteLife) 0.2))
      (Niagara|SetNiagaraVariable(Float) m "SizeMin" (G MoteSize))
      (Niagara|SetNiagaraVariable(Float) m "SizeMax" (* 2.0 (G MoteSize)))
      (Niagara|SetNiagaraVariable(Float) m "Radius" (G MoteRadius))
      (Niagara|SetNiagaraVariable(Float) m "Noise" (G MoteNoise))
      (if (or (not (Components|Activation|IsActive m)) (<= (Utilities|Array|Get(acopy) (G MoteF) I) 0.0))
        (Components|Activation|Activate m true)))))

;;@ TdFly
;; El vuelo del pensamiento I (FlyState): 1 el emisor viaja a la ameba (smoothstep, arco de FlyArc cm) -> llega en FeedAt:
;; deja de nacer y la ameba destella; si es el elegido, la ameba se llena (bChosenIn) y suena FeedSound -> 3 mueren las
;; ultimas (FlyTime s) -> 4 se apaga la nube.
(fn TdFly (I)
  (bind st (Utilities|Array|Get(acopy) (G FlyState) I))
  (bind ca (Utilities|Array|Get(acopy) (G ConsumeAt) I))
  (bind fa (Utilities|Array|Get(acopy) (G FeedAt) I))
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (if (== st 1)
    (bind t (Math|Float|Clamp(Float) (/ (- (G Clock) ca) (Math|Float|Max(Float) (- fa ca) 0.1))))
    (Transformation|SetWorldLocation m (+ (Math|Vector|Lerp(Vector) (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Thoughts) I)) (G MainHome) (* (* t t) (- 3.0 (* 2.0 t)))) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (* (G FlyArc) (Math|Trig|Sin(Radians) (* 3.1415927 t))))))
    (if (>= t 1.0)
      (Niagara|SetNiagaraVariable(Float) m "SpawnRate" 0.0)
      (Utilities|Array|SetArrayElem (G FlyState) I 3 true)
      (S LastFeedAt (G Clock))
      (if (== I (G Chosen))
        (S ChosenIn true)
        (S ChosenInAt (G Clock))
        (CallFunction|TdSound :Snd (G FeedSound) :Vol (G SfxVol))))
    (elif (and (== st 3) (>= (G Clock) (+ fa (+ (G FlyTime) 0.4))))
      (Utilities|Array|SetArrayElem (G FlyState) I 4 true)
      (Components|Activation|Deactivate m))))

;;@ TdDust
;; El polvo de la mirada (desde DustAt hasta la eleccion): sigue el punto donde se mira, a DustDist cm, o al pensamiento
;; mirado. Sin camara (Simulate), un vaiven lento delante de EyePos.
(fn TdDust (Dt)
  (bind cm (Game|GetPlayerCameraManager 0))
  (bind tp (Transformation|GetActorLocation :self (Utilities|Array|Get(acopy) (G Thoughts) (Math|Integer|Max(Integer) (G Target) 0))))
  (Utilities|IsValid cm
    (:"Is Valid"
      (CallFunction|TdDustAt :Dt Dt :P (select (>= (G Target) 0) tp (+ (Camera|GetCameraLocation cm) (* (Math|Vector|GetForwardVector (Camera|GetCameraRotation cm)) (G DustDist))))))
    (:"Is Not Valid"
      (CallFunction|TdDustAt :Dt Dt :P (select (>= (G Target) 0) tp (+ (G EyePos) (* (Math|Vector|GetForwardVector (Math|Rotator|MakeRotator :Roll 0.0 :Pitch (* 8.0 (Math|Trig|Sin(Radians) (* 0.21 (G Clock)))) :Yaw (* 30.0 (Math|Trig|Sin(Radians) (* 0.13 (G Clock)))))) (G DustDist))))))))

;;@ TdDustAt
;; Lleva el polvo hacia P (DustSpeed) y lo hace nacer (DustRate) en las fases 1 a 3, desde DustAt.
(fn TdDustAt (Dt P)
  (bind d (G DustComp))
  (S DustPos (Math|Interpolation|VInterpTo :Current (G DustPos) :Target P :DeltaTime Dt :InterpSpeed (G DustSpeed)))
  (Transformation|SetWorldLocation d (G DustPos))
  (Niagara|SetNiagaraVariable(Position) d "Target" (G DustPos))
  (Niagara|SetNiagaraVariable(Float) d "SpawnRate" (select (and (and (>= (G Phase) 1) (< (G Phase) 4)) (>= (G Clock) (G DustAt))) (G DustRate) 0.0)))

;;@ TdMain
;; La ameba: CellE va hacia lo que hay que mostrar (FeedSpeed): la atencion (AttnMax por AttnSum / AttnFull s de mirar
;; pensamientos) y, cuando llega el elegido, 1. Aparece con ease-out-back en RevealTime s, crece de SleepScale a 1, pasa de
;; SleepState a AwakeState y su Agitation de SleepAgit a AwakeAgit. Cada polvo que llega es un destello (bl, BloomTime s):
;; luz BloomLight, escala BloomScale, agitacion FeedAgit, vida FeedLife / FeedCurl. Su vida y sus brazos van a AwakeLife y
;; AwakeCurl; lo que va al shader en LifeSteps escalones. Deriva con WF, WP. Llegado el elegido, toma ChosenTint de su color
;; (TintNow, en 2 s). El color se empuja solo si cambio.
(fn TdMain (Dt)
  (bind c (G Main))
  (Utilities|IsValid c
    (:"Is Valid"
      (S CellE (Math|Interpolation|FInterpTo :Current (G CellE) :Target (select (G ChosenIn) 1.0 (* (G AttnMax) (Math|Float|Clamp(Float) (/ (G AttnSum) (Math|Float|Max(Float) (G AttnFull) 1.0))))) :DeltaTime Dt :InterpSpeed (G FeedSpeed)))
      (bind ch (Math|Float|Clamp(Float) (G CellE)))
      (bind e (* (* ch ch) (- 3.0 (* 2.0 ch))))
      (S TintNow (select (and (G ChosenIn) (>= (G Chosen) 0)) (* (G ChosenTint) (Math|Float|Clamp(Float) (/ (- (G Clock) (G ChosenInAt)) 2.0))) 0.0))
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
      (if (> (Math|Float|Absolute(Float) (- (+ L (* 3.0 (G TintNow))) (G LightP))) 0.004)
        (S LightP (+ L (* 3.0 (G TintNow))))
        (CallFunction|TdLook :L L)))))

;;@ TdChosenTitle
;; La palabra del elegido, bajo la ameba: emerge 0,6 s despues de que llega (barrido liquido en TitleTime s) y se queda.
(fn TdChosenTitle ()
  (bind cc (G ChosenComp))
  (Rendering|SetVisibility cc (and (G ChosenIn) (>= (G Chosen) 0)) false)
  (if (and (G ChosenIn) (>= (G Chosen) 0))
    (Rendering|Material|SetScalarParameterValueonMaterials cc "Reveal" (Math|Float|Clamp(Float) (/ (- (- (G Clock) (G ChosenInAt)) 0.6) (Math|Float|Max(Float) (G TitleTime) 0.1))))
    (Rendering|Material|SetScalarParameterValueonMaterials cc "LT" (G Clock))))

;;@ TdLook
;; Pinta la ameba con luz L (0 dormida, 1 despierta, > 1 destello) sobre sus colores originales (y TintNow del elegido),
;; con su propio PushLook; la envoltura y el polvo van directo al material.
(fn TdLook (L)
  (bind c (G Main))
  (Class|BPLovingCellSC|SetAmoebaColor1 :self c :AmoebaColor1 (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 0) :L L))
  (Class|BPLovingCellSC|SetAmoebaColor2 :self c :AmoebaColor2 (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 1) :L L))
  (Class|BPLovingCellSC|SetMembraneColor :self c :MembraneColor (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 2) :L L))
  (Class|BPLovingCellSC|SetMembraneRim :self c :MembraneRim (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 3) :L L))
  (Class|BPLovingCellSC|SetOuterColor :self c :OuterColor (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 4) :L L))
  (Class|BPLovingCellSC|SetDustColor :self c :DustColor (CallFunction|TdMix :C (Utilities|Array|Get(acopy) (G OrigCol) 5) :L L))
  (Class|BPLovingCellSC|PushLook :self c)
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetOuterShell c) "OuterCol" (Math|Color|NewOpacity(LinearColor) (Class|BPLovingCellSC|GetOuterColor c) (Class|BPLovingCellSC|GetOuterOpacity c)))
  (Rendering|Material|SetColorParameterValueonMaterials (Class|BPLovingCellSC|GetDust c) "DustCol" (Class|BPLovingCellSC|GetDustColor c)))

;;@ TdMix
;; Color dormido = lerp(original, SleepTint, SleepMix) * SleepDim; con luz L vuelve al original (L > 1 lo pasa); despues
;; TintNow hacia el color del elegido. Conserva el alfa.
(fn TdMix (C L)
  (bind (r g b a) (Utilities|Struct|BreakLinearColor C))
  (return (Math|Color|NewOpacity(LinearColor) (Math|Color|Lerp(LinearColor) (Math|Color|Lerp(LinearColor) (* (Math|Color|Lerp(LinearColor) C (G SleepTint) (G SleepMix)) (G SleepDim)) C L) (Utilities|Array|Get(acopy) (G CCol) (Math|Integer|Max(Integer) (G Chosen) 0)) (G TintNow)) a)))

;;@ TdSound
(fn TdSound (Snd Vol)
  (Utilities|IsValid Snd
    (:"Is Valid"
      (Audio|PlaySound2D :Sound Snd :VolumeMultiplier Vol))))
