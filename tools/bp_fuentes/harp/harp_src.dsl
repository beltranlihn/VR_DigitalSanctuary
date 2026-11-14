;; BP_Harp_SC — fuente del DSL. (G X) = getter, (S X v) = setter; gen_harp_dsl.py los expande con la categoria de cada variable.
;; Cada bloque empieza con ";;@ <Grafo>".

;;@ Fail
(fn Fail (What)
  (S BuildFails (+ (G BuildFails) 1))
  (Development|PrintString :InString (Utilities|String|Append :A "HARP build fail: " :B (Utilities|String|ToString(Name) What))))

;;@ MSNode
(fn MSNode (NS N Var)
  (bind h (Audio|MetaSound|Builder|AddMetaSoundNodeByClassName :self (G Builder) :ClassName (Utilities|Struct|MakeMetaSoundClassName :Namespace NS :Name N :Variant Var) :MajorVersion 1)
    (:Succeeded (return h))
    (:Failed (CallFunction|Fail :What N) (return h))))

;;@ MSOut
(fn MSOut (Node OutName)
  (bind o (Audio|MetaSound|Builder|FindNodeOutputbyName :self (G Builder) :NodeHandle Node :OutputName OutName)
    (:Succeeded (return o))
    (:Failed (CallFunction|Fail :What OutName) (return o))))

;;@ MSConnectH
(fn MSConnectH (OutH InH)
  (Audio|MetaSound|Builder|ConnectNodes :self (G Builder) :NodeOutputHandle OutH :NodeInputHandle InH
    (:Succeeded)
    (:Failed (CallFunction|Fail :What (Utilities|Name|MakeLiteralName "connect")))))

;;@ MSConnect
(fn MSConnect (OutH To InName)
  (bind ih (Audio|MetaSound|Builder|FindNodeInputbyName :self (G Builder) :NodeHandle To :InputName InName)
    (:Succeeded (CallFunction|MSConnectH :OutH OutH :InH ih))
    (:Failed (CallFunction|Fail :What InName))))

;;@ MSSet
(fn MSSet (To InName Val)
  (bind (dtp lit) (Audio|MetaSound|Builder|CreateMetaSoundFloatLiteral :self (EngineSubsystems|GetMetaSoundBuilderSubsystem) :Value Val))
  (bind ih (Audio|MetaSound|Builder|FindNodeInputbyName :self (G Builder) :NodeHandle To :InputName InName)
    (:Succeeded
      (Audio|MetaSound|Builder|SetNodeInputDefault :self (G Builder) :NodeInputHandle ih :Literal lit
        (:Succeeded)
        (:Failed (CallFunction|Fail :What InName))))
    (:Failed (CallFunction|Fail :What InName))))

;;@ MSInput
(fn MSInput (Nm Trig Def)
  (bind (dtp lit) (Audio|MetaSound|Builder|CreateMetaSoundFloatLiteral :self (EngineSubsystems|GetMetaSoundBuilderSubsystem) :Value Def))
  (bind h (Audio|MetaSound|Builder|AddGraphInputNode :self (G Builder) :Name Nm :DataType (select Trig (Utilities|Name|MakeLiteralName "Trigger") (Utilities|Name|MakeLiteralName "Float")) :DefaultValue (select Trig (Utilities|Struct|MakeMetaSoundLiteral) lit) :bIsConstructorInput false)
    (:Succeeded (return h))
    (:Failed (CallFunction|Fail :What Nm) (return h))))

;;@ LinkTo
(fn LinkTo (O J)
  (bind to (Utilities|Array|Get(acopy) (G LTo) J))
  (if (>= to 0)
    (CallFunction|MSConnect :OutH O :To (Utilities|Array|Get(acopy) (G Handles) to) :InName (Utilities|Array|Get(acopy) (G LIn) J))
    (else (if (== to -10) (S VoiceL O) (else (S VoiceR O))))))

;;@ VoiceLink
(fn VoiceLink (J HP HV HC)
  (bind from (Utilities|Array|Get(acopy) (G LFrom) J))
  (if (>= from 0)
    (bind o (CallFunction|MSOut :Node (Utilities|Array|Get(acopy) (G Handles) from) :OutName (Utilities|Array|Get(acopy) (G LOut) J)))
    (CallFunction|LinkTo :O o :J J)
    (else (CallFunction|LinkTo :O (select (== from -1) HP (select (== from -2) HV HC)) :J J))))

;;@ VoiceDef
(fn VoiceDef (D Period Fb Pan)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (CallFunction|MSSet :To (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)) :InName (Utilities|Array|Get(acopy) (G DIn) D) :Val (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) Period v)))))

;;@ BuildVoice
(fn BuildVoice (I Period Fb Pan)
  (bind hp (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G PluckN) I) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (bind hv (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G VelN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 0.5)))
  (bind hc (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G CutN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 4000.0)))
  (Utilities|Array|Clear (G Handles))
  (for k (range (Utilities|Array|Length (G VName)))
    (bind h (CallFunction|MSNode :NS (Utilities|Array|Get(acopy) (G VNS) k) :N (Utilities|Array|Get(acopy) (G VName) k) :Var (Utilities|Array|Get(acopy) (G VVar) k)))
    (Utilities|Array|Add (G Handles) h))
  (for j (range (Utilities|Array|Length (G LFrom)))
    (CallFunction|VoiceLink :J j :HP hp :HV hv :HC hc))
  (for d (range (Utilities|Array|Length (G DNode)))
    (CallFunction|VoiceDef :D d :Period Period :Fb Fb :Pan Pan)))

;;@ MixVoice
(fn MixVoice (I)
  (if (== I 0)
    (S SumL (G VoiceL))
    (S SumR (G VoiceR))
    (else
      (bind nUE (Utilities|Name|MakeLiteralName "UE"))
      (bind nAdd (Utilities|Name|MakeLiteralName "Add"))
      (bind nAud (Utilities|Name|MakeLiteralName "Audio"))
      (bind nPO (Utilities|Name|MakeLiteralName "PrimaryOperand"))
      (bind nAO (Utilities|Name|MakeLiteralName "AdditionalOperands"))
      (bind nOut (Utilities|Name|MakeLiteralName "Out"))
      (bind al (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
      (CallFunction|MSConnect :OutH (G SumL) :To al :InName nPO)
      (CallFunction|MSConnect :OutH (G VoiceL) :To al :InName nAO)
      (bind ol (CallFunction|MSOut :Node al :OutName nOut))
      (S SumL ol)
      (bind ar (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
      (CallFunction|MSConnect :OutH (G SumR) :To ar :InName nPO)
      (CallFunction|MSConnect :OutH (G VoiceR) :To ar :InName nAO)
      (bind orr (CallFunction|MSOut :Node ar :OutName nOut))
      (S SumR orr))))

;;@ BuildFX
(fn BuildFX ()
  (bind nUE (Utilities|Name|MakeLiteralName "UE"))
  (bind nAud (Utilities|Name|MakeLiteralName "Audio"))
  (bind nMul (Utilities|Name|MakeLiteralName "Multiply"))
  (bind nABF (Utilities|Name|MakeLiteralName "Audio by Float"))
  (bind nPO (Utilities|Name|MakeLiteralName "PrimaryOperand"))
  (bind nAO (Utilities|Name|MakeLiteralName "AdditionalOperands"))
  (bind nOut (Utilities|Name|MakeLiteralName "Out"))
  (bind nIL (Utilities|Name|MakeLiteralName "In Left"))
  (bind nIR (Utilities|Name|MakeLiteralName "In Right"))
  (bind nOL (Utilities|Name|MakeLiteralName "Out Left"))
  (bind nOR (Utilities|Name|MakeLiteralName "Out Right"))
  (bind nWet (Utilities|Name|MakeLiteralName "Wet Level"))
  (bind nDry (Utilities|Name|MakeLiteralName "Dry Level"))
  (bind one (Math|Float|MakeLiteralFloat 1.0))
  (bind gl (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumL) :To gl :InName nPO)
  (CallFunction|MSSet :To gl :InName nAO :Val (G Volume))
  (bind gr (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumR) :To gr :InName nPO)
  (CallFunction|MSSet :To gr :InName nAO :Val (G Volume))
  (bind sd (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Stereo Delay") :Var nAud))
  (bind gol (CallFunction|MSOut :Node gl :OutName nOut))
  (CallFunction|MSConnect :OutH gol :To sd :InName nIL)
  (bind gor (CallFunction|MSOut :Node gr :OutName nOut))
  (CallFunction|MSConnect :OutH gor :To sd :InName nIR)
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Delay Time") :Val (G DelayTime))
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Feedback") :Val (G DelayFeedback))
  (CallFunction|MSSet :To sd :InName nWet :Val (G DelayWet))
  (CallFunction|MSSet :To sd :InName nDry :Val one)
  (bind pr (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Plate Reverb") :Var (Utilities|Name|MakeLiteralName "Stereo")))
  (bind sol (CallFunction|MSOut :Node sd :OutName nOL))
  (CallFunction|MSConnect :OutH sol :To pr :InName nIL)
  (bind sor (CallFunction|MSOut :Node sd :OutName nOR))
  (CallFunction|MSConnect :OutH sor :To pr :InName nIR)
  (CallFunction|MSSet :To pr :InName nWet :Val (G ReverbWet))
  (CallFunction|MSSet :To pr :InName nDry :Val one)
  (CallFunction|MSSet :To pr :InName (Utilities|Name|MakeLiteralName "Decay") :Val (G ReverbDecay))
  (bind nLim (Utilities|Name|MakeLiteralName "Limiter"))
  (bind nAudPin (Utilities|Name|MakeLiteralName "Audio"))
  (bind nGain (Utilities|Name|MakeLiteralName "Input Gain dB"))
  (bind nThr (Utilities|Name|MakeLiteralName "Threshold dB"))
  (bind thr (Math|Float|MakeLiteralFloat -3.0))
  (bind ll (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind pol (CallFunction|MSOut :Node pr :OutName nOL))
  (CallFunction|MSConnect :OutH pol :To ll :InName nAudPin)
  (CallFunction|MSSet :To ll :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To ll :InName nThr :Val thr)
  (bind lol (CallFunction|MSOut :Node ll :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lol :InH (Utilities|Array|Get(acopy) (G AudioOuts) 0))
  (bind lr (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind por (CallFunction|MSOut :Node pr :OutName nOR))
  (CallFunction|MSConnect :OutH por :To lr :InName nAudPin)
  (CallFunction|MSSet :To lr :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To lr :InName nThr :Val thr)
  (bind lor (CallFunction|MSOut :Node lr :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lor :InH (Utilities|Array|Get(acopy) (G AudioOuts) 1)))

;;@ BuildBody
(fn BuildBody ()
  (bind n (G NumStrings))
  (bind steps (G ScaleSteps))
  (bind sl (Utilities|Array|Length steps))
  (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
  (for i (range n)
    (bind oct (/ i sl))
    (bind midi (+ (+ (G RootNote) (Utilities|Array|Get(acopy) steps (- i (* oct sl)))) (* oct 12)))
    (bind freq (* 440.0 (Math|Float|Power 2.0 (/ (- (Math|Conversions|ToFloat(Integer) midi) 69.0) 12.0))))
    (bind per (/ 1.0 freq))
    (bind fb (Math|Float|Exp (/ -6.9078 (* freq (G Decay)))))
    (bind pan (* (G PanWidth) (- (* 2.0 (/ (Math|Conversions|ToFloat(Integer) i) nm1)) 1.0)))
    (CallFunction|BuildVoice :I i :Period per :Fb fb :Pan pan)
    (CallFunction|MixVoice :I i))
  (CallFunction|BuildFX)
  (Audio|MetaSound|Builder|Audition :self (G Builder) :AudioComponent (Variables|Default|GetSynth) :bLiveUpdatesEnabled false)
  (S Ready true)
  (Development|PrintString :InString (Utilities|String|Append :A "HARP synth ready, fails=" :B (Utilities|String|ToString(Integer) (G BuildFails)))))

;;@ BuildSynth
(fn BuildSynth ()
  (S BuildFails 0)
  (S Ready false)
  (Audio|MetaSound|Builder|CreateSourceBuilder :self (EngineSubsystems|GetMetaSoundBuilderSubsystem) :BuilderName "HarpSynth" :OutputFormat "Stereo" :bIsOneShot false
    (:Succeeded (S Builder _returnvalue) (S AudioOuts _audiooutnodeinputs) (CallFunction|BuildBody))
    (:Failed (Development|PrintString :InString "HARP: CreateSourceBuilder failed"))))

;;@ MakeNames
(fn MakeNames ()
  (Utilities|Array|Clear (G PluckN))
  (Utilities|Array|Clear (G VelN))
  (Utilities|Array|Clear (G CutN))
  (for i (range (G NumStrings))
    (bind s (Utilities|String|ToString(Integer) i))
    (Utilities|Array|Add (G PluckN) (Utilities|String|StringToName (Utilities|String|Append :A "Pluck_" :B s)))
    (Utilities|Array|Add (G VelN) (Utilities|String|StringToName (Utilities|String|Append :A "Vel_" :B s)))
    (Utilities|Array|Add (G CutN) (Utilities|String|StringToName (Utilities|String|Append :A "Cut_" :B s)))))

;;@ BuildStrings
(fn BuildStrings ()
  (Utilities|Array|Clear (G Strings))
  (bind n (G NumStrings))
  (bind sp (G Spacing))
  (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
  (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
  (bind r (G StringRadius))
  (for i (range n)
    (bind fi (Math|Conversions|ToFloat(Integer) i))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z 0.0) :Scale (Math|Vector|MakeVector :X r :Y r :Z (/ len 100.0)))))
    (Components|StaticMesh|SetStaticMesh c (G StringMesh))
    (Rendering|Material|SetMaterial c 0 (G StringMat))
    (Collision|SetCollisionEnabled c "NoCollision")
    (Rendering|SetCastShadow c false)
    (Utilities|Array|Add (G Strings) c)))

;;@ EnsureStrings
(fn EnsureStrings ()
  (if (!= (Utilities|Array|Length (G Strings)) (G NumStrings))
    (CallFunction|BuildStrings)))

;;@ InitLook
(fn InitLook ()
  (bind side (Transformation|GetActorRightVector))
  (bind base (Math|Conversions|ToVector(LinearColor) (G BaseColor)))
  (Utilities|Array|Resize (G Energy) (G NumStrings))
  (Utilities|Array|Resize (G LastPluck) (G NumStrings))
  (for c (G Strings)
    (Rendering|Material|SetVectorParameterValueonMaterials c "SideDir" side)
    (Rendering|Material|SetVectorParameterValueonMaterials c "BaseColor" base)
    (Rendering|Material|SetScalarParameterValueonMaterials c "Glow" (G Glow))
    (Rendering|Material|SetScalarParameterValueonMaterials c "Amp" (G VibAmp))
    (Rendering|Material|SetScalarParameterValueonMaterials c "WobbleHz" (G WobbleHz))
    (Rendering|Material|SetScalarParameterValueonMaterials c "Energy" 0.0)))

;;@ FindHands
(fn FindHands ()
  (Utilities|IsValid (G HandR)
    (:"Is Valid")
    (:"Is Not Valid"
      (bind pawn (Game|GetPlayerPawn 0))
      (Utilities|IsValid pawn
        (:"Is Valid"
          (for mc (Actor|GetComponentsByClass pawn "/Script/HeadMountedDisplay.MotionControllerComponent")
            (bind m (Utilities|Casting|CastToMotionControllerComponent :Object mc)
              (:then
                (bind src (Class|MotionControllerComponent|GetMotionSource m))
                (if (== src "RightGrip") (S HandR m)
                  (else (if (== src "LeftGrip") (S HandL m)))))
              (:CastFailed))))
        (:"Is Not Valid")))))

;;@ HarpTick
(fn HarpTick (DT)
  (CallFunction|FindHands)
  (CallFunction|DecayStrings :DT DT)
  (CallFunction|TickR :DT DT)
  (CallFunction|TickL :DT DT))

;;@ TickR
(fn TickR (DT)
  (if (G DebugStrum)
    (bind t (Utilities|Time|GetGameTimeinSeconds))
    (bind span (+ (* (* (Math|Conversions|ToFloat(Integer) (- (G NumStrings) 1)) 0.5) (G Spacing)) 4.0))
    (CallFunction|HandStep :P (Math|Vector|MakeVector :X 0.0 :Y (* (Math|Trig|Sin(Radians) (* t 1.3)) span) :Z (* (G StringLen) 0.4)) :Right (Math|Boolean|MakeLiteralBool true) :DT DT)
    (else
      (Utilities|IsValid (G HandR)
        (:"Is Valid"
          (CallFunction|HandStep :P (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (+ (Transformation|GetWorldLocation (G HandR)) (* (Transformation|GetForwardVector (G HandR)) (G TipFwd)))) :Right (Math|Boolean|MakeLiteralBool true) :DT DT))
        (:"Is Not Valid")))))

;;@ TickL
(fn TickL (DT)
  (Utilities|IsValid (G HandL)
    (:"Is Valid"
      (CallFunction|HandStep :P (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (+ (Transformation|GetWorldLocation (G HandL)) (* (Transformation|GetForwardVector (G HandL)) (G TipFwd)))) :Right (Math|Boolean|MakeLiteralBool false) :DT DT))
    (:"Is Not Valid")))

;;@ HandStep
(fn HandStep (P Right DT)
  (bind prev (select Right (G PrevR) (G PrevL)))
  (bind has (select Right (G HasR) (G HasL)))
  (CallFunction|DetectStrum :P0 prev :P1 P :DT DT :Right Right :Has has)
  (CallFunction|DetectPoke :P0 prev :P1 P :DT DT :Right Right :Has has)
  (if Right
    (S PrevR P)
    (S HasR true)
    (else (S PrevL P) (S HasL true))))

;;@ DetectStrum
(fn DetectStrum (P0 P1 DT Right Has)
  (bind y0 (.y P0))
  (bind y1 (.y P1))
  (if (and (and Has (< (Math|Float|Absolute(Float) (.x P1)) (G PlaneTol))) (and (< (Math|Float|Absolute(Float) (.x P0)) (* (G PlaneTol) 2.0)) (!= y0 y1)))
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind i0 (Math|Integer|Max(Integer) 0 (Math|Float|Ceil (/ (+ (Math|Float|Min(Float) y0 y1) half) sp))))
    (bind i1 (Math|Integer|Min(Integer) (- n 1) (Math|Float|Floor (/ (+ (Math|Float|Max(Float) y0 y1) half) sp))))
    (bind speed (/ (Math|Float|Absolute(Float) (- y1 y0)) DT))
    (for k (range (+ (- i1 i0) 1))
      (bind i (+ i0 k))
      (bind fi (Math|Conversions|ToFloat(Integer) i))
      (bind t (/ (- (- (* fi sp) half) y0) (- y1 y0)))
      (bind z (Math|Float|Lerp (.z P0) (.z P1) t))
      (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
      (if (and (> z 0.0) (< z len))
        (CallFunction|Pluck :I i :Speed speed :Right Right)))))

;;@ DetectPoke
(fn DetectPoke (P0 P1 DT Right Has)
  (bind x0 (.x P0))
  (bind x1 (.x P1))
  (if (and Has (!= (> x0 0.0) (> x1 0.0)))
    (bind t (/ x0 (- x0 x1)))
    (bind y (Math|Float|Lerp (.y P0) (.y P1) t))
    (bind z (Math|Float|Lerp (.z P0) (.z P1) t))
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind i (Math|Float|Round (/ (+ y half) sp)))
    (bind fi (Math|Conversions|ToFloat(Integer) i))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (if (and (and (>= i 0) (< i n)) (and (< (Math|Float|Absolute(Float) (- y (- (* fi sp) half))) (G HitHalfWidth)) (and (> z 0.0) (< z len))))
      (CallFunction|Pluck :I i :Speed (/ (Math|Float|Absolute(Float) (- x1 x0)) DT) :Right Right))))

;;@ Pluck
(fn Pluck (I Speed Right)
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (if (>= (- now (Utilities|Array|Get(acopy) (G LastPluck) I)) (G Cooldown))
    (Utilities|Array|SetArrayElem (G LastPluck) I now)
    (bind vel (Math|Float|Clamp(Float) (/ Speed (G VelFull)) 0.12 1.0))
    (Audio|Parameter|SetFloatParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G VelN) I) :InFloat (+ 0.2 (* 0.8 vel)))
    (Audio|Parameter|SetFloatParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G CutN) I) :InFloat (+ 900.0 (* 9000.0 (* vel vel))))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G PluckN) I))
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) vel))
    (Utilities|Array|SetArrayElem (G Energy) I e)
    (bind c (Utilities|Array|Get(acopy) (G Strings) I))
    (Rendering|Material|SetScalarParameterValueonMaterials c "Energy" e)
    (Rendering|Material|SetVectorParameterValueonMaterials c "HandColor" (Math|Conversions|ToVector(LinearColor) (select Right (G RightColor) (G LeftColor))))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP pluck " :B (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)
    (bind pc (Game|GetPlayerController 0))
    (bind hs (* (G HapticScale) (+ 0.35 (* 0.65 vel))))
    (if Right
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right" :Scale hs :bLoop false)
      (else (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left" :Scale hs :bLoop false)))))

;;@ DecayStrings
(fn DecayStrings (DT)
  (bind f (Math|Float|Exp (/ (neg DT) (G VibDecay))))
  (bind en (G Energy))
  (for i (range (Utilities|Array|Length en))
    (bind e (Utilities|Array|Get(acopy) en i))
    (if (> e 0.0)
      (bind e2 (select (< (* e f) 0.004) 0.0 (* e f)))
      (Utilities|Array|SetArrayElem en i e2)
      (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) i) "Energy" e2))))

;;@ UserConstructionScript
(fn ConstructionScript ()
  (CallFunction|BuildStrings))

;;@ EventGraph
(event EventBeginPlay
  (CallFunction|EnsureStrings)
  (CallFunction|InitLook)
  (CallFunction|MakeNames)
  (CallFunction|BuildSynth))

(event EventTick (DeltaSeconds)
  (CallFunction|HarpTick :DT DeltaSeconds))

;; ---- 2026-10-27 (2a vuelta): mandos de la Obra en vez de las manos; la cabeza del mando toca la cuerda ----

;;@ MountQCtrl
(fn MountQCtrl (Left)
  (bind grip (select Left (G HandL) (G HandR)))
  (Utilities|IsValid grip
    (:"Is Valid"
      (bind a (Game|SpawnActorfromClass "/SC_Base/Blueprints/BP_QuestCtrl_SC.BP_QuestCtrl_SC_C" (Transformation|GetWorldTransform grip) "AlwaysSpawn"))
      (Class|BPQuestCtrlSC|SetLeft :self a :bLeft Left)
      (Class|BPQuestCtrlSC|ApplyHand :self a)
      (Transformation|AttachActorToComponent a grip "None" "KeepRelative" "KeepRelative" "KeepRelative" false)
      (bind s (G QCtrlScale))
      (Transformation|SetActorRelativeTransform a (Math|Transform|MakeTransform :Location (select Left (G QCtrlLocL) (G QCtrlLocR)) :Rotation (select Left (G QCtrlRotL) (G QCtrlRotR)) :Scale (Math|Vector|MakeVector :X s :Y s :Z s)))
      (if Left (S QCtrlL a) (else (S QCtrlR a))))))

;;@ CtrlEnsure
(fn CtrlEnsure (Left)
  (Utilities|IsValid (select Left (G QCtrlL) (G QCtrlR))
    (:"Is Valid")
    (:"Is Not Valid" (CallFunction|MountQCtrl :Left Left))))

;;@ ConcealHands
(fn ConcealHands ()
  (S HandsHidden true)
  (if (G HideHands)
    (for c (Components|GetChildrenComponents (G HandR) true)
      (bind sk (Utilities|Casting|CastToSkeletalMeshComponent :Object c)
        (:then (Rendering|SetVisibility sk false true) (Development|SetHiddenInGame sk true true))
        (:CastFailed)))
    (for c2 (Components|GetChildrenComponents (G HandL) true)
      (bind sk2 (Utilities|Casting|CastToSkeletalMeshComponent :Object c2)
        (:then (Rendering|SetVisibility sk2 false true) (Development|SetHiddenInGame sk2 true true))
        (:CastFailed)))))

;;@ CtrlTick
(fn CtrlTick ()
  (Utilities|IsValid (G HandR)
    (:"Is Valid"
      (CallFunction|CtrlEnsure :Left (Math|Boolean|MakeLiteralBool false))
      (CallFunction|CtrlEnsure :Left (Math|Boolean|MakeLiteralBool true))
      (if (not (G HandsHidden)) (CallFunction|ConcealHands)))
    (:"Is Not Valid")))

;;@ HandTickR
(fn HandTickR (DT)
  (if (G DebugStrum)
    (CallFunction|TickR :DT DT)
    (else
      (Utilities|IsValid (G QCtrlR)
        (:"Is Valid"
          (CallFunction|HandStep :P (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Math|Transform|TransformLocation (Transformation|GetActorTransform (G QCtrlR)) (G HeadLocal))) :Right (Math|Boolean|MakeLiteralBool true) :DT DT))
        (:"Is Not Valid" (CallFunction|TickR :DT DT))))))

;;@ HandTickL
(fn HandTickL (DT)
  (bind hl (G HeadLocal))
  (Utilities|IsValid (G QCtrlL)
    (:"Is Valid"
      (CallFunction|HandStep :P (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Math|Transform|TransformLocation (Transformation|GetActorTransform (G QCtrlL)) (Math|Vector|MakeVector :X (neg (.x hl)) :Y (.y hl) :Z (.z hl)))) :Right (Math|Boolean|MakeLiteralBool false) :DT DT))
    (:"Is Not Valid" (CallFunction|TickL :DT DT))))

;;@ HarpTick2
(fn HarpTick2 (DT)
  (CallFunction|FindHands)
  (CallFunction|CtrlTick)
  (CallFunction|DecayStrings :DT DT)
  (CallFunction|HandTickR :DT DT)
  (CallFunction|HandTickL :DT DT))

;; ---- 2026-10-28: varios sonidos por indice (SoundIndex). Cada fila de la receta lleva su sonido (VSnd/LSnd/DSnd) ----

;;@ VoiceDef2
(fn VoiceDef2 (D Period Fb Pan)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (CallFunction|MSSet :To (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)) :InName (Utilities|Array|Get(acopy) (G DIn) D) :Val (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v))))))))

;;@ BuildVoice2
(fn BuildVoice2 (I Period Fb Pan)
  (bind snd (G SoundIndex))
  (bind hp (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G PluckN) I) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (bind hv (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G VelN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 0.5)))
  (bind hc (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G CutN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 4000.0)))
  (Utilities|Array|Clear (G Handles))
  (for k (range (Utilities|Array|Length (G VName)))
    (if (== (Utilities|Array|Get(acopy) (G VSnd) k) snd)
      (bind h (CallFunction|MSNode :NS (Utilities|Array|Get(acopy) (G VNS) k) :N (Utilities|Array|Get(acopy) (G VName) k) :Var (Utilities|Array|Get(acopy) (G VVar) k)))
      (Utilities|Array|Add (G Handles) h)))
  (for j (range (Utilities|Array|Length (G LFrom)))
    (if (== (Utilities|Array|Get(acopy) (G LSnd) j) snd)
      (CallFunction|VoiceLink :J j :HP hp :HV hv :HC hc)))
  (for d (range (Utilities|Array|Length (G DNode)))
    (if (== (Utilities|Array|Get(acopy) (G DSnd) d) snd)
      (CallFunction|VoiceDef2 :D d :Period Period :Fb Fb :Pan Pan))))

;;@ BuildFX2
(fn BuildFX2 ()
  (bind nUE (Utilities|Name|MakeLiteralName "UE"))
  (bind nAud (Utilities|Name|MakeLiteralName "Audio"))
  (bind nMul (Utilities|Name|MakeLiteralName "Multiply"))
  (bind nABF (Utilities|Name|MakeLiteralName "Audio by Float"))
  (bind nPO (Utilities|Name|MakeLiteralName "PrimaryOperand"))
  (bind nAO (Utilities|Name|MakeLiteralName "AdditionalOperands"))
  (bind nOut (Utilities|Name|MakeLiteralName "Out"))
  (bind nIL (Utilities|Name|MakeLiteralName "In Left"))
  (bind nIR (Utilities|Name|MakeLiteralName "In Right"))
  (bind nOL (Utilities|Name|MakeLiteralName "Out Left"))
  (bind nOR (Utilities|Name|MakeLiteralName "Out Right"))
  (bind nWet (Utilities|Name|MakeLiteralName "Wet Level"))
  (bind nDry (Utilities|Name|MakeLiteralName "Dry Level"))
  (bind one (Math|Float|MakeLiteralFloat 1.0))
  (bind gl (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumL) :To gl :InName nPO)
  (CallFunction|MSSet :To gl :InName nAO :Val (G Volume))
  (bind gr (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumR) :To gr :InName nPO)
  (CallFunction|MSSet :To gr :InName nAO :Val (G Volume))
  (bind sd (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Stereo Delay") :Var nAud))
  (bind cw (Utilities|Array|Get(acopy) (G SndChorus) (G SoundIndex)))
  (bind nFl (Utilities|Name|MakeLiteralName "Flanger"))
  (bind nNo (Utilities|Name|MakeLiteralName ""))
  (bind nIA (Utilities|Name|MakeLiteralName "In Audio"))
  (bind nOA (Utilities|Name|MakeLiteralName "Out Audio"))
  (bind nMix (Utilities|Name|MakeLiteralName "Mix Level"))
  (bind nRate (Utilities|Name|MakeLiteralName "Modulation Rate"))
  (bind nDep (Utilities|Name|MakeLiteralName "Modulation Depth"))
  (bind nCen (Utilities|Name|MakeLiteralName "Center Delay"))
  (bind dep (Math|Float|MakeLiteralFloat 0.5))
  (bind cen (Math|Float|MakeLiteralFloat 12.0))
  (bind fl (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (bind gol (CallFunction|MSOut :Node gl :OutName nOut))
  (CallFunction|MSConnect :OutH gol :To fl :InName nIA)
  (CallFunction|MSSet :To fl :InName nMix :Val cw)
  (CallFunction|MSSet :To fl :InName nRate :Val (Math|Float|MakeLiteralFloat 0.5))
  (CallFunction|MSSet :To fl :InName nDep :Val dep)
  (CallFunction|MSSet :To fl :InName nCen :Val cen)
  (bind fr (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (bind gor (CallFunction|MSOut :Node gr :OutName nOut))
  (CallFunction|MSConnect :OutH gor :To fr :InName nIA)
  (CallFunction|MSSet :To fr :InName nMix :Val cw)
  (CallFunction|MSSet :To fr :InName nRate :Val (Math|Float|MakeLiteralFloat 0.62))
  (CallFunction|MSSet :To fr :InName nDep :Val dep)
  (CallFunction|MSSet :To fr :InName nCen :Val cen)
  (bind flo (CallFunction|MSOut :Node fl :OutName nOA))
  (CallFunction|MSConnect :OutH flo :To sd :InName nIL)
  (bind fro (CallFunction|MSOut :Node fr :OutName nOA))
  (CallFunction|MSConnect :OutH fro :To sd :InName nIR)
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Delay Time") :Val (G DelayTime))
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Feedback") :Val (G DelayFeedback))
  (CallFunction|MSSet :To sd :InName nWet :Val (G DelayWet))
  (CallFunction|MSSet :To sd :InName nDry :Val one)
  (bind pr (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Plate Reverb") :Var (Utilities|Name|MakeLiteralName "Stereo")))
  (bind sol (CallFunction|MSOut :Node sd :OutName nOL))
  (CallFunction|MSConnect :OutH sol :To pr :InName nIL)
  (bind sor (CallFunction|MSOut :Node sd :OutName nOR))
  (CallFunction|MSConnect :OutH sor :To pr :InName nIR)
  (CallFunction|MSSet :To pr :InName nWet :Val (G ReverbWet))
  (CallFunction|MSSet :To pr :InName nDry :Val one)
  (CallFunction|MSSet :To pr :InName (Utilities|Name|MakeLiteralName "Decay") :Val (G ReverbDecay))
  (bind nLim (Utilities|Name|MakeLiteralName "Limiter"))
  (bind nAudPin (Utilities|Name|MakeLiteralName "Audio"))
  (bind nGain (Utilities|Name|MakeLiteralName "Input Gain dB"))
  (bind nThr (Utilities|Name|MakeLiteralName "Threshold dB"))
  (bind thr (Math|Float|MakeLiteralFloat -3.0))
  (bind ll (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind pol (CallFunction|MSOut :Node pr :OutName nOL))
  (CallFunction|MSConnect :OutH pol :To ll :InName nAudPin)
  (CallFunction|MSSet :To ll :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To ll :InName nThr :Val thr)
  (bind lol (CallFunction|MSOut :Node ll :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lol :InH (Utilities|Array|Get(acopy) (G AudioOuts) 0))
  (bind lr (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind por (CallFunction|MSOut :Node pr :OutName nOR))
  (CallFunction|MSConnect :OutH por :To lr :InName nAudPin)
  (CallFunction|MSSet :To lr :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To lr :InName nThr :Val thr)
  (bind lor (CallFunction|MSOut :Node lr :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lor :InH (Utilities|Array|Get(acopy) (G AudioOuts) 1)))

;; ---- 2026-10-28 (2a): destello donde el mando toca la cuerda (reserva de esferas aditivas) ----

;;@ SparkSlot
;; OBSOLETA: devuelve n despues del Add (bind re-evaluado). Usar SparkSlot2 (LastIndex), escrita a mano el 10-28.
(fn SparkSlot ()
  (bind n (Utilities|Array|Length (G SparkComps)))
  (if (< n (G SparkPool))
    (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
    (Components|StaticMesh|SetStaticMesh c (G SparkMesh))
    (Rendering|Material|SetMaterial c 0 (G SparkMat))
    (Collision|SetCollisionEnabled c "NoCollision")
    (Rendering|SetCastShadow c false)
    (Utilities|Array|Add (G SparkComps) c)
    (Utilities|Array|Add (G SparkAge) 99.0)
    (return n)
    (else
      (S SparkNext (select (>= (+ (G SparkNext) 1) n) 0 (+ (G SparkNext) 1)))
      (return (select (== (G SparkNext) 0) (- n 1) (- (G SparkNext) 1))))))

;;@ SparkTipZ
(fn SparkTipZ (Right)
  (bind q (select Right (G QCtrlR) (G QCtrlL)))
  (bind fallback (* (G StringLen) 0.4))
  (if (G DebugStrum)
    (return fallback)
    (else
      (Utilities|IsValid q
        (:"Is Valid"
          (bind hl (G HeadLocal))
          (return (.z (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Math|Transform|TransformLocation (Transformation|GetActorTransform q) (Math|Vector|MakeVector :X (select Right (.x hl) (neg (.x hl))) :Y (.y hl) :Z (.z hl)))))))
        (:"Is Not Valid" (return fallback))))))

;;@ Spark
(fn Spark (I Right)
  (if (G ShowSparks)
    (bind z (CallFunction|SparkTipZ :Right Right))
    (bind slot (CallFunction|SparkSlot))
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind fi (Math|Conversions|ToFloat(Integer) I))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind wp (Math|Transform|TransformLocation (Transformation|GetActorTransform) (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z (Math|Float|Clamp(Float) z 0.0 len))))
    (bind c (Utilities|Array|Get(acopy) (G SparkComps) slot))
    (Transformation|SetWorldLocation :self c :NewLocation wp :bSweep false :bTeleport true)
    (bind s0 (* (G SparkSize) 0.006))
    (Transformation|SetWorldScale3D c (Math|Vector|MakeVector :X s0 :Y s0 :Z s0))
    (Rendering|Material|SetVectorParameterValueonMaterials c "Color" (Math|Conversions|ToVector(LinearColor) (select Right (G RightColor) (G LeftColor))))
    (Rendering|Material|SetScalarParameterValueonMaterials c "Fade" 1.0)
    (Rendering|SetVisibility c true false)
    (Utilities|Array|SetArrayElem (G SparkAge) slot 0.0)))

;;@ SparkTick
(fn SparkTick (DT)
  (bind life (Math|Float|Max(Float) (G SparkLife) 0.05))
  (bind ages (G SparkAge))
  (for i (range (Utilities|Array|Length ages))
    (bind a (Utilities|Array|Get(acopy) ages i))
    (if (< a life)
      (bind a2 (+ a DT))
      (bind t (Math|Float|Clamp(Float) (/ a2 life) 0.0 1.0))
      (bind c (Utilities|Array|Get(acopy) (G SparkComps) i))
      (bind s (* (* (G SparkSize) 0.01) (+ 0.6 (* (G SparkGrow) t))))
      (Transformation|SetWorldScale3D c (Math|Vector|MakeVector :X s :Y s :Z s))
      (Rendering|Material|SetScalarParameterValueonMaterials c "Fade" (* (- 1.0 t) (- 1.0 t)))
      (Rendering|SetVisibility c (< a2 life) false)
      (Utilities|Array|SetArrayElem ages i a2))))

;; ---- 2026-10-28 (3a): PAD con nota sostenida. Cada voz suma la entrada Rel_i (trigger de release). Modo "hold" por sonido (SndHold) ----

;;@ VoiceDef3
(fn VoiceDef3 (D Period Fb Pan)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (CallFunction|MSSet :To (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)) :InName (Utilities|Array|Get(acopy) (G DIn) D) :Val (select (< v -1007.5) (* f 1.0035) (select (< v -1006.5) (* f 0.9965) (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v))))))))))

;;@ VoiceLink2
(fn VoiceLink2 (J HP HV HC HR)
  (bind from (Utilities|Array|Get(acopy) (G LFrom) J))
  (if (>= from 0)
    (bind o (CallFunction|MSOut :Node (Utilities|Array|Get(acopy) (G Handles) from) :OutName (Utilities|Array|Get(acopy) (G LOut) J)))
    (CallFunction|LinkTo :O o :J J)
    (else (CallFunction|LinkTo :O (select (== from -1) HP (select (== from -2) HV (select (== from -3) HC HR))) :J J))))

;;@ BuildVoice3
(fn BuildVoice3 (I Period Fb Pan)
  (bind snd (G SoundIndex))
  (bind hp (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G PluckN) I) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (bind hv (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G VelN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 0.5)))
  (bind hc (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G CutN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 4000.0)))
  (bind hr (CallFunction|MSInput :Nm (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (Utilities|Array|Clear (G Handles))
  (for k (range (Utilities|Array|Length (G VName)))
    (if (== (Utilities|Array|Get(acopy) (G VSnd) k) snd)
      (bind h (CallFunction|MSNode :NS (Utilities|Array|Get(acopy) (G VNS) k) :N (Utilities|Array|Get(acopy) (G VName) k) :Var (Utilities|Array|Get(acopy) (G VVar) k)))
      (Utilities|Array|Add (G Handles) h)))
  (for j (range (Utilities|Array|Length (G LFrom)))
    (if (== (Utilities|Array|Get(acopy) (G LSnd) j) snd)
      (CallFunction|VoiceLink2 :J j :HP hp :HV hv :HC hc :HR hr)))
  (for d (range (Utilities|Array|Length (G DNode)))
    (if (== (Utilities|Array|Get(acopy) (G DSnd) d) snd)
      (CallFunction|VoiceDef3 :D d :Period Period :Fb Fb :Pan Pan))))

;;@ HoldIndex
(fn HoldIndex (P)
  (bind n (G NumStrings))
  (bind sp (G Spacing))
  (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
  (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
  (bind i (Math|Float|Round (/ (+ (.y P) half) sp)))
  (bind fi (Math|Conversions|ToFloat(Integer) i))
  (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
  (return (select (and (and (< (Math|Float|Absolute(Float) (.x P)) (G PlaneTol)) (and (>= i 0) (< i n))) (and (< (Math|Float|Absolute(Float) (- (.y P) (- (* fi sp) half))) (G HoldWidth)) (and (> (.z P) 0.0) (< (.z P) len)))) i -1)))

;;@ NoteOffIf
(fn NoteOffIf (I Right)
  (if (and (>= I 0) (!= I (- (select Right (G HeldL1) (G HeldR1)) 1)))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP release " :B (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))

;;@ NoteOnIf
(fn NoteOnIf (I Speed Right)
  (if (>= I 0)
    (CallFunction|Pluck :I I :Speed Speed :Right Right)))

;;@ HoldSustain
(fn HoldSustain (I)
  (if (>= I 0)
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) (G HoldGlow)))
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Energy" e)
    (Utilities|Array|SetArrayElem (G Energy) I e)))

;;@ HoldChange
(fn HoldChange (Old New Speed Right)
  (CallFunction|NoteOffIf :I Old :Right Right)
  (CallFunction|NoteOnIf :I New :Speed Speed :Right Right)
  (if Right
    (S HeldR1 (+ New 1))
    (else (S HeldL1 (+ New 1)))))

;;@ HoldStep
(fn HoldStep (P0 P1 DT Right)
  (bind cur (CallFunction|HoldIndex :P P1))
  (bind held (- (select Right (G HeldR1) (G HeldL1)) 1))
  (if (!= cur held)
    (CallFunction|HoldChange :Old held :New cur :Speed (/ (Math|Vector|VectorLength (- P1 P0)) DT) :Right Right)
    (else (CallFunction|HoldSustain :I cur))))

;;@ DetectAll
(fn DetectAll (P0 P1 DT Right Has)
  (if (== (Utilities|Array|Get(acopy) (G SndHold) (G SoundIndex)) 1)
    (CallFunction|HoldStep :P0 P0 :P1 P1 :DT DT :Right Right)
    (else (CallFunction|DetectStrum :P0 P0 :P1 P1 :DT DT :Right Right :Has Has))))

;;@ DetectPoke2
(fn DetectPoke2 (P0 P1 DT Right Has)
  (if (!= (Utilities|Array|Get(acopy) (G SndHold) (G SoundIndex)) 1)
    (CallFunction|DetectPoke :P0 P0 :P1 P1 :DT DT :Right Right :Has Has)))

;; ---- 2026-10-28 (4a): pad expresivo. El destello se queda mientras se sostiene y sigue a la mano; subir/bajar la mano = brillo (corte), relativo a la altura del primer toque ----

;;@ HoldBegin
(fn HoldBegin (I Right Z)
  (if (>= I 0)
    (Audio|Parameter|SetFloatParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G CutN) I) :InFloat (G PadCutBase))
    (if Right
      (S HoldZ0R Z)
      (S HoldSparkR (G LastSpark))
      (else (S HoldZ0L Z) (S HoldSparkL (G LastSpark))))))

;;@ HoldSustain2
(fn HoldSustain2 (I Right Z)
  (if (>= I 0)
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) (G HoldGlow)))
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Energy" e)
    (Utilities|Array|SetArrayElem (G Energy) I e)
    (bind dz (- Z (select Right (G HoldZ0R) (G HoldZ0L))))
    (bind cut (Math|Float|Clamp(Float) (* (G PadCutBase) (Math|Float|Power 2.0 (* dz (G PadOctPerCm)))) (G PadCutMin) (G PadCutMax)))
    (Audio|Parameter|SetFloatParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G CutN) I) :InFloat cut)
    (bind slot (select Right (G HoldSparkR) (G HoldSparkL)))
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind fi (Math|Conversions|ToFloat(Integer) I))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind wp (Math|Transform|TransformLocation (Transformation|GetActorTransform) (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z (Math|Float|Clamp(Float) Z 0.0 len))))
    (Transformation|SetWorldLocation :self (Utilities|Array|Get(acopy) (G SparkComps) slot) :NewLocation wp :bSweep false :bTeleport true)
    (Utilities|Array|SetArrayElem (G SparkAge) slot (G HoldSparkAge))))

;;@ HoldChange2
(fn HoldChange2 (Old New Speed Right Z)
  (CallFunction|NoteOffIf :I Old :Right Right)
  (CallFunction|NoteOnIf :I New :Speed Speed :Right Right)
  (CallFunction|HoldBegin :I New :Right Right :Z Z)
  (if Right
    (S HeldR1 (+ New 1))
    (else (S HeldL1 (+ New 1)))))

;;@ HoldStep2
(fn HoldStep2 (P0 P1 DT Right)
  (bind cur (CallFunction|HoldIndex :P P1))
  (bind held (- (select Right (G HeldR1) (G HeldL1)) 1))
  (if (!= cur held)
    (CallFunction|HoldChange2 :Old held :New cur :Speed (/ (Math|Vector|VectorLength (- P1 P0)) DT) :Right Right :Z (.z P1))
    (else (CallFunction|HoldSustain2 :I cur :Right Right :Z (.z P1)))))

;; ---- 2026-10-28: guarda del destello sostenido (HoldSustain2 movia un destello inexistente en el primer toque) ----

;;@ KeepSpark
(fn KeepSpark (Slot I Z)
  (if (Utilities|Array|IsValidIndex (G SparkComps) Slot)
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind fi (Math|Conversions|ToFloat(Integer) I))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind wp (Math|Transform|TransformLocation (Transformation|GetActorTransform) (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z (Math|Float|Clamp(Float) Z 0.0 len))))
    (Transformation|SetWorldLocation :self (Utilities|Array|Get(acopy) (G SparkComps) Slot) :NewLocation wp :bSweep false :bTeleport true)
    (Utilities|Array|SetArrayElem (G SparkAge) Slot (G HoldSparkAge))))

;;@ HoldSustain3
(fn HoldSustain3 (I Right Z)
  (if (>= I 0)
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) (G HoldGlow)))
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Energy" e)
    (Utilities|Array|SetArrayElem (G Energy) I e)
    (bind dz (- Z (select Right (G HoldZ0R) (G HoldZ0L))))
    (bind cut (Math|Float|Clamp(Float) (* (G PadCutBase) (Math|Float|Power 2.0 (* dz (G PadOctPerCm)))) (G PadCutMin) (G PadCutMax)))
    (Audio|Parameter|SetFloatParameter :self (Variables|Default|GetSynth) :InName (Utilities|Array|Get(acopy) (G CutN) I) :InFloat cut)
    (CallFunction|KeepSpark :Slot (select Right (G HoldSparkR) (G HoldSparkL)) :I I :Z Z)))

;; ---- 2026-10-28 (6a): LATCH con el gatillo. Con una cuerda sostenida, el gatillo la deja sonando mientras se mantiene; la mano queda libre para tocar otras (acorde de 4 con dos manos) ----

;;@ EnsureInput
;; Copia de BP_SeqRig_SC.EnsureInput (IMC_Weapon R/L, receta que anda en visor)
(fn EnsureInput ()
  (bind pc (Game|GetPlayerController 0))
  (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem pc))
  (Input|EnableInput self pc)
  (Input|AddMappingContext sub (G IMCRight) 1000 "(bIgnoreAllPressedKeysUntilRelease=False,bForceImmediately=True,bNotifyUserSettings=False)")
  (Input|AddMappingContext sub (G IMCLeft) 1000 "(bIgnoreAllPressedKeysUntilRelease=False,bForceImmediately=True,bNotifyUserSettings=False)")
  (S InputReady (and (Math|Conversions|ToBoolean(Integer) (Input|MappingQueries|HasMappingContext sub (G IMCRight))) (Math|Conversions|ToBoolean(Integer) (Input|MappingQueries|HasMappingContext sub (G IMCLeft)))))
  (if (G InputReady)
    (Development|PrintString :InString "HARP input ready (IMC_Weapon R/L)" :bPrintToScreen false)))

;;@ TrigDown
(fn TrigDown (Right)
  (if Right
    (S TrigR true)
    (else (S TrigL true))))

;;@ TrigUp
(fn TrigUp (Right)
  (if Right
    (S TrigR false)
    (else (S TrigL false))))

;;@ NoteOffIf2
;; NoteOffIf + no suelta una cuerda que tiene el latch de cualquiera de las dos manos
(fn NoteOffIf2 (I Right)
  (if (and (and (>= I 0) (!= I (- (select Right (G HeldL1) (G HeldR1)) 1))) (and (!= I (- (G LatchR1) 1)) (!= I (- (G LatchL1) 1))))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP release " :B (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))

;;@ LatchEnsure
(fn LatchEnsure ()
  (if (< (Utilities|Array|Length (G LatchComps)) 2)
    (Utilities|Array|Clear (G LatchComps))
    (for k (range 2)
      (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
      (Components|StaticMesh|SetStaticMesh c (G SparkMesh))
      (Rendering|Material|SetMaterial c 0 (G SparkMat))
      (Collision|SetCollisionEnabled c "NoCollision")
      (Rendering|SetCastShadow c false)
      (Rendering|SetVisibility c false false)
      (Utilities|Array|Add (G LatchComps) c))))

;;@ LatchShow
;; El destello fijo del latch: nace donde estaba el destello sostenido de esa mano
(fn LatchShow (Right)
  (bind slot (select Right (G HoldSparkR) (G HoldSparkL)))
  (if (and (G ShowSparks) (Utilities|Array|IsValidIndex (G SparkComps) slot))
    (CallFunction|LatchEnsure)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) (select Right 0 1)))
    (Transformation|SetWorldLocation :self c :NewLocation (Transformation|GetWorldLocation (Utilities|Array|Get(acopy) (G SparkComps) slot)) :bSweep false :bTeleport true)
    (bind t (Math|Float|Clamp(Float) (/ (G HoldSparkAge) (Math|Float|Max(Float) (G SparkLife) 0.05)) 0.0 1.0))
    (bind s (* (* (G SparkSize) 0.01) (+ 0.6 (* (G SparkGrow) t))))
    (Transformation|SetWorldScale3D c (Math|Vector|MakeVector :X s :Y s :Z s))
    (Rendering|Material|SetVectorParameterValueonMaterials c "Color" (Math|Conversions|ToVector(LinearColor) (select Right (G RightColor) (G LeftColor))))
    (Rendering|Material|SetScalarParameterValueonMaterials c "Fade" (* (- 1.0 t) (- 1.0 t)))
    (Rendering|SetVisibility c true false)))

;;@ LatchFade
;; Al soltar el gatillo, el destello fijo pasa a la reserva y se apaga como cualquier otro
(fn LatchFade (Right)
  (if (>= (Utilities|Array|Length (G LatchComps)) 2)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) (select Right 0 1)))
    (if (Rendering|IsVisible c)
      (bind slot (CallFunction|SparkSlot2))
      (bind sc (Utilities|Array|Get(acopy) (G SparkComps) slot))
      (Transformation|SetWorldLocation :self sc :NewLocation (Transformation|GetWorldLocation c) :bSweep false :bTeleport true)
      (Rendering|Material|SetVectorParameterValueonMaterials sc "Color" (Math|Conversions|ToVector(LinearColor) (select Right (G RightColor) (G LeftColor))))
      (Rendering|SetVisibility sc true false)
      (Utilities|Array|SetArrayElem (G SparkAge) slot (G HoldSparkAge))
      (Rendering|SetVisibility c false false))))

;;@ LatchRel
;; Suelta la nota del latch salvo que una mano la este tocando o la otra mano tambien la tenga
(fn LatchRel (I Right)
  (if (and (and (!= I (- (G HeldR1) 1)) (!= I (- (G HeldL1) 1))) (!= I (- (select Right (G LatchL1) (G LatchR1)) 1)))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP latch release " :B (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))

;;@ LatchClear
(fn LatchClear (Right)
  (if Right
    (S LatchR1 0)
    (else (S LatchL1 0))))

;;@ LatchFree
(fn LatchFree (Right I)
  (CallFunction|LatchFade :Right Right)
  (CallFunction|LatchRel :I I :Right Right)
  (CallFunction|LatchClear :Right Right))

;;@ LatchSet
(fn LatchSet (Right)
  (CallFunction|LatchShow :Right Right)
  (bind pc (Game|GetPlayerController 0))
  (bind hs (* (G HapticScale) 0.6))
  (if Right
    (S LatchR1 (G HeldR1))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP latch " :B (Utilities|String|ToString(Integer) (- (G HeldR1) 1))) :bPrintToScreen false)
    (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right" :Scale hs :bLoop false)
    (else
      (S LatchL1 (G HeldL1))
      (Development|PrintString :InString (Utilities|String|Append :A "HARP latch " :B (Utilities|String|ToString(Integer) (- (G HeldL1) 1))) :bPrintToScreen false)
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left" :Scale hs :bLoop false))))

;;@ LatchHold
;; Mientras el gatillo sigue apretado, la cuerda del latch queda encendida; si se solto, se libera
(fn LatchHold (I Right Trig)
  (if Trig
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) (G HoldGlow)))
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Energy" e)
    (Utilities|Array|SetArrayElem (G Energy) I e)
    (else (CallFunction|LatchFree :Right Right :I I))))

;;@ LatchHand
;; Por cuadro y por mano: gatillo apretado + cuerda sostenida + sin latch = latch. Con latch: mantener o liberar
(fn LatchHand (Right)
  (bind latch (- (select Right (G LatchR1) (G LatchL1)) 1))
  (bind trig (and (select Right (G TrigR) (G TrigL)) (G TriggerLatch)))
  (if (>= latch 0)
    (CallFunction|LatchHold :I latch :Right Right :Trig trig)
    (else
      (if (and trig (> (select Right (G HeldR1) (G HeldL1)) 0))
        (CallFunction|LatchSet :Right Right)))))

;;@ LatchTick
(fn LatchTick ()
  (CallFunction|LatchHand :Right (Math|Boolean|MakeLiteralBool true))
  (CallFunction|LatchHand :Right (Math|Boolean|MakeLiteralBool false))
  (if (not (G InputReady))
    (CallFunction|EnsureInput)))

;; ---- 2026-10-28 (7a): SNAP del pad (la cuerda atrapa la mano cerca y no la suelta facil) + LUZ de la cuerda tocada separada de la vibracion ----

;;@ HoldIndex2
;; Como HoldIndex, con iman: atrapa a SnapCatch de mas; la cuerda sostenida se mantiene hasta SnapHold de mas en profundidad y en las puntas, y hacia el costado SnapSide mas que la captura (sin pasar la mitad del espaciado + SnapSide): histeresis, entre dos cuerdas no titila
(fn HoldIndex2 (P Held)
  (bind n (G NumStrings))
  (bind sp (G Spacing))
  (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
  (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
  (bind i (Math|Integer|Clamp(Integer) (Math|Float|Round (/ (+ (.y P) half) sp)) 0 (- n 1)))
  (bind fi (Math|Conversions|ToFloat(Integer) i))
  (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
  (bind ax (Math|Float|Absolute(Float) (.x P)))
  (bind sc (G SnapCatch))
  (bind catch (and (and (< ax (+ (G PlaneTol) sc)) (< (Math|Float|Absolute(Float) (- (.y P) (- (* fi sp) half))) (+ (G HoldWidth) sc))) (and (> (.z P) (neg sc)) (< (.z P) (+ len sc)))))
  (bind fh (Math|Conversions|ToFloat(Integer) Held))
  (bind lenh (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fh nm1)))))
  (bind sh (+ sc (G SnapHold)))
  (bind keep (and (and (>= Held 0) (< ax (+ (G PlaneTol) sh))) (and (< (Math|Float|Absolute(Float) (- (.y P) (- (* fh sp) half))) (Math|Float|Min(Float) (+ (+ (G HoldWidth) sc) (G SnapSide)) (+ (* sp 0.5) (G SnapSide)))) (and (> (.z P) (neg sh)) (< (.z P) (+ lenh sh))))))
  (return (select keep Held (select catch i -1))))

;;@ HoldStep3
(fn HoldStep3 (P0 P1 DT Right)
  (bind held (- (select Right (G HeldR1) (G HeldL1)) 1))
  (bind cur (CallFunction|HoldIndex2 :P P1 :Held held))
  (if (!= cur held)
    (CallFunction|HoldChange2 :Old held :New cur :Speed (/ (Math|Vector|VectorLength (- P1 P0)) DT) :Right Right :Z (.z P1))
    (else (CallFunction|HoldSustain3 :I cur :Right Right :Z (.z P1)))))

;;@ LightLook
(fn LightLook (I)
  (bind c (Utilities|Array|Get(acopy) (G Strings) I))
  (Rendering|Material|SetScalarParameterValueonMaterials c "Light" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitGlow" (G LitGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitSat" (G LitSat))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitThick" (G LitThick)))

;;@ LightEnsure
;; Una vez (o si cambia el numero de cuerdas): dimensiona Light/LightSeen y carga las perillas de luz en el material de cada cuerda
(fn LightEnsure ()
  (bind n (Utilities|Array|Length (G Strings)))
  (if (!= (Utilities|Array|Length (G Light)) n)
    (Utilities|Array|Resize (G Light) n)
    (Utilities|Array|Resize (G LightSeen) n)
    (for i (range n)
      (CallFunction|LightLook :I i))))

;;@ LightSet
(fn LightSet (I L Seen)
  (Utilities|Array|SetArrayElem (G Light) I L)
  (Utilities|Array|SetArrayElem (G LightSeen) I Seen)
  (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Light" L))

;;@ LightOne
;; Toque nuevo (LastPluck mas nuevo que lo visto) = luz 1; si no, baja en LightDecay s. Sostenida o con latch = al menos HoldLight
(fn LightOne (I Step)
  (bind l0 (Utilities|Array|Get(acopy) (G Light) I))
  (bind lp (Utilities|Array|Get(acopy) (G LastPluck) I))
  (bind fresh (> lp (Utilities|Array|Get(acopy) (G LightSeen) I)))
  (bind held (or (or (== I (- (G HeldR1) 1)) (== I (- (G HeldL1) 1))) (or (== I (- (G LatchR1) 1)) (== I (- (G LatchL1) 1)))))
  (bind l1 (select fresh 1.0 (Math|Float|Max(Float) (- l0 Step) 0.0)))
  (bind l2 (select held (Math|Float|Max(Float) l1 (G HoldLight)) l1))
  (if (or (> l0 0.0) (> l2 0.0))
    (CallFunction|LightSet :I I :L l2 :Seen lp)))

;;@ LightTick
(fn LightTick (DT)
  (CallFunction|LightEnsure)
  (bind step (/ DT (Math|Float|Max(Float) (G LightDecay) 0.05)))
  (for i (range (Utilities|Array|Length (G Strings)))
    (CallFunction|LightOne :I i :Step step)))

;; ---- 2026-10-28 (8a): cada nota con su color (por nota musical: las octavas comparten color) y la esfera vibrando a un ritmo que sube con la nota ----

;;@ NoteMidi
;; Igual que BuildBody: raiz + escala[i mod k] + 12 * (i div k)
(fn NoteMidi (I)
  (bind k (Math|Integer|Max(Integer) (Utilities|Array|Length (G ScaleSteps)) 1))
  (return (+ (+ (G RootNote) (Utilities|Array|Get(acopy) (G ScaleSteps) (- I (* k (/ I k))))) (* 12 (/ I k)))))

;;@ NoteColor
;; Tono = NoteHueStart + NoteHueRange * (nota mod 12) / 12, en grados; saturacion NoteSat
(fn NoteColor (I)
  (bind m (CallFunction|NoteMidi :I I))
  (bind pc (- m (* 12 (/ m 12))))
  (bind h (+ (+ (G NoteHueStart) (* (G NoteHueRange) (/ (Math|Conversions|ToFloat(Integer) pc) 12.0))) 720.0))
  (bind hw (- h (* 360.0 (Math|Conversions|ToFloat(Integer) (Math|Float|Floor (/ h 360.0))))))
  (return (Math|Color|HSVtoRGB hw (G NoteSat) 1.0 1.0)))

;;@ NoteVibHz
;; Ritmo visible de la vibracion: SparkVibHz en la raiz, SparkVibOct octavas visuales por octava musical
(fn NoteVibHz (I)
  (bind m (CallFunction|NoteMidi :I I))
  (return (* (G SparkVibHz) (Math|Float|Power 2.0 (* (/ (Math|Conversions|ToFloat(Integer) (- m (G RootNote))) 12.0) (G SparkVibOct))))))

;;@ SparkTone
;; Color de la esfera = mezcla mano -> nota (NoteColorMix) y su vibracion
(fn SparkTone (C I Right)
  (bind nc (CallFunction|NoteColor :I I))
  (bind hz (CallFunction|NoteVibHz :I I))
  (Rendering|Material|SetVectorParameterValueonMaterials C "Color" (Math|Conversions|ToVector(LinearColor) (Math|Color|Lerp(LinearColor) (select Right (G RightColor) (G LeftColor)) nc (G NoteColorMix))))
  (Rendering|Material|SetScalarParameterValueonMaterials C "VibHz" hz)
  (Rendering|Material|SetScalarParameterValueonMaterials C "VibAmp" (G SparkVibAmp)))

;;@ LightLook
;; (8a) reescrita: tambien carga el color de la nota en la cuerda
(fn LightLook (I)
  (bind c (Utilities|Array|Get(acopy) (G Strings) I))
  (bind nc (CallFunction|NoteColor :I I))
  (Rendering|Material|SetScalarParameterValueonMaterials c "Light" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitGlow" (G LitGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitSat" (G LitSat))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitThick" (G LitThick))
  (Rendering|Material|SetVectorParameterValueonMaterials c "NoteColor" (Math|Conversions|ToVector(LinearColor) nc))
  (Rendering|Material|SetScalarParameterValueonMaterials c "NoteMix" (G NoteColorMix)))

;;@ LatchShow
;; (8a) reescrita: color y vibracion de la nota (SparkTone)
(fn LatchShow (Right)
  (bind slot (select Right (G HoldSparkR) (G HoldSparkL)))
  (if (and (G ShowSparks) (Utilities|Array|IsValidIndex (G SparkComps) slot))
    (CallFunction|LatchEnsure)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) (select Right 0 1)))
    (Transformation|SetWorldLocation :self c :NewLocation (Transformation|GetWorldLocation (Utilities|Array|Get(acopy) (G SparkComps) slot)) :bSweep false :bTeleport true)
    (bind t (Math|Float|Clamp(Float) (/ (G HoldSparkAge) (Math|Float|Max(Float) (G SparkLife) 0.05)) 0.0 1.0))
    (bind s (* (* (G SparkSize) 0.01) (+ 0.6 (* (G SparkGrow) t))))
    (Transformation|SetWorldScale3D c (Math|Vector|MakeVector :X s :Y s :Z s))
    (CallFunction|SparkTone :C c :I (- (select Right (G HeldR1) (G HeldL1)) 1) :Right Right)
    (Rendering|Material|SetScalarParameterValueonMaterials c "Fade" (* (- 1.0 t) (- 1.0 t)))
    (Rendering|SetVisibility c true false)))

;;@ LatchFade
;; (8a) reescrita: la esfera que pasa a la reserva conserva el color y la vibracion de la nota
(fn LatchFade (Right)
  (if (>= (Utilities|Array|Length (G LatchComps)) 2)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) (select Right 0 1)))
    (if (Rendering|IsVisible c)
      (bind slot (CallFunction|SparkSlot2))
      (bind sc (Utilities|Array|Get(acopy) (G SparkComps) slot))
      (Transformation|SetWorldLocation :self sc :NewLocation (Transformation|GetWorldLocation c) :bSweep false :bTeleport true)
      (CallFunction|SparkTone :C sc :I (- (select Right (G LatchR1) (G LatchL1)) 1) :Right Right)
      (Rendering|SetVisibility sc true false)
      (Utilities|Array|SetArrayElem (G SparkAge) slot (G HoldSparkAge))
      (Rendering|SetVisibility c false false))))

;; ---- 2026-10-28 (9a): LATCH en 4 ranuras (K 0 gatillo R, 1 gatillo L, 2 grip R, 3 grip L) -> acorde de 6. Latch1[K] = cuerda+1. Esfera mas arriba (SparkLift) ----

;;@ GripDown
(fn GripDown (Right)
  (if Right
    (S GripR true)
    (else (S GripL true))))

;;@ GripUp
(fn GripUp (Right)
  (if Right
    (S GripR false)
    (else (S GripL false))))

;;@ LatchAny
;; true si una ranura distinta de K (K = -1: cualquiera) tiene tomada la cuerda I
(fn LatchAny (I K)
  (Utilities|Array|Resize (G Latch1) (Math|Integer|Max(Integer) (Utilities|Array|Length (G Latch1)) 4))
  (bind l (G Latch1))
  (return (and (>= I 0) (or (or (and (!= K 0) (== I (- (Utilities|Array|Get(acopy) l 0) 1))) (and (!= K 1) (== I (- (Utilities|Array|Get(acopy) l 1) 1)))) (or (and (!= K 2) (== I (- (Utilities|Array|Get(acopy) l 2) 1))) (and (!= K 3) (== I (- (Utilities|Array|Get(acopy) l 3) 1))))))))

;;@ SparkTipZ2
(fn SparkTipZ2 (Right)
  (bind z (CallFunction|SparkTipZ :Right Right))
  (return (+ z (G SparkLift))))

;;@ SlotShow
(fn SlotShow (K)
  (bind right (== (- K (* 2 (/ K 2))) 0))
  (bind slot (select right (G HoldSparkR) (G HoldSparkL)))
  (if (and (G ShowSparks) (Utilities|Array|IsValidIndex (G SparkComps) slot))
    (CallFunction|LatchEnsure)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) K))
    (Transformation|SetWorldLocation :self c :NewLocation (Transformation|GetWorldLocation (Utilities|Array|Get(acopy) (G SparkComps) slot)) :bSweep false :bTeleport true)
    (bind t (Math|Float|Clamp(Float) (/ (G HoldSparkAge) (Math|Float|Max(Float) (G SparkLife) 0.05)) 0.0 1.0))
    (bind s (* (* (G SparkSize) 0.01) (+ 0.6 (* (G SparkGrow) t))))
    (Transformation|SetWorldScale3D c (Math|Vector|MakeVector :X s :Y s :Z s))
    (CallFunction|SparkTone :C c :I (- (select right (G HeldR1) (G HeldL1)) 1) :Right right)
    (Rendering|Material|SetScalarParameterValueonMaterials c "Fade" (* (- 1.0 t) (- 1.0 t)))
    (Rendering|SetVisibility c true false)))

;;@ SlotFade
(fn SlotFade (K I)
  (if (> (Utilities|Array|Length (G LatchComps)) K)
    (bind c (Utilities|Array|Get(acopy) (G LatchComps) K))
    (if (Rendering|IsVisible c)
      (bind slot (CallFunction|SparkSlot2))
      (bind sc (Utilities|Array|Get(acopy) (G SparkComps) slot))
      (Transformation|SetWorldLocation :self sc :NewLocation (Transformation|GetWorldLocation c) :bSweep false :bTeleport true)
      (CallFunction|SparkTone :C sc :I I :Right (== (- K (* 2 (/ K 2))) 0))
      (Rendering|SetVisibility sc true false)
      (Utilities|Array|SetArrayElem (G SparkAge) slot (G HoldSparkAge))
      (Rendering|SetVisibility c false false))))

;;@ SlotRel
;; Suelta la nota salvo que una mano la este tocando u otra ranura la tenga
(fn SlotRel (K I)
  (bind la (CallFunction|LatchAny :I I :K K))
  (if (and (and (!= I (- (G HeldR1) 1)) (!= I (- (G HeldL1) 1))) (not la))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))))
    (Development|PrintString :InString (Utilities|String|Append :A (Utilities|String|Append :A "HARP latch release k=" :B (Utilities|String|ToString(Integer) K)) :B (Utilities|String|Append :A " i=" :B (Utilities|String|ToString(Integer) I))) :bPrintToScreen false)))

;;@ SlotFree
(fn SlotFree (K I)
  (CallFunction|SlotFade :K K :I I)
  (CallFunction|SlotRel :K K :I I)
  (Utilities|Array|SetArrayElem (G Latch1) K 0))

;;@ SlotSet
(fn SlotSet (K)
  (bind right (== (- K (* 2 (/ K 2))) 0))
  (bind held (select right (G HeldR1) (G HeldL1)))
  (CallFunction|SlotShow :K K)
  (Utilities|Array|SetArrayElem (G Latch1) K held)
  (Development|PrintString :InString (Utilities|String|Append :A (Utilities|String|Append :A "HARP latch k=" :B (Utilities|String|ToString(Integer) K)) :B (Utilities|String|Append :A " i=" :B (Utilities|String|ToString(Integer) (- held 1)))) :bPrintToScreen false)
  (bind pc (Game|GetPlayerController 0))
  (bind hs (* (G HapticScale) 0.6))
  (if right
    (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right" :Scale hs :bLoop false)
    (else (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left" :Scale hs :bLoop false))))

;;@ SlotHold
(fn SlotHold (K I Down)
  (if Down
    (bind e (Math|Float|Max(Float) (Utilities|Array|Get(acopy) (G Energy) I) (G HoldGlow)))
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Energy" e)
    (Utilities|Array|SetArrayElem (G Energy) I e)
    (else (CallFunction|SlotFree :K K :I I))))

;;@ SlotHand
;; Por cuadro y por ranura: boton apretado + cuerda sostenida que ninguna otra ranura tiene = latch. Con latch: mantener o liberar
(fn SlotHand (K)
  (bind right (== (- K (* 2 (/ K 2))) 0))
  (bind latch (- (Utilities|Array|Get(acopy) (G Latch1) K) 1))
  (bind down (select (< K 2) (and (select right (G TrigR) (G TrigL)) (G TriggerLatch)) (and (select right (G GripR) (G GripL)) (G GripLatch))))
  (bind hi (- (select right (G HeldR1) (G HeldL1)) 1))
  (bind taken (CallFunction|LatchAny :I hi :K K))
  (if (>= latch 0)
    (CallFunction|SlotHold :K K :I latch :Down down)
    (else
      (if (and (and down (>= hi 0)) (not taken))
        (CallFunction|SlotSet :K K)))))

;;@ LatchEnsure
;; (9a) reescrita: 4 ranuras
(fn LatchEnsure ()
  (Utilities|Array|Resize (G Latch1) (Math|Integer|Max(Integer) (Utilities|Array|Length (G Latch1)) 4))
  (if (< (Utilities|Array|Length (G LatchComps)) 4)
    (Utilities|Array|Clear (G LatchComps))
    (for k (range 4)
      (bind c (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
      (Components|StaticMesh|SetStaticMesh c (G SparkMesh))
      (Rendering|Material|SetMaterial c 0 (G SparkMat))
      (Collision|SetCollisionEnabled c "NoCollision")
      (Rendering|SetCastShadow c false)
      (Rendering|SetVisibility c false false)
      (Utilities|Array|Add (G LatchComps) c))))

;;@ LatchTick
;; (9a) reescrita: las 4 ranuras
(fn LatchTick ()
  (CallFunction|LatchEnsure)
  (for k (range 4)
    (CallFunction|SlotHand :K k))
  (if (not (G InputReady))
    (CallFunction|EnsureInput)))

;;@ NoteOffIf2
;; (9a) reescrita: no suelta una cuerda que tenga cualquier ranura
(fn NoteOffIf2 (I Right)
  (bind la (CallFunction|LatchAny :I I :K (Math|Integer|MakeLiteralInt -1)))
  (if (and (and (>= I 0) (!= I (- (select Right (G HeldL1) (G HeldR1)) 1))) (not la))
    (Audio|Parameter|ExecuteTriggerParameter :self (Variables|Default|GetSynth) :InName (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))))
    (Development|PrintString :InString (Utilities|String|Append :A "HARP release " :B (Utilities|String|ToString(Integer) I)) :bPrintToScreen false)))

;;@ LightOne
;; (9a) reescrita: sostenida = una mano la toca o una ranura la tiene
(fn LightOne (I Step)
  (bind la (CallFunction|LatchAny :I I :K (Math|Integer|MakeLiteralInt -1)))
  (bind l0 (Utilities|Array|Get(acopy) (G Light) I))
  (bind lp (Utilities|Array|Get(acopy) (G LastPluck) I))
  (bind fresh (> lp (Utilities|Array|Get(acopy) (G LightSeen) I)))
  (bind held (or (or (== I (- (G HeldR1) 1)) (== I (- (G HeldL1) 1))) la))
  (bind l1 (select fresh 1.0 (Math|Float|Max(Float) (- l0 Step) 0.0)))
  (bind l2 (select held (Math|Float|Max(Float) l1 (G HoldLight)) l1))
  (if (or (> l0 0.0) (> l2 0.0))
    (CallFunction|LightSet :I I :L l2 :Seen lp)))

;;@ KeepSpark
;; (9a) reescrita: la esfera sostenida va SparkLift mas arriba que la cabeza del mando
(fn KeepSpark (Slot I Z)
  (if (Utilities|Array|IsValidIndex (G SparkComps) Slot)
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind fi (Math|Conversions|ToFloat(Integer) I))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind wp (Math|Transform|TransformLocation (Transformation|GetActorTransform) (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z (Math|Float|Clamp(Float) (+ Z (G SparkLift)) 0.0 len))))
    (Transformation|SetWorldLocation :self (Utilities|Array|Get(acopy) (G SparkComps) Slot) :NewLocation wp :bSweep false :bTeleport true)
    (Utilities|Array|SetArrayElem (G SparkAge) Slot (G HoldSparkAge))))


;; ---- 2026-10-28 (10a): CHORUS de verdad (el de BuildFX2 tenia 0,5 ms de profundidad: ~3 cents, no se oia) ----

;;@ BuildFX3
;; Copia de BuildFX2 con un chorus de verdad: 2 voces moduladas por lado (Flanger al 100 % humedo, la profundidad del Flanger es en ms), mezcla seca + humeda por SndChorus[SoundIndex]
(fn BuildFX3 ()
  (bind nUE (Utilities|Name|MakeLiteralName "UE"))
  (bind nAud (Utilities|Name|MakeLiteralName "Audio"))
  (bind nMul (Utilities|Name|MakeLiteralName "Multiply"))
  (bind nABF (Utilities|Name|MakeLiteralName "Audio by Float"))
  (bind nPO (Utilities|Name|MakeLiteralName "PrimaryOperand"))
  (bind nAO (Utilities|Name|MakeLiteralName "AdditionalOperands"))
  (bind nOut (Utilities|Name|MakeLiteralName "Out"))
  (bind nIL (Utilities|Name|MakeLiteralName "In Left"))
  (bind nIR (Utilities|Name|MakeLiteralName "In Right"))
  (bind nOL (Utilities|Name|MakeLiteralName "Out Left"))
  (bind nOR (Utilities|Name|MakeLiteralName "Out Right"))
  (bind nWet (Utilities|Name|MakeLiteralName "Wet Level"))
  (bind nDry (Utilities|Name|MakeLiteralName "Dry Level"))
  (bind one (Math|Float|MakeLiteralFloat 1.0))
  (bind gl (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumL) :To gl :InName nPO)
  (CallFunction|MSSet :To gl :InName nAO :Val (G Volume))
  (bind gr (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH (G SumR) :To gr :InName nPO)
  (CallFunction|MSSet :To gr :InName nAO :Val (G Volume))
  (bind sd (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Stereo Delay") :Var nAud))
  (bind cw (Utilities|Array|Get(acopy) (G SndChorus) (G SoundIndex)))
  (bind nFl (Utilities|Name|MakeLiteralName "Flanger"))
  (bind nNo (Utilities|Name|MakeLiteralName ""))
  (bind nAdd (Utilities|Name|MakeLiteralName "Add"))
  (bind nIA (Utilities|Name|MakeLiteralName "In Audio"))
  (bind nOA (Utilities|Name|MakeLiteralName "Out Audio"))
  (bind nMix (Utilities|Name|MakeLiteralName "Mix Level"))
  (bind nRate (Utilities|Name|MakeLiteralName "Modulation Rate"))
  (bind nDep (Utilities|Name|MakeLiteralName "Modulation Depth"))
  (bind nCen (Utilities|Name|MakeLiteralName "Center Delay"))
  (bind r0 (G ChorusRate))
  (bind d0 (G ChorusDelay))
  (bind a0 (G ChorusDepth))
  (bind wetg (* 0.5 cw))
  (bind dryg (- 1.0 (* 0.35 cw)))
  (bind gol (CallFunction|MSOut :Node gl :OutName nOut))
  (bind l1 (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (CallFunction|MSConnect :OutH gol :To l1 :InName nIA)
  (CallFunction|MSSet :To l1 :InName nMix :Val one)
  (CallFunction|MSSet :To l1 :InName nRate :Val r0)
  (CallFunction|MSSet :To l1 :InName nCen :Val d0)
  (CallFunction|MSSet :To l1 :InName nDep :Val a0)
  (bind l2 (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (CallFunction|MSConnect :OutH gol :To l2 :InName nIA)
  (CallFunction|MSSet :To l2 :InName nMix :Val one)
  (CallFunction|MSSet :To l2 :InName nRate :Val (* r0 1.55))
  (CallFunction|MSSet :To l2 :InName nCen :Val (* d0 1.4))
  (CallFunction|MSSet :To l2 :InName nDep :Val (* a0 0.6))
  (bind la (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
  (bind o_l1_1 (CallFunction|MSOut :Node l1 :OutName nOA))
  (CallFunction|MSConnect :OutH o_l1_1 :To la :InName nPO)
  (bind o_l2_2 (CallFunction|MSOut :Node l2 :OutName nOA))
  (CallFunction|MSConnect :OutH o_l2_2 :To la :InName nAO)
  (bind lw (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (bind o_la_3 (CallFunction|MSOut :Node la :OutName nOut))
  (CallFunction|MSConnect :OutH o_la_3 :To lw :InName nPO)
  (CallFunction|MSSet :To lw :InName nAO :Val wetg)
  (bind ld (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH gol :To ld :InName nPO)
  (CallFunction|MSSet :To ld :InName nAO :Val dryg)
  (bind lo (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
  (bind o_lw_4 (CallFunction|MSOut :Node lw :OutName nOut))
  (CallFunction|MSConnect :OutH o_lw_4 :To lo :InName nPO)
  (bind o_ld_5 (CallFunction|MSOut :Node ld :OutName nOut))
  (CallFunction|MSConnect :OutH o_ld_5 :To lo :InName nAO)
  (bind o_lo_6 (CallFunction|MSOut :Node lo :OutName nOut))
  (CallFunction|MSConnect :OutH o_lo_6 :To sd :InName nIL)
  (bind gor (CallFunction|MSOut :Node gr :OutName nOut))
  (bind r1 (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (CallFunction|MSConnect :OutH gor :To r1 :InName nIA)
  (CallFunction|MSSet :To r1 :InName nMix :Val one)
  (CallFunction|MSSet :To r1 :InName nRate :Val (* r0 1.09))
  (CallFunction|MSSet :To r1 :InName nCen :Val (+ d0 1.3))
  (CallFunction|MSSet :To r1 :InName nDep :Val a0)
  (bind r2 (CallFunction|MSNode :NS nUE :N nFl :Var nNo))
  (CallFunction|MSConnect :OutH gor :To r2 :InName nIA)
  (CallFunction|MSSet :To r2 :InName nMix :Val one)
  (CallFunction|MSSet :To r2 :InName nRate :Val (* r0 1.42))
  (CallFunction|MSSet :To r2 :InName nCen :Val (* d0 1.25))
  (CallFunction|MSSet :To r2 :InName nDep :Val (* a0 0.6))
  (bind ra (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
  (bind o_r1_7 (CallFunction|MSOut :Node r1 :OutName nOA))
  (CallFunction|MSConnect :OutH o_r1_7 :To ra :InName nPO)
  (bind o_r2_8 (CallFunction|MSOut :Node r2 :OutName nOA))
  (CallFunction|MSConnect :OutH o_r2_8 :To ra :InName nAO)
  (bind rw (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (bind o_ra_9 (CallFunction|MSOut :Node ra :OutName nOut))
  (CallFunction|MSConnect :OutH o_ra_9 :To rw :InName nPO)
  (CallFunction|MSSet :To rw :InName nAO :Val wetg)
  (bind rd (CallFunction|MSNode :NS nUE :N nMul :Var nABF))
  (CallFunction|MSConnect :OutH gor :To rd :InName nPO)
  (CallFunction|MSSet :To rd :InName nAO :Val dryg)
  (bind ro (CallFunction|MSNode :NS nUE :N nAdd :Var nAud))
  (bind o_rw_10 (CallFunction|MSOut :Node rw :OutName nOut))
  (CallFunction|MSConnect :OutH o_rw_10 :To ro :InName nPO)
  (bind o_rd_11 (CallFunction|MSOut :Node rd :OutName nOut))
  (CallFunction|MSConnect :OutH o_rd_11 :To ro :InName nAO)
  (bind o_ro_12 (CallFunction|MSOut :Node ro :OutName nOut))
  (CallFunction|MSConnect :OutH o_ro_12 :To sd :InName nIR)
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Delay Time") :Val (G DelayTime))
  (CallFunction|MSSet :To sd :InName (Utilities|Name|MakeLiteralName "Feedback") :Val (G DelayFeedback))
  (CallFunction|MSSet :To sd :InName nWet :Val (G DelayWet))
  (CallFunction|MSSet :To sd :InName nDry :Val one)
  (bind pr (CallFunction|MSNode :NS nUE :N (Utilities|Name|MakeLiteralName "Plate Reverb") :Var (Utilities|Name|MakeLiteralName "Stereo")))
  (bind sol (CallFunction|MSOut :Node sd :OutName nOL))
  (CallFunction|MSConnect :OutH sol :To pr :InName nIL)
  (bind sor (CallFunction|MSOut :Node sd :OutName nOR))
  (CallFunction|MSConnect :OutH sor :To pr :InName nIR)
  (CallFunction|MSSet :To pr :InName nWet :Val (G ReverbWet))
  (CallFunction|MSSet :To pr :InName nDry :Val one)
  (CallFunction|MSSet :To pr :InName (Utilities|Name|MakeLiteralName "Decay") :Val (G ReverbDecay))
  (bind nLim (Utilities|Name|MakeLiteralName "Limiter"))
  (bind nAudPin (Utilities|Name|MakeLiteralName "Audio"))
  (bind nGain (Utilities|Name|MakeLiteralName "Input Gain dB"))
  (bind nThr (Utilities|Name|MakeLiteralName "Threshold dB"))
  (bind thr (Math|Float|MakeLiteralFloat -3.0))
  (bind ll (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind pol (CallFunction|MSOut :Node pr :OutName nOL))
  (CallFunction|MSConnect :OutH pol :To ll :InName nAudPin)
  (CallFunction|MSSet :To ll :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To ll :InName nThr :Val thr)
  (bind lol (CallFunction|MSOut :Node ll :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lol :InH (Utilities|Array|Get(acopy) (G AudioOuts) 0))
  (bind lr (CallFunction|MSNode :NS nUE :N nLim :Var nAud))
  (bind por (CallFunction|MSOut :Node pr :OutName nOR))
  (CallFunction|MSConnect :OutH por :To lr :InName nAudPin)
  (CallFunction|MSSet :To lr :InName nGain :Val (G MasterGainDb))
  (CallFunction|MSSet :To lr :InName nThr :Val thr)
  (bind lor (CallFunction|MSOut :Node lr :OutName nAudPin))
  (CallFunction|MSConnectH :OutH lor :InH (Utilities|Array|Get(acopy) (G AudioOuts) 1)))

;; ---- 2026-10-28 (12a): HALO que sube por la cuerda desde la esfera. Un toque = un pulso; sostenida = un pulso tras otro. Lo dibuja el material (HarpHalo); el BP le pasa edades relativas ----

;;@ HaloStart
;; Un toque: el halo sale a la altura de la esfera. Si la cuerda ya estaba emitiendo (sostenida), solo mueve el punto de salida
(fn HaloStart (I Z)
  (CallFunction|LightEnsure)
  (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "HaloZ" Z)
  (if (not (Utilities|Array|Get(acopy) (G HaloOn) I))
    (Utilities|Array|SetArrayElem (G HaloT0) I (Utilities|Time|GetGameTimeinSeconds))
    (Utilities|Array|SetArrayElem (G HaloT1) I (Utilities|Time|GetGameTimeinSeconds))))

;;@ HaloFlip
;; Empieza o termina el sostenido de la cuerda I: anota el momento
(fn HaloFlip (I Held Now)
  (if (!= Held (Utilities|Array|Get(acopy) (G HaloOn) I))
    (Utilities|Array|SetArrayElem (G HaloOn) I Held)
    (Utilities|Array|SetArrayElem (G HaloT1) I Now)))

;;@ HaloSend
;; Edades relativas, no tiempos absolutos (en el Quest las entradas del Custom van en media precision). A = desde que empezo a emitir, envuelta por periodo para que no crezca; B = desde que dejo de emitir (0 mientras sostiene)
(fn HaloSend (I Now)
  (bind c (Utilities|Array|Get(acopy) (G Strings) I))
  (bind spd (Math|Float|Max(Float) (G HaloSpeed) 1.0))
  (bind per (/ (Math|Float|Max(Float) (G HaloGap) (G HaloWidth)) spd))
  (bind amax (+ (/ (G HaloReach) spd) 1.0))
  (bind a (- Now (Utilities|Array|Get(acopy) (G HaloT0) I)))
  (bind aw (- a (* per (Math|Conversions|ToFloat(Integer) (Math|Float|Floor (/ (Math|Float|Max(Float) (- a amax) 0.0) per))))))
  (bind on (Utilities|Array|Get(acopy) (G HaloOn) I))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloA" aw)
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloB" (select on 0.0 (Math|Float|Min(Float) (- Now (Utilities|Array|Get(acopy) (G HaloT1) I)) (+ amax 1.0)))))

;;@ LightSet2
(fn LightSet2 (I L Seen Held)
  (Utilities|Array|SetArrayElem (G Light) I L)
  (Utilities|Array|SetArrayElem (G LightSeen) I Seen)
  (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "Light" L)
  (CallFunction|HaloFlip :I I :Held Held :Now (Utilities|Time|GetGameTimeinSeconds))
  (CallFunction|HaloSend :I I :Now (Utilities|Time|GetGameTimeinSeconds)))

;;@ LightOne
;; (12a) reescrita: igual que la 9a, y le pasa a LightSet2 si la cuerda esta sostenida (para el halo)
(fn LightOne (I Step)
  (bind la (CallFunction|LatchAny :I I :K (Math|Integer|MakeLiteralInt -1)))
  (bind l0 (Utilities|Array|Get(acopy) (G Light) I))
  (bind lp (Utilities|Array|Get(acopy) (G LastPluck) I))
  (bind fresh (> lp (Utilities|Array|Get(acopy) (G LightSeen) I)))
  (bind held (or (or (== I (- (G HeldR1) 1)) (== I (- (G HeldL1) 1))) la))
  (bind l1 (select fresh 1.0 (Math|Float|Max(Float) (- l0 Step) 0.0)))
  (bind l2 (select held (Math|Float|Max(Float) l1 (G HoldLight)) l1))
  (if (or (> l0 0.0) (> l2 0.0))
    (CallFunction|LightSet2 :I I :L l2 :Seen lp :Held held)))

;;@ LightEnsure
;; (12a) reescrita: tambien dimensiona los arreglos del halo
(fn LightEnsure ()
  (bind n (Utilities|Array|Length (G Strings)))
  (Utilities|Array|Resize (G HaloT0) n)
  (Utilities|Array|Resize (G HaloT1) n)
  (Utilities|Array|Resize (G HaloOn) n)
  (if (!= (Utilities|Array|Length (G Light)) n)
    (Utilities|Array|Resize (G Light) n)
    (Utilities|Array|Resize (G LightSeen) n)
    (for i (range n)
      (CallFunction|LightLook :I i))))

;;@ LightLook
;; (12a) reescrita: tambien carga el largo de la cuerda y las perillas del halo
(fn LightLook (I)
  (bind c (Utilities|Array|Get(acopy) (G Strings) I))
  (bind nc (CallFunction|NoteColor :I I))
  (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- (G NumStrings) 1)) 1.0))
  (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ (Math|Conversions|ToFloat(Integer) I) nm1)))))
  (Rendering|Material|SetScalarParameterValueonMaterials c "Light" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitGlow" (G LitGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitSat" (G LitSat))
  (Rendering|Material|SetScalarParameterValueonMaterials c "LitThick" (G LitThick))
  (Rendering|Material|SetVectorParameterValueonMaterials c "NoteColor" (Math|Conversions|ToVector(LinearColor) nc))
  (Rendering|Material|SetScalarParameterValueonMaterials c "NoteMix" (G NoteColorMix))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloLen" len)
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloSpeed" (G HaloSpeed))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloWidth" (G HaloWidth))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloGap" (G HaloGap))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloReach" (G HaloReach))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloSwell" (G HaloSwell))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloGlow" (G HaloGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloA" 50.0)
  (Rendering|Material|SetScalarParameterValueonMaterials c "HaloB" 50.0))

;;@ KeepSpark
;; (12a) reescrita: ademas mueve el punto de salida del halo con la esfera sostenida
(fn KeepSpark (Slot I Z)
  (if (Utilities|Array|IsValidIndex (G SparkComps) Slot)
    (bind n (G NumStrings))
    (bind sp (G Spacing))
    (bind nm1 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- n 1)) 1.0))
    (bind half (* (* (Math|Conversions|ToFloat(Integer) (- n 1)) 0.5) sp))
    (bind fi (Math|Conversions|ToFloat(Integer) I))
    (bind len (* (G StringLen) (- 1.0 (* (G LenTaper) (/ fi nm1)))))
    (bind zs (Math|Float|Clamp(Float) (+ Z (G SparkLift)) 0.0 len))
    (bind wp (Math|Transform|TransformLocation (Transformation|GetActorTransform) (Math|Vector|MakeVector :X 0.0 :Y (- (* fi sp) half) :Z zs)))
    (Transformation|SetWorldLocation :self (Utilities|Array|Get(acopy) (G SparkComps) Slot) :NewLocation wp :bSweep false :bTeleport true)
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) (G Strings) I) "HaloZ" zs)
    (Utilities|Array|SetArrayElem (G SparkAge) Slot (G HoldSparkAge))))

;; ---- 2026-10-28 (13a): EL HANG. Perilla InstrumentType (0 arpa, 1 hang): mismos sintes, otro formato. Cuerpo + 9 pads (mallas de Blender: SM_Hang_*), cada pad se hunde en SU eje; anillo que se expande en cada golpe (y queda vibrando si el sonido es sostenido) ----

;;@ HideStrings
(fn HideStrings ()
  (for i (range (Utilities|Array|Length (G Strings)))
    (Rendering|SetVisibility (Utilities|Array|Get(acopy) (G Strings) i) false false)))

;;@ BuildPad
;; Un pad (o el ding, I = 0) colgado del cuerpo en su transformada de Blender, y su anillo (plano aditivo) encima
(fn BuildPad (I)
  (bind r (Utilities|Array|Get(acopy) (G PadRad) I))
  (bind pad (AddComponent|Common|AddStaticMeshComponent :bManualAttachment true :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|AttachComponentToComponent :self pad :Parent (G HangBody))
  (Transformation|SetRelativeLocationAndRotation :self pad :NewLocation (Utilities|Array|Get(acopy) (G PadLoc) I) :NewRotation (Math|Rotator|MakeRotfromZ (Utilities|Array|Get(acopy) (G PadUp) I)) :bSweep false :bTeleport true)
  (Components|StaticMesh|SetStaticMesh pad (select (== I 0) (G HangDingMesh) (G HangPadMesh)))
  (Rendering|Material|SetMaterial pad 0 (G MatPadTop))
  (Rendering|Material|SetMaterial pad 1 (G MatPadSide))
  (Collision|SetCollisionEnabled pad "NoCollision")
  (Rendering|SetCastShadow pad false)
  (Utilities|Array|Add (G HangPads) pad)
  (bind ring (AddComponent|Common|AddStaticMeshComponent :bManualAttachment true :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|AttachComponentToComponent :self ring :Parent pad)
  (bind s (/ (* r 4.0) 100.0))
  (Transformation|SetRelativeLocation :self ring :NewLocation (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (+ (G PadTopH) 0.12)) :bSweep false :bTeleport true)
  (Transformation|SetRelativeScale3D ring (Math|Vector|MakeVector :X s :Y s :Z s))
  (Components|StaticMesh|SetStaticMesh ring (G RingMesh))
  (Rendering|Material|SetMaterial ring 0 (G MatRing))
  (Collision|SetCollisionEnabled ring "NoCollision")
  (Rendering|SetCastShadow ring false)
  (Rendering|SetVisibility ring false false)
  (Utilities|Array|Add (G HangRings) ring))

;;@ BuildHang
;; Script de construccion (despues de BuildStrings): en modo 1 esconde las cuerdas y arma el hang
(fn BuildHang ()
  (Utilities|Array|Clear (G HangPads))
  (Utilities|Array|Clear (G HangRings))
  (if (== (G InstrumentType) 1)
    (CallFunction|HideStrings)
    (bind body (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (G HangLoc) :Rotation (G HangRot))))
    (Components|StaticMesh|SetStaticMesh body (G HangBodyMesh))
    (Rendering|Material|SetMaterial body 0 (G MatHangBody))
    (Rendering|Material|SetMaterial body 1 (G MatHangPocket))
    (Rendering|Material|SetMaterial body 2 (G MatHangGroove))
    (Collision|SetCollisionEnabled body "NoCollision")
    (Rendering|SetCastShadow body false)
    (S HangBody body)
    (for i (range (Utilities|Array|Length (G PadLoc)))
      (CallFunction|BuildPad :I i))))

;;@ PadLook
;; En el primer cuadro: centro y eje de cada pad en el espacio del actor (en reposo) + color de su nota
(fn PadLook (I)
  (bind pad (Utilities|Array|Get(acopy) (G HangPads) I))
  (bind nc (CallFunction|NoteColor :I (Utilities|Array|Get(acopy) (G PadNote) I)))
  (Utilities|Array|Add (G PadC) (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (Transformation|GetWorldLocation pad)))
  (Utilities|Array|Add (G PadN) (Math|Transform|InverseTransformDirection (Transformation|GetActorTransform) (Transformation|GetUpVector pad)))
  (Utilities|Array|Add (G PadR) (Utilities|Array|Get(acopy) (G PadRad) I))
  (Rendering|Material|SetVectorParameterValueonMaterials pad "FlashColor" (Math|Conversions|ToVector(LinearColor) nc))
  (Rendering|Material|SetVectorParameterValueonMaterials pad "GrooveColor" (Math|Conversions|ToVector(LinearColor) nc))
  (Rendering|Material|SetScalarParameterValueonMaterials pad "GrooveGlow" (G PadIdleGlow))
  (Rendering|Material|SetVectorParameterValueonMaterials (Utilities|Array|Get(acopy) (G HangRings) I) "Col" (Math|Conversions|ToVector(LinearColor) nc)))

;;@ HangInit
(fn HangInit ()
  (S ShowSparks false)
  (Utilities|Array|Clear (G PadC))
  (Utilities|Array|Clear (G PadN))
  (Utilities|Array|Clear (G PadR))
  (Utilities|Array|Resize (G PadRel) (Utilities|Array|Length (G HangPads)))
  (Utilities|Array|Resize (G PadHeldPrev) (Utilities|Array|Length (G HangPads)))
  (Utilities|Array|Resize (G PadQuiet) (Utilities|Array|Length (G HangPads)))
  (for i (range (Utilities|Array|Length (G HangPads)))
    (CallFunction|PadLook :I i))
  (S HangReady true))

;;@ HangInitIf
(fn HangInitIf ()
  (if (not (G HangReady))
    (CallFunction|HangInit)))

;;@ RingRel
(fn RingRel (I Held Now)
  (if (not Held)
    (Utilities|Array|SetArrayElem (G PadRel) I Now)))

;;@ RingEdge
;; Cambio de sostenido: al soltar, el anillo arranca a expandirse desde ahi
(fn RingEdge (I Held Now)
  (if (!= Held (Utilities|Array|Get(acopy) (G PadHeldPrev) I))
    (Utilities|Array|SetArrayElem (G PadHeldPrev) I Held)
    (CallFunction|RingRel :I I :Held Held :Now Now)))

;;@ RingDraw
;; Golpe: el aro sale del borde del pad (0,5) hacia afuera (0,95) y se apaga en RingLife. Sostenido: queda en RingHoldR vibrando al ritmo de la nota
(fn RingDraw (I V Held Age Rel)
  (bind ring (Utilities|Array|Get(acopy) (G HangRings) I))
  (bind hz (CallFunction|NoteVibHz :I V))
  (bind t (Math|Float|Clamp(Float) (/ (Math|Float|Min(Float) Age Rel) (Math|Float|Max(Float) (G RingLife) 0.05)) 0.0 1.0))
  (bind e (* (- 1.0 t) (- 1.0 t)))
  (Rendering|SetVisibility ring (or Held (< t 1.0)) false)
  (Rendering|Material|SetScalarParameterValueonMaterials ring "Rad" (select Held (G RingHoldR) (+ 0.5 (* 0.45 (- 1.0 e)))))
  (Rendering|Material|SetScalarParameterValueonMaterials ring "Int" (select Held (G RingHoldGlow) (* (G RingGlow) e)))
  (Rendering|Material|SetScalarParameterValueonMaterials ring "Vib" (select Held (G RingVib) (* (G RingVib) 0.4)))
  (Rendering|Material|SetScalarParameterValueonMaterials ring "W" (G RingW))
  (Rendering|Material|SetScalarParameterValueonMaterials ring "Lobes" (G RingLobes))
  (Rendering|Material|SetScalarParameterValueonMaterials ring "Ph" (Math|Float|Fraction (* Age hz))))

;;@ PadDraw
;; El pad se hunde por SU eje (golpe: PadHitSink que vuelve en PadSinkTime; sostenido: PadHoldSink), destella con su nota y la ranura se enciende
(fn PadDraw (I V Held Age Rel)
  (bind pad (Utilities|Array|Get(acopy) (G HangPads) I))
  (bind hit (Math|Float|Exp (/ (neg Age) (Math|Float|Max(Float) (G PadSinkTime) 0.01))))
  (bind sink (Math|Float|Max(Float) (select Held (G PadHoldSink) 0.0) (* hit (G PadHitSink))))
  (Transformation|SetRelativeLocation :self pad :NewLocation (- (Utilities|Array|Get(acopy) (G PadLoc) I) (* (Utilities|Array|Get(acopy) (G PadUp) I) sink)) :bSweep false :bTeleport true)
  (bind lit (Math|Float|Max(Float) (select Held 0.6 0.0) hit))
  (Rendering|Material|SetScalarParameterValueonMaterials pad "Flash" (* (G PadFlash) lit))
  (Rendering|Material|SetScalarParameterValueonMaterials pad "GrooveGlow" (+ (G PadIdleGlow) (* (G PadHitGlow) lit)))
  (CallFunction|RingDraw :I I :V V :Held Held :Age Age :Rel Rel))

;;@ PadOne
;; Por cuadro y por pad. Un pad quieto (sin sostener, golpe viejo, anillo apagado) se dibuja una sola vez y despues se saltea
(fn PadOne (I DT)
  (bind v (Utilities|Array|Get(acopy) (G PadNote) I))
  (bind la (CallFunction|LatchAny :I v :K (Math|Integer|MakeLiteralInt -1)))
  (bind held (or (or (== v (- (G HeldR1) 1)) (== v (- (G HeldL1) 1))) la))
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (bind age (- now (Utilities|Array|Get(acopy) (G LastPluck) v)))
  (CallFunction|RingEdge :I I :Held held :Now now)
  (bind rel (- now (Utilities|Array|Get(acopy) (G PadRel) I)))
  (bind quiet (and (not held) (and (> age 1.0) (> rel (G RingLife)))))
  (if (or (not quiet) (not (Utilities|Array|Get(acopy) (G PadQuiet) I)))
    (Utilities|Array|SetArrayElem (G PadQuiet) I quiet)
    (CallFunction|PadDraw :I I :V v :Held held :Age age :Rel rel)))

;;@ PadTickOn
(fn PadTickOn (DT)
  (CallFunction|HangInitIf)
  (for i (range (Utilities|Array|Length (G HangPads)))
    (CallFunction|PadOne :I i :DT DT)))

;;@ PadTick
(fn PadTick (DT)
  (if (== (G InstrumentType) 1)
    (CallFunction|PadTickOn :DT DT)))

;;@ PadHitOne
;; Golpe: la cabeza del mando cruza, bajando, el plano a PadHitAbove sobre la cara del pad, dentro de su radio
(fn PadHitOne (I P0 P1 DT Right)
  (bind c (Utilities|Array|Get(acopy) (G PadC) I))
  (bind n (Utilities|Array|Get(acopy) (G PadN) I))
  (bind d0 (- (Math|Vector|DotProduct (- P0 c) n) (G PadTopH)))
  (bind d1 (- (Math|Vector|DotProduct (- P1 c) n) (G PadTopH)))
  (bind lat (Math|Vector|VectorLength (- (- P1 c) (* n (Math|Vector|DotProduct (- P1 c) n)))))
  (if (and (and (> d0 (G PadHitAbove)) (<= d1 (G PadHitAbove))) (and (< lat (+ (Utilities|Array|Get(acopy) (G PadR) I) (G PadSlop))) (> d1 (neg (G PadHoldBelow)))))
    (CallFunction|Pluck :I (Utilities|Array|Get(acopy) (G PadNote) I) :Speed (/ (- d0 d1) (Math|Float|Max(Float) DT 0.001)) :Right Right)))

;;@ PadNear
(fn PadNear (I P Extra)
  (if (Utilities|Array|IsValidIndex (G PadC) I)
    (bind c (Utilities|Array|Get(acopy) (G PadC) I))
    (bind n (Utilities|Array|Get(acopy) (G PadN) I))
    (bind d (- (Math|Vector|DotProduct (- P c) n) (G PadTopH)))
    (bind lat (Math|Vector|VectorLength (- (- P c) (* n (Math|Vector|DotProduct (- P c) n)))))
    (return (and (and (< d (+ (G PadHoldAbove) Extra)) (> d (neg (G PadHoldBelow)))) (< lat (+ (+ (Utilities|Array|Get(acopy) (G PadR) I) (G PadSlop)) Extra))))
    (else (return false))))

;;@ PadIndex
;; Pad bajo la mano para el sostenido: el que ya tiene la mano se mantiene con PadKeep de mas
(fn PadIndex (P Held)
  (bind keep (CallFunction|PadNear :I Held :P P :Extra (G PadKeep)))
  (if keep
    (return Held)
    (else
      (for i (range (Utilities|Array|Length (G PadC)))
        (bind near (CallFunction|PadNear :I i :P P :Extra (Math|Float|MakeLiteralFloat 0.0)))
        (if near (return i)))
      (return -1))))

;;@ PadOfVoice
(fn PadOfVoice (V)
  (for i (range (Utilities|Array|Length (G PadNote)))
    (if (== (Utilities|Array|Get(acopy) (G PadNote) i) V) (return i)))
  (return -1))

;;@ PadVoice
(fn PadVoice (P)
  (if (Utilities|Array|IsValidIndex (G PadNote) P)
    (return (Utilities|Array|Get(acopy) (G PadNote) P))
    (else (return -1))))

;;@ PadPress
;; Cuanto se hunde la mano bajo la cara del pad (cm): el sostenido lo usa como "altura" (mas hondo = mas brillo)
(fn PadPress (I P)
  (if (Utilities|Array|IsValidIndex (G PadC) I)
    (return (neg (- (Math|Vector|DotProduct (- P (Utilities|Array|Get(acopy) (G PadC) I)) (Utilities|Array|Get(acopy) (G PadN) I)) (G PadTopH))))
    (else (return 0.0))))

;;@ PadHold
;; Sostenido en el hang: la misma maquina que las cuerdas (HoldChange2 / HoldSustain3), con pads en vez de cuerdas
(fn PadHold (P0 P1 DT Right)
  (bind held (- (select Right (G HeldR1) (G HeldL1)) 1))
  (bind hp (CallFunction|PadOfVoice :V held))
  (bind cp (CallFunction|PadIndex :P P1 :Held hp))
  (bind cv (CallFunction|PadVoice :P cp))
  (bind z (CallFunction|PadPress :I cp :P P1))
  (if (!= cv held)
    (CallFunction|HoldChange2 :Old held :New cv :Speed (/ (Math|Vector|VectorLength (- P1 P0)) (Math|Float|Max(Float) DT 0.001)) :Right Right :Z z)
    (else (CallFunction|HoldSustain3 :I cv :Right Right :Z z))))

;;@ PadStep
(fn PadStep (P0 P1 DT Right)
  (if (== (Utilities|Array|Get(acopy) (G SndHold) (G SoundIndex)) 1)
    (CallFunction|PadHold :P0 P0 :P1 P1 :DT DT :Right Right)
    (else
      (for i (range (Utilities|Array|Length (G PadC)))
        (CallFunction|PadHitOne :I i :P0 P0 :P1 P1 :DT DT :Right Right)))))

;;@ DetectAll
;; (13a) reescrita: el hang tiene su propia deteccion
(fn DetectAll (P0 P1 DT Right Has)
  (if (== (G InstrumentType) 1)
    (CallFunction|PadStep :P0 P0 :P1 P1 :DT DT :Right Right)
    (else
      (if (== (Utilities|Array|Get(acopy) (G SndHold) (G SoundIndex)) 1)
        (CallFunction|HoldStep3 :P0 P0 :P1 P1 :DT DT :Right Right)
        (else (CallFunction|DetectStrum :P0 P0 :P1 P1 :DT DT :Right Right :Has Has))))))

;;@ DetectPoke2
;; (13a) reescrita: sin el detector de cuerdas en el hang
(fn DetectPoke2 (P0 P1 DT Right Has)
  (if (and (!= (G InstrumentType) 1) (!= (Utilities|Array|Get(acopy) (G SndHold) (G SoundIndex)) 1))
    (CallFunction|DetectPoke :P0 P0 :P1 P1 :DT DT :Right Right :Has Has)))

;;@ DebugHand
;; Mano de prueba: en el hang golpea los pads de a uno (baja y sube por el eje de cada pad, 0,9 s por pad); en el arpa barre las cuerdas como antes
(fn DebugHand (DT)
  (bind t (Utilities|Time|GetGameTimeinSeconds))
  (if (and (== (G InstrumentType) 1) (> (Utilities|Array|Length (G PadC)) 0))
    (bind n (Utilities|Array|Length (G PadC)))
    (bind q (Math|Float|Floor (/ t 0.9)))
    (bind k (- q (* n (/ q n))))
    (bind ph (- (/ t 0.9) (Math|Conversions|ToFloat(Integer) q)))
    (bind h (+ (G PadTopH) (* 3.0 (Math|Trig|Cos(Radians) (* ph 6.2831853)))))
    (CallFunction|HandStep :P (+ (Utilities|Array|Get(acopy) (G PadC) k) (* (Utilities|Array|Get(acopy) (G PadN) k) h)) :Right (Math|Boolean|MakeLiteralBool true) :DT DT)
    (else
      (bind span (+ (* (* (Math|Conversions|ToFloat(Integer) (- (G NumStrings) 1)) 0.5) (G Spacing)) 4.0))
      (CallFunction|HandStep :P (Math|Vector|MakeVector :X 0.0 :Y (* (Math|Trig|Sin(Radians) (* t 1.3)) span) :Z (* (G StringLen) 0.4)) :Right (Math|Boolean|MakeLiteralBool true) :DT DT))))

;;@ TickR
;; (13a) reescrita: la mano de prueba pasa a DebugHand (sirve para el arpa y el hang)
(fn TickR (DT)
  (if (G DebugStrum)
    (CallFunction|DebugHand :DT DT)
    (else
      (Utilities|IsValid (G HandR)
        (:"Is Valid"
          (CallFunction|HandStep :P (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform) (+ (Transformation|GetWorldLocation (G HandR)) (* (Transformation|GetForwardVector (G HandR)) (G TipFwd)))) :Right (Math|Boolean|MakeLiteralBool true) :DT DT))
        (:"Is Not Valid")))))

;; ---- 2026-10-28 (14a): perilla del ataque del pad (ficha -1009) + pads del hang con color ----

;;@ VoiceDef3
;; (14a) reescrita: ficha -1009 = PadAttack (perilla del ataque del pad, s)
(fn VoiceDef3 (D Period Fb Pan)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (CallFunction|MSSet :To (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)) :InName (Utilities|Array|Get(acopy) (G DIn) D) :Val (select (< v -1008.5) (G PadAttack) (select (< v -1007.5) (* f 1.0035) (select (< v -1006.5) (* f 0.9965) (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v)))))))))))

;;@ BuildPad
;; (14a) reescrita: el pad toma el color de su nota (x PadColorV), como los botones de color de la paleta de Drawing
;; Un pad (o el ding, I = 0) colgado del cuerpo en su transformada de Blender, y su anillo (plano aditivo) encima
(fn BuildPad (I)
  (bind r (Utilities|Array|Get(acopy) (G PadRad) I))
  (bind pad (AddComponent|Common|AddStaticMeshComponent :bManualAttachment true :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|AttachComponentToComponent :self pad :Parent (G HangBody))
  (Transformation|SetRelativeLocationAndRotation :self pad :NewLocation (Utilities|Array|Get(acopy) (G PadLoc) I) :NewRotation (Math|Rotator|MakeRotfromZ (Utilities|Array|Get(acopy) (G PadUp) I)) :bSweep false :bTeleport true)
  (Components|StaticMesh|SetStaticMesh pad (select (== I 0) (G HangDingMesh) (G HangPadMesh)))
  (Rendering|Material|SetMaterial pad 0 (G MatPadTop))
  (Rendering|Material|SetMaterial pad 1 (G MatPadSide))
  (bind nc (CallFunction|NoteColor :I (Utilities|Array|Get(acopy) (G PadNote) I)))
  (Rendering|Material|SetVectorParameterValueonMaterials pad "BaseColor" (* (Math|Conversions|ToVector(LinearColor) nc) (G PadColorV)))
  (Collision|SetCollisionEnabled pad "NoCollision")
  (Rendering|SetCastShadow pad false)
  (Utilities|Array|Add (G HangPads) pad)
  (bind ring (AddComponent|Common|AddStaticMeshComponent :bManualAttachment true :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
  (Transformation|AttachComponentToComponent :self ring :Parent pad)
  (bind s (/ (* r 4.0) 100.0))
  (Transformation|SetRelativeLocation :self ring :NewLocation (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (+ (G PadTopH) 0.12)) :bSweep false :bTeleport true)
  (Transformation|SetRelativeScale3D ring (Math|Vector|MakeVector :X s :Y s :Z s))
  (Components|StaticMesh|SetStaticMesh ring (G RingMesh))
  (Rendering|Material|SetMaterial ring 0 (G MatRing))
  (Collision|SetCollisionEnabled ring "NoCollision")
  (Rendering|SetCastShadow ring false)
  (Rendering|SetVisibility ring false false)
  (Utilities|Array|Add (G HangRings) ring))

;; ---- 2026-10-28 (15a): sonido 3 = HANG por SINTESIS MODAL (senos con caida propia por modo) + escala Re Kurd en el hang (HangSteps). Ficha de frecuencia generica: v <= -10000 -> f * ((-v - 10000) / 1000) ----

;;@ NoteMidi
;; (15a) reescrita: en el hang (InstrumentType 1) la escala es HangSteps (Re Kurd); en el arpa, ScaleSteps
(fn NoteMidi (I)
  (bind k (Math|Integer|Max(Integer) (Utilities|Array|Length (G ScaleSteps)) 1))
  (bind hk (Math|Integer|Max(Integer) (Utilities|Array|Length (G HangSteps)) 1))
  (bind sm (+ (+ (G RootNote) (Utilities|Array|Get(acopy) (G ScaleSteps) (- I (* k (/ I k))))) (* 12 (/ I k))))
  (bind hm (+ (+ (G RootNote) (Utilities|Array|Get(acopy) (G HangSteps) (- I (* hk (/ I hk))))) (* 12 (/ I hk))))
  (return (select (and (== (G InstrumentType) 1) (> (Utilities|Array|Length (G HangSteps)) 0)) hm sm)))

;;@ VoiceDef3
;; (15a) reescrita: + ficha generica de proporcion (v <= -10000: f * ((-v - 10000) / 1000)), para los modos del hang
(fn VoiceDef3 (D Period Fb Pan)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (CallFunction|MSSet :To (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)) :InName (Utilities|Array|Get(acopy) (G DIn) D) :Val (select (< v -9999.5) (* f (/ (- (neg v) 10000.0) 1000.0)) (select (< v -1008.5) (G PadAttack) (select (< v -1007.5) (* f 1.0035) (select (< v -1006.5) (* f 0.9965) (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v))))))))))))

;;@ VoiceFor
;; Una voz: su nota (NoteMidi: la escala del instrumento) -> periodo, feedback, pan
(fn VoiceFor (I N)
  (bind m (CallFunction|NoteMidi :I I))
  (bind f (* 440.0 (Math|Float|Power 2.0 (/ (- (Math|Conversions|ToFloat(Integer) m) 69.0) 12.0))))
  (CallFunction|BuildVoice3 :I I :Period (/ 1.0 f) :Fb (Math|Float|Exp (/ -6.9078 (* f (G Decay)))) :Pan (* (G PanWidth) (- (* 2.0 (/ (Math|Conversions|ToFloat(Integer) I) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- N 1)) 1.0))) 1.0)))
  (CallFunction|MixVoice :I I))

;;@ BuildBody
;; (15a) reescrita: las voces salen de VoiceFor (con NoteMidi); en el hang solo hay tantas como pads (9)
(fn BuildBody ()
  (bind n (select (== (G InstrumentType) 1) (Utilities|Array|Length (G PadLoc)) (G NumStrings)))
  (for i (range n)
    (CallFunction|VoiceFor :I i :N n))
  (CallFunction|BuildFX3)
  (CallFunction|DebugRecord)
  (Audio|MetaSound|Builder|Audition :self (G Builder) :AudioComponent (Variables|Default|GetSynth) :bLiveUpdatesEnabled false)
  (S Ready true)
  (Development|PrintString :InString (Utilities|String|Append :A "HARP synth ready, fails=" :B (Utilities|String|ToString(Integer) (G BuildFails)))))

;; ---- 2026-10-28 (16a): con cada golpe en el hang, una ESFERA con estela sale de su pad hacia el frente y se pierde a lo lejos ----

;;@ OrbEnsure
;; (16c) Reserva de OrbPool esferas + haces. El haz es un SplineMesh de la malla de la cuerda (48 anillos, eje Z) que sigue la curva del vuelo; en espacio de mundo (SetAbsolute)
;; sin adjuntar (bManualAttachment true): nace Static y adjuntarlo a la raiz Movable aborta con warning
(fn OrbEnsure ()
  (if (< (Utilities|Array|Length (G OrbComps)) (G OrbPool))
    (for k (range (- (G OrbPool) (Utilities|Array|Length (G OrbComps))))
      (bind o (AddComponent|Common|AddStaticMeshComponent :bManualAttachment false :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
      (Components|StaticMesh|SetStaticMesh o (G SparkMesh))
      (Rendering|Material|SetMaterial o 0 (G SparkMat))
      (Collision|SetCollisionEnabled o "NoCollision")
      (Rendering|SetCastShadow o false)
      (Rendering|SetVisibility o false false)
      (Utilities|Array|Add (G OrbComps) o)
      (bind bm (AddComponent|Rendering|AddSplineMeshComponent :bManualAttachment true :RelativeTransform (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))))
      (Transformation|SetMobility bm "Movable")
      (Transformation|SetAbsolute bm true true true)
      (Components|StaticMesh|SetStaticMesh bm (G StringMesh))
      (SplineMesh|SetForwardAxis bm "Z" false)
      (Rendering|Material|SetMaterial bm 0 (G SparkMat))
      (Collision|SetCollisionEnabled bm "NoCollision")
      (Rendering|SetCastShadow bm false)
      (Rendering|SetVisibility bm false false)
      (Utilities|Array|Add (G OrbBeams) bm)
      (Utilities|Array|Add (G OrbAge) 99.0)
      (Utilities|Array|Add (G OrbP0) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 0.0))
      (Utilities|Array|Add (G OrbDir) (Math|Vector|MakeVector :X 1.0 :Y 0.0 :Z 0.0))
      (Utilities|Array|Add (G OrbVel) 0.0)
      (Utilities|Array|Add (G OrbSeed) 0.0))))

;;@ OrbSlot
;; Siguiente esfera de la reserva (rota); devuelve la que toca usar
(fn OrbSlot ()
  (bind n (Math|Integer|Max(Integer) (Utilities|Array|Length (G OrbComps)) 1))
  (S OrbNext (- (+ (G OrbNext) 1) (* n (/ (+ (G OrbNext) 1) n))))
  (return (- (+ (G OrbNext) (- n 1)) (* n (/ (+ (G OrbNext) (- n 1)) n)))))

;;@ OrbPath
;; (18) Donde esta la esfera Slot a los Tm segundos. Sale con un IMPULSO del hang: arranca a OrbKick cm/s (segun la fuerza del golpe)
;; y frena en OrbDrag s hasta planear a OrbSpeed, con OrbAccel de fuga hacia lo lejos. Ondula apenas a los lados y arriba
;; (OrbWave cm a OrbWaveHz, la vertical a 1,37x y 0,6 de amplitud); la onda se abre en los primeros OrbWaveIn cm y crece hasta 2,5x lejos
(fn OrbPath (Slot Tm)
  (bind vv (Utilities|Array|Get(acopy) (G OrbVel) Slot))
  (bind sp (* (G OrbSpeed) (+ 0.7 (* 0.6 vv))))
  (bind tau (Math|Float|Max(Float) (G OrbDrag) 0.05))
  (bind kk (Math|Float|Max(Float) (- (* (G OrbKick) (+ 0.4 (* 0.6 vv))) sp) 0.0))
  ;; dist pasa por Max(Float) (tipado): si la suma promovible alimenta a (* fw dist) se vuelve VECTOR y la division de amp queda en (/ 0 ...) = onda nula
  (bind dist (Math|Float|Max(Float) (+ (+ (* sp Tm) (* (* 0.5 (G OrbAccel)) (* Tm Tm))) (* (* kk tau) (- 1.0 (Math|Float|Exp (/ (neg Tm) tau))))) -100000.0))
  (bind fw (Utilities|Array|Get(acopy) (G OrbDir) Slot))
  (bind sd (Math|Vector|Normalize (Math|Vector|CrossProduct fw (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z 1.0))))
  (bind upv (Math|Vector|CrossProduct sd fw))
  (bind phs (Utilities|Array|Get(acopy) (G OrbSeed) Slot))
  (bind wq (* 6.2832 (G OrbWaveHz)))
  (bind amp (* (G OrbWave) (Math|Float|Clamp(Float) (/ dist (Math|Float|Max(Float) (G OrbWaveIn) 1.0)) 0.0 2.5)))
  (bind a1 (* amp (Math|Trig|Sin(Radians) (+ (* wq Tm) phs))))
  (bind a2 (* (* amp 0.6) (Math|Trig|Sin(Radians) (+ (* (* wq 1.37) Tm) (* phs 2.1)))))
  (return (+ (+ (+ (Utilities|Array|Get(acopy) (G OrbP0) Slot) (* fw dist)) (* sd a1)) (* upv a2))))

;;@ OrbPlace
;; (18) La esfera recorre OrbPath; se enciende suave en OrbSoft s (smoothstep en brillo, y del 35 % al 100 % en tamano) y se apaga hacia el final (1 - k^2).
;; (19) El haz: ancho OrbTailW del de la punta en la cola (antes 0,08 fijo: cola de gusanito) y brillo OrbBeamI (antes 0,6 fijo).
;; El haz es la curva de los ultimos OrbTrail s del vuelo: Hermite entre la cola y la esfera, tangentes por diferencia de 0,04 s x el largo en tiempo
(fn OrbPlace (Slot)
  (bind tt (Utilities|Array|Get(acopy) (G OrbAge) Slot))
  (bind life (Math|Float|Max(Float) (G OrbLife) 0.1))
  (bind vv (Utilities|Array|Get(acopy) (G OrbVel) Slot))
  (bind ta (Math|Float|Max(Float) (- tt (G OrbTrail)) 0.0))
  (bind dk (* (- tt ta) 25.0))
  (bind hp (CallFunction|OrbPath :Slot Slot :Tm tt))
  (bind hp0 (CallFunction|OrbPath :Slot Slot :Tm (- tt 0.04)))
  (bind tp (CallFunction|OrbPath :Slot Slot :Tm ta))
  (bind tp1 (CallFunction|OrbPath :Slot Slot :Tm (+ ta 0.04)))
  (bind k (Math|Float|Clamp(Float) (/ tt life) 0.0 1.0))
  (bind fade (- 1.0 (* k k)))
  (bind s0 (Math|Float|Clamp(Float) (/ tt (Math|Float|Max(Float) (G OrbSoft) 0.01)) 0.0 1.0))
  (bind pop (* (* s0 s0) (- 3.0 (* 2.0 s0))))
  (bind sz (* (* (* (G OrbSize) 0.01) (+ 0.6 (* 0.6 vv))) (+ 0.35 (* 0.65 pop))))
  (bind rw (* (* sz 50.0) (G OrbBeamW)))
  (bind orb (Utilities|Array|Get(acopy) (G OrbComps) Slot))
  (bind bm (Utilities|Array|Get(acopy) (G OrbBeams) Slot))
  (Rendering|SetVisibility orb (< tt life) false)
  (Rendering|SetVisibility bm (and (< tt life) (> (- tt ta) 0.03)) false)
  (Transformation|SetWorldLocation :self orb :NewLocation hp :bSweep false :bTeleport true)
  (Transformation|SetWorldScale3D orb (Math|Vector|MakeVector :X sz :Y sz :Z sz))
  (Rendering|Material|SetScalarParameterValueonMaterials orb "Fade" (* fade pop))
  (SplineMesh|SetStartScale bm (Math|Vector2D|MakeVector2D :X (* rw (G OrbTailW)) :Y (* rw (G OrbTailW))) false)
  (SplineMesh|SetEndScale bm (Math|Vector2D|MakeVector2D :X rw :Y rw) false)
  (SplineMesh|SetStartandEnd bm tp (* (- tp1 tp) dk) hp (* (- hp hp0) dk) true)
  (Rendering|Material|SetScalarParameterValueonMaterials bm "Fade" (* (* fade (G OrbBeamI)) pop)))

;;@ OrbLaunch
;; (19) Nace DEBAJO del hang, bajo SU pad (PadLoc en el espacio del cuerpo, OrbBelow cm bajo la base; HangLoc/HangRot), asi la zona donde se toca queda libre.
;; Corre OrbAhead por la linea de vuelo: hacia el frente del instrumento, abriendose segun el lado del pad (OrbSpread) y subiendo (OrbRise).
;; El haz lleva el degradado a lo largo (Along = OrbAlong en el material: brilla en la punta y se apaga hacia la cola).
;; Semilla de la onda al azar; esfera con cuerpo (OrbCore, OrbRim, OrbGlow) y haz de nucleo suave sin vibracion.
;; Color = color de la nota AL CUADRADO (satura el pastel de NoteColor; con el aditivo salia blanco)
(fn OrbLaunch (I V Vel)
  (CallFunction|OrbEnsure)
  (bind s (CallFunction|OrbSlot))
  (bind c (Utilities|Array|Get(acopy) (G PadC) I))
  (bind nc (CallFunction|NoteColor :I V))
  (bind hz (CallFunction|NoteVibHz :I V))
  (bind cv (Math|Conversions|ToVector(LinearColor) nc))
  (bind orb (Utilities|Array|Get(acopy) (G OrbComps) s))
  (bind bm (Utilities|Array|Get(acopy) (G OrbBeams) s))
  (bind dw (Math|Transform|TransformDirection (Transformation|GetActorTransform) (Math|Vector|Normalize (Math|Vector|MakeVector :X 1.0 :Y (* (.y c) (G OrbSpread)) :Z (G OrbRise)))))
  (bind pl (Utilities|Array|Get(acopy) (G PadLoc) I))
  (bind hl (Math|Transform|TransformLocation (Math|Transform|MakeTransform :Location (G HangLoc) :Rotation (G HangRot)) (Math|Vector|MakeVector :X (.x pl) :Y (.y pl) :Z (neg (G OrbBelow)))))
  (Utilities|Array|SetArrayElem (G OrbP0) s (+ (Math|Transform|TransformLocation (Transformation|GetActorTransform) hl) (* dw (G OrbAhead))))
  (Utilities|Array|SetArrayElem (G OrbDir) s dw)
  (Utilities|Array|SetArrayElem (G OrbVel) s Vel)
  (Utilities|Array|SetArrayElem (G OrbSeed) s (* (Math|Random|RandomFloat) 6.2832))
  (Utilities|Array|SetArrayElem (G OrbAge) s 0.0)
  (Rendering|Material|SetVectorParameterValueonMaterials orb "Color" (* cv cv))
  (Rendering|Material|SetVectorParameterValueonMaterials bm "Color" (* cv cv))
  (Rendering|Material|SetScalarParameterValueonMaterials orb "VibAmp" (G OrbVib))
  (Rendering|Material|SetScalarParameterValueonMaterials orb "VibHz" hz)
  (Rendering|Material|SetScalarParameterValueonMaterials bm "VibAmp" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials orb "Glow" (G OrbGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials bm "Glow" (G OrbGlow))
  (Rendering|Material|SetScalarParameterValueonMaterials orb "Core" (G OrbCore))
  (Rendering|Material|SetScalarParameterValueonMaterials bm "Core" 1.5)
  (Rendering|Material|SetScalarParameterValueonMaterials orb "Rim" (G OrbRim))
  (Rendering|Material|SetScalarParameterValueonMaterials bm "Rim" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials bm "Along" (G OrbAlong))
  (CallFunction|OrbPlace :Slot s))

;;@ OrbCheck
;; Golpe nuevo en el pad I (LastPluck de su voz mas nuevo que lo visto) -> lanza una esfera con la fuerza del golpe
(fn OrbCheck (I V LP)
  (Utilities|Array|Resize (G PadSeen) (Math|Integer|Max(Integer) (Utilities|Array|Length (G PadSeen)) (Utilities|Array|Length (G HangPads))))
  (if (and (G ShowOrbs) (> LP (Utilities|Array|Get(acopy) (G PadSeen) I)))
    (Utilities|Array|SetArrayElem (G PadSeen) I LP)
    (CallFunction|OrbLaunch :I I :V V :Vel (Utilities|Array|Get(acopy) (G Energy) V))))

;;@ OrbOne
(fn OrbOne (Slot DT)
  (if (< (Utilities|Array|Get(acopy) (G OrbAge) Slot) (G OrbLife))
    (Utilities|Array|SetArrayElem (G OrbAge) Slot (+ (Utilities|Array|Get(acopy) (G OrbAge) Slot) DT))
    (CallFunction|OrbPlace :Slot Slot)))

;;@ OrbTick
(fn OrbTick (DT)
  (for i (range (Utilities|Array|Length (G OrbComps)))
    (CallFunction|OrbOne :Slot i :DT DT)))

;;@ PadTickOn
;; (16a) reescrita: + OrbTick
(fn PadTickOn (DT)
  (CallFunction|HangInitIf)
  (for i (range (Utilities|Array|Length (G HangPads)))
    (CallFunction|PadOne :I i :DT DT))
  (CallFunction|OrbTick :DT DT))

;;@ PadOne
;; (16a) reescrita: + OrbCheck (la esfera que sale con cada golpe)
(fn PadOne (I DT)
  (bind v (Utilities|Array|Get(acopy) (G PadNote) I))
  (bind la (CallFunction|LatchAny :I v :K (Math|Integer|MakeLiteralInt -1)))
  (bind held (or (or (== v (- (G HeldR1) 1)) (== v (- (G HeldL1) 1))) la))
  (bind now (Utilities|Time|GetGameTimeinSeconds))
  (bind age (- now (Utilities|Array|Get(acopy) (G LastPluck) v)))
  (CallFunction|RingEdge :I I :Held held :Now now)
  (CallFunction|OrbCheck :I I :V v :LP (Utilities|Array|Get(acopy) (G LastPluck) v))
  (bind rel (- now (Utilities|Array|Get(acopy) (G PadRel) I)))
  (bind quiet (and (not held) (and (> age 1.0) (> rel (G RingLife)))))
  (if (or (not quiet) (not (Utilities|Array|Get(acopy) (G PadQuiet) I)))
    (Utilities|Array|SetArrayElem (G PadQuiet) I quiet)
    (CallFunction|PadDraw :I I :V v :Held held :Age age :Rel rel)))

;; ---- 2026-10-28 (17a): sonido 3 = HANG por RESONADORES. Cada golpe = un clic seco (Trigger Counter -> audio -> paso alto) + un poco de ruido, filtrado por la fuerza (Cut) y x Vel^2 / Vel^3;
;; los modos son Biquad pasa-banda (caida exponencial real, el golpe nuevo suma energia, la cola no salta con la fuerza del golpe siguiente). Datos y fuentes: docs/INVESTIGACION-SONIDO-HANG-2026-10-28.md ----

;;@ MSSetI
;; (17a) como MSSet, con literal entero: para los pines enum (Type del Biquad: 2 = Band Pass)
(fn MSSetI (To InName Val)
  (bind (dtp lit) (Audio|MetaSound|Builder|CreateMetaSoundIntLiteral :self (EngineSubsystems|GetMetaSoundBuilderSubsystem) :Value Val))
  (bind ih (Audio|MetaSound|Builder|FindNodeInputbyName :self (G Builder) :NodeHandle To :InputName InName)
    (:Succeeded
      (Audio|MetaSound|Builder|SetNodeInputDefault :self (G Builder) :NodeInputHandle ih :Literal lit
        (:Succeeded)
        (:Failed (CallFunction|Fail :What InName))))
    (:Failed (CallFunction|Fail :What InName))))

;;@ VoiceDef4
;; (17a) VoiceDef3 + la voz (I) + fichas de los resonadores:
;;   -1100-k        -> literal entero k (enum)
;;   -1010          -> peso del ding: 1 en la voz 0, HangBodyOther en las demas
;;   -300000-100*Hz -> frecuencia absoluta (Hz); se recuerda en SynLastHz
;;   -200000-1000*T -> ancho de banda (octavas) para caer 60 dB en T s sobre SynLastHz, x (220/f)^HangT60Tilt (las agudas caen antes)
;;   -10000-1000*r  -> f * r; se recuerda en SynLastHz
(fn VoiceDef4 (D Period Fb Pan I)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (bind nd (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)))
  (bind nm (Utilities|Array|Get(acopy) (G DIn) D))
  (if (and (< v -1099.5) (> v -1199.5))
    (CallFunction|MSSetI :To nd :InName nm :Val (Math|Float|Round (- (neg v) 1100.0)))
    (else
      (bind hz (select (< v -299999.5) (/ (- (neg v) 300000.0) 100.0) (* f (/ (- (neg v) 10000.0) 1000.0))))
      (if (< v -299999.5) (S SynLastHz hz))
      (if (and (< v -9999.5) (> v -199999.5)) (S SynLastHz hz))
      (bind t60 (* (/ (- (neg v) 200000.0) 1000.0) (Math|Float|Clamp(Float) (Math|Float|Power (/ 220.0 f) (G HangT60Tilt)) 0.6 1.6)))
      (bind bw (/ 3.174 (* (Math|Float|Max(Float) t60 0.005) (Math|Float|Max(Float) (G SynLastHz) 1.0))))
      (CallFunction|MSSet :To nd :InName nm :Val (select (< v -299999.5) hz (select (< v -199999.5) bw (select (< v -9999.5) hz (select (< v -1009.5) (select (== I 0) 1.0 (G HangBodyOther)) (select (< v -1008.5) (G PadAttack) (select (< v -1007.5) (* f 1.0035) (select (< v -1006.5) (* f 0.9965) (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v)))))))))))))))))

;;@ BuildVoice4
;; (17a) BuildVoice3 que le pasa la voz (I) a VoiceDef4
(fn BuildVoice4 (I Period Fb Pan)
  (bind snd (G SoundIndex))
  (bind hp (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G PluckN) I) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (bind hv (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G VelN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 0.5)))
  (bind hc (CallFunction|MSInput :Nm (Utilities|Array|Get(acopy) (G CutN) I) :Trig (Math|Boolean|MakeLiteralBool false) :Def (Math|Float|MakeLiteralFloat 4000.0)))
  (bind hr (CallFunction|MSInput :Nm (Utilities|String|StringToName (Utilities|String|Append :A "Rel_" :B (Utilities|String|ToString(Integer) I))) :Trig (Math|Boolean|MakeLiteralBool true) :Def (Math|Float|MakeLiteralFloat 0.0)))
  (Utilities|Array|Clear (G Handles))
  (for k (range (Utilities|Array|Length (G VName)))
    (if (== (Utilities|Array|Get(acopy) (G VSnd) k) snd)
      (bind h (CallFunction|MSNode :NS (Utilities|Array|Get(acopy) (G VNS) k) :N (Utilities|Array|Get(acopy) (G VName) k) :Var (Utilities|Array|Get(acopy) (G VVar) k)))
      (Utilities|Array|Add (G Handles) h)))
  (for j (range (Utilities|Array|Length (G LFrom)))
    (if (== (Utilities|Array|Get(acopy) (G LSnd) j) snd)
      (CallFunction|VoiceLink2 :J j :HP hp :HV hv :HC hc :HR hr)))
  (for d (range (Utilities|Array|Length (G DNode)))
    (if (== (Utilities|Array|Get(acopy) (G DSnd) d) snd)
      (CallFunction|VoiceDef4 :D d :Period Period :Fb Fb :Pan Pan :I I))))

;;@ VoiceFor
;; (17a) reescrita: arma la voz con BuildVoice4 (fichas de los resonadores)
(fn VoiceFor (I N)
  (bind m (CallFunction|NoteMidi :I I))
  (bind f (* 440.0 (Math|Float|Power 2.0 (/ (- (Math|Conversions|ToFloat(Integer) m) 69.0) 12.0))))
  (CallFunction|BuildVoice4 :I I :Period (/ 1.0 f) :Fb (Math|Float|Exp (/ -6.9078 (* f (G Decay)))) :Pan (* (G PanWidth) (- (* 2.0 (/ (Math|Conversions|ToFloat(Integer) I) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- N 1)) 1.0))) 1.0)))
  (CallFunction|MixVoice :I I))

;;@ MSNode
;; (17a) reescrita: el Biquad Filter de MetaSounds es version mayor 2 (los demas nodos que usamos, 1)
(fn MSNode (NS N Var)
  (bind h (Audio|MetaSound|Builder|AddMetaSoundNodeByClassName :self (G Builder) :ClassName (Utilities|Struct|MakeMetaSoundClassName :Namespace NS :Name N :Variant Var) :MajorVersion (select (Utilities|String|EqualExactly(String) :A (Utilities|String|ToString(Name) N) :B "Biquad Filter") 2 1))
    (:Succeeded (return h))
    (:Failed (CallFunction|Fail :What N) (return h))))

;;@ VoiceDef4
;; (17b) reescrita: + fichas de ganancia con perillas (para afinar de oido en 4-Hang; se aplican al armar el sinte):
;;   -400000-10*g -> g x HangDecay (la amplitud no cambia al alargar la caida)
;;   -500000-10*g -> g x HangDecay x HangMetal (inarmonicos)
;;   -600000-10*g -> g x HangDecay x HangShimmer (gemelas del batido)
;;   -300000-100*Hz -> frecuencia absoluta (Hz); se recuerda en SynLastHz
;;   -200000-1000*T -> ancho de banda (octavas) para caer 60 dB en T x HangDecay s sobre SynLastHz, x (220/f)^HangT60Tilt (las agudas caen antes)
;;   -10000-1000*r  -> f * r; se recuerda en SynLastHz
;;   -1100-k -> literal entero k (enum) · -1010 -> peso del ding (1 en la voz 0, HangBodyOther en las demas)
(fn VoiceDef4 (D Period Fb Pan I)
  (bind v (Utilities|Array|Get(acopy) (G DVal) D))
  (bind f (/ 1.0 Period))
  (bind nd (Utilities|Array|Get(acopy) (G Handles) (Utilities|Array|Get(acopy) (G DNode) D)))
  (bind nm (Utilities|Array|Get(acopy) (G DIn) D))
  (if (and (< v -1099.5) (> v -1199.5))
    (CallFunction|MSSetI :To nd :InName nm :Val (Math|Float|Round (- (neg v) 1100.0)))
    (else
      (bind hz (select (< v -299999.5) (/ (- (neg v) 300000.0) 100.0) (* f (/ (- (neg v) 10000.0) 1000.0))))
      (if (and (< v -299999.5) (> v -399999.5)) (S SynLastHz hz))
      (if (and (< v -9999.5) (> v -199999.5)) (S SynLastHz hz))
      (bind t60 (* (* (/ (- (neg v) 200000.0) 1000.0) (Math|Float|Clamp(Float) (Math|Float|Power (/ 220.0 f) (G HangT60Tilt)) 0.6 1.6)) (G HangDecay)))
      (bind bw (/ 3.174 (* (Math|Float|Max(Float) t60 0.005) (Math|Float|Max(Float) (G SynLastHz) 1.0))))
      (bind gk (select (< v -599999.5) (G HangShimmer) (select (< v -499999.5) (G HangMetal) 1.0)))
      (bind gv (* (* (/ (- (neg v) (select (< v -599999.5) 600000.0 (select (< v -499999.5) 500000.0 400000.0))) 10.0) gk) (G HangDecay)))
      (CallFunction|MSSet :To nd :InName nm :Val (select (< v -399999.5) gv (select (< v -299999.5) hz (select (< v -199999.5) bw (select (< v -9999.5) hz (select (< v -1009.5) (select (== I 0) 1.0 (G HangBodyOther)) (select (< v -1008.5) (G PadAttack) (select (< v -1007.5) (* f 1.0035) (select (< v -1006.5) (* f 0.9965) (select (< v -1005.5) (* f 1.004) (select (< v -1004.5) (* f 0.5) (select (< v -1003.5) f (select (< v -1002.5) Pan (select (< v -1001.5) Fb (select (< v -1000.5) (- Period 0.0000208) v))))))))))))))))))
