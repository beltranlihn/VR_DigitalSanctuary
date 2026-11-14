# patch_v2.py (2026-10-30) - 2.a vuelta de Test_Thoughts sobre thoughts_src.dsl: salida linda (respira, se suelta en polvo
# desde su superficie, palabra que sube y se disuelve, los demas escalonados) y carga suave de la ameba (cascada + energia).
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
s = open('thoughts_src.dsl', encoding='utf-8').read()


def block(name):
    i = s.index(';;@ ' + name + '\n')
    j = s.find(';;@ ', i + 5)
    return i, (j if j >= 0 else len(s))


def replace(name, new):
    global s
    i, j = block(name)
    s = s[:i] + new.rstrip('\n') + '\n\n' + s[j:]


def sub(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, 1)


# TdBoot: FlyAt; sin LastFeedAt
sub("    (Utilities|Array|Add (G FeedAt) -1.0)\n", "    (Utilities|Array|Add (G FeedAt) -1.0)\n    (Utilities|Array|Add (G FlyAt) -1.0)\n")
sub("  (S MainRevealAt -1.0)\n  (S LastFeedAt -1.0)\n", "  (S MainRevealAt -1.0)\n")

# TdThought: el titulo en la salida
sub("""  (bind to (select (== st 3) (Math|Float|Clamp(Float) (/ (- (G Clock) (Utilities|Array|Get(acopy) (G ConsumeAt) I)) (Math|Float|Max(Float) (G TitleOutTime) 0.1))) 0.0))
  (Rendering|SetVisibility tc (and (> rv 0.005) (< to 1.0)) false)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Reveal" rv)""",
    """  (bind rt (- (G Clock) (Utilities|Array|Get(acopy) (G ConsumeAt) I)))
  (bind rvt (select (and (== st 3) (>= rt 0.0)) (Math|Float|Max(Float) rv (Math|Float|Clamp(Float) (/ rt 0.4))) rv))
  (bind to (select (== st 3) (Math|Float|Clamp(Float) (/ (- rt (G Burst)) (Math|Float|Max(Float) (G TitleOutTime) 0.1))) 0.0))
  (Rendering|SetVisibility tc (and (> rvt 0.005) (< to 1.0)) false)
  (Rendering|Material|SetScalarParameterValueonMaterials tc "Reveal" rvt)""")
sub("""    (elif (and (== st 0) (and (G FormOn) (and (>= (Utilities|Array|Get(acopy) (G NextAt) I) 0.0) (>= (G Clock) (Utilities|Array|Get(acopy) (G NextAt) I)))))
      (CallFunction|TdForm :I I))))""",
    """    (elif (and (== st 0) (and (G FormOn) (and (>= (Utilities|Array|Get(acopy) (G NextAt) I) 0.0) (>= (G Clock) (Utilities|Array|Get(acopy) (G NextAt) I)))))
      (CallFunction|TdForm :I I)
      (elif (and (== st 3) (> to 0.0))
        (Transformation|SetWorldLocation tc (+ (Utilities|Array|Get(acopy) (G SlotLoc) (Math|Integer|Max(Integer) (Utilities|Array|Get(acopy) (G SlotOf) I) 0)) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (- (* (G TitleRise) (* (* to to) (- 3.0 (* 2.0 to)))) (G TitleDrop)))))))))""")
sub(";; despues de mirarlo: le quedan ReleaseLife s (soltar = dejarlo ir).",
    ";; despues de mirarlo: le quedan ReleaseLife s (soltar = dejarlo ir). Hecho polvo: su palabra emerge al soltarse (0,4 s), se\n;; va con el barrido despues de Burst (TitleOutTime) y sube TitleRise cm mientras se disuelve.")

replace('TdChoose', """;;@ TdChoose
;; I es el pensamiento elegido: se cierra la eleccion y no se forman mas; su palabra va a quedar bajo la ameba (ChosenComp,
;; ChosenDrop cm, ChosenScale); suena VO_23b ("Let us gather all these thoughts..."). El se suelta ya; los demas vivos lo
;; siguen escalonados (GatherDelay + k GatherGap s): todos se vuelven polvo y confluyen en la ameba. Vibran los mandos.
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
  (CallFunction|TdConsume :I I :At (G Clock))
  (S GatherK 0)
  (for j (range (Utilities|Array|Length (G Thoughts)))
    (if (and (!= j I) (== (Utilities|Array|Get(acopy) (G TState) j) 1))
      (S GatherK (+ (G GatherK) 1))
      (CallFunction|TdConsume :I j :At (+ (G Clock) (+ (G GatherDelay) (* (Math|Conversions|ToFloat(Integer) (- (G GatherK) 1)) (G GatherGap)))))))
  (bind pc (Game|GetPlayerController 0))
  (Utilities|IsValid pc
    (:"Is Valid"
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Left")
      (Game|Feedback|PlayHapticEffect :self pc :HapticEffect (G HapticEffect) :Hand "Right"))))
""")

replace('TdConsume', """;;@ TdConsume
;; El pensamiento I queda para hacerse polvo a la hora At (TdFly lo suelta): deja de ser mirable y de juntar su nube.
(fn TdConsume (I At)
  (Utilities|Array|SetArrayElem (G TState) I 3 true)
  (Utilities|Array|SetArrayElem (G ConsumeAt) I At true)
  (Utilities|Array|SetArrayElem (G FlyState) I 0 true)
  (Utilities|Array|SetArrayElem (G MoteOn) I false true))
""")

replace('TdFly', """;;@ TdFly
;; La salida y el vuelo del pensamiento I (FlyState):
;;   0 espera su hora (ConsumeAt) -> 1 SE SUELTA: nace polvo de su color en su superficie (BurstRadius) que la ameba ya atrae
;;     (Push FlyPush); durante Burst s respira: crece BurstGrow y enciende el borde BurstGlow (smoothstep)
;;   -> 2 se disuelve (Disappear en ShrinkTime s) y el emisor viaja a la ameba (smoothstep, arco FlyArc) a FlySpeed cm/s
;;   -> llega en FeedAt: deja de nacer y le suma FeedKick a la carga de la ameba (BloomE, sin saltos); si es el elegido,
;;      la ameba se llena (bChosenIn) y suena FeedSound -> 3 mueren las ultimas (FlyTime s) -> 4 se apaga la nube.
;; (Pull NO sirve para viajar: es radial desde el propio emisor, gotcha 631.)
(fn TdFly (I)
  (bind p (Utilities|Array|Get(acopy) (G Thoughts) I))
  (bind st (Utilities|Array|Get(acopy) (G FlyState) I))
  (bind rt (- (G Clock) (Utilities|Array|Get(acopy) (G ConsumeAt) I)))
  (bind m (Utilities|Array|Get(acopy) (G Motes) I))
  (bind sl (Transformation|GetActorLocation :self p))
  (if (and (== st 0) (>= rt 0.0))
    (Utilities|Array|SetArrayElem (G FlyState) I 1 true)
    (Niagara|SetNiagaraVariable(Position) m "Target" (G MainHome))
    (Niagara|SetNiagaraVariable(Float) m "Push" (G FlyPush))
    (Niagara|SetNiagaraVariable(Float) m "Pull" 0.0)
    (Niagara|SetNiagaraVariable(Float) m "Radius" (G BurstRadius))
    (Niagara|SetNiagaraVariable(Float) m "Noise" (G FlyNoise))
    (Niagara|SetNiagaraVariable(Float) m "Life" (Math|Float|Max(Float) (G FlyTime) 0.2))
    (Niagara|SetNiagaraVariable(Float) m "SpawnRate" (G FlyRate))
    (Niagara|SetNiagaraVariable(Float) m "Fade" 1.0)
    (Niagara|SetNiagaraVariable(LinearColor) m "OrbColor" (Math|Color|NewOpacity(LinearColor) (Utilities|Array|Get(acopy) (G CCol) I) (G MoteAlpha)))
    (Niagara|SetNiagaraVariable(Float) m "SizeMin" (G MoteSize))
    (Niagara|SetNiagaraVariable(Float) m "SizeMax" (* 2.0 (G MoteSize)))
    (Transformation|SetWorldLocation m sl)
    (Components|Activation|Activate m false)
    (elif (== st 1)
      (bind b (Math|Float|Clamp(Float) (/ rt (Math|Float|Max(Float) (G Burst) 0.05))))
      (bind sb (* (* b b) (- 3.0 (* 2.0 b))))
      (Class|BPProtoSoulSC|SetSize :self p :Size (* (Utilities|Array|Get(acopy) (G BaseSize) I) (+ 1.0 (* (G BurstGrow) sb))))
      (Class|BPProtoSoulSC|SetEdgeIntensity :self p :EdgeIntensity (* (Utilities|Array|Get(acopy) (G BaseEdge) I) (+ 1.0 (* (G BurstGlow) sb))))
      (if (>= rt (G Burst))
        (Class|BPProtoSoulSC|SetDisappearTime :self p :DisappearTime (G ShrinkTime))
        (Class|BPProtoSoulSC|Disappear :self p)
        (Utilities|Array|SetArrayElem (G FlyAt) I (G Clock) true)
        (Utilities|Array|SetArrayElem (G FeedAt) I (+ (G Clock) (Math|Float|Max(Float) (/ (Math|Vector|Distance(Vector) sl (G MainHome)) (Math|Float|Max(Float) (G FlySpeed) 10.0)) 0.3)) true)
        (Utilities|Array|SetArrayElem (G FlyState) I 2 true))
      (elif (== st 2)
        (bind f0 (Utilities|Array|Get(acopy) (G FlyAt) I))
        (bind t (Math|Float|Clamp(Float) (/ (- (G Clock) f0) (Math|Float|Max(Float) (- (Utilities|Array|Get(acopy) (G FeedAt) I) f0) 0.1))))
        (Transformation|SetWorldLocation m (+ (Math|Vector|Lerp(Vector) sl (G MainHome) (* (* t t) (- 3.0 (* 2.0 t)))) (Math|Vector|MakeVector :X 0.0 :Y 0.0 :Z (* (G FlyArc) (Math|Trig|Sin(Radians) (* 3.1415927 t))))))
        (if (>= t 1.0)
          (Niagara|SetNiagaraVariable(Float) m "SpawnRate" 0.0)
          (Utilities|Array|SetArrayElem (G FlyState) I 3 true)
          (S BloomE (Math|Float|Min(Float) (+ (G BloomE) (G FeedKick)) 1.5))
          (if (== I (G Chosen))
            (S ChosenIn true)
            (S ChosenInAt (G Clock))
            (CallFunction|TdSound :Snd (G FeedSound) :Vol (G SfxVol))))
        (elif (and (== st 3) (>= (G Clock) (+ (Utilities|Array|Get(acopy) (G FeedAt) I) (+ (G FlyTime) 0.4))))
          (Utilities|Array|SetArrayElem (G FlyState) I 4 true)
          (Components|Activation|Deactivate m))))))
""")

# TdMain: carga suave (cascada) y destello por energia
sub("""      (S CellE (Math|Interpolation|FInterpTo :Current (G CellE) :Target (select (G ChosenIn) 1.0 (* (G AttnMax) (Math|Float|Clamp(Float) (/ (G AttnSum) (Math|Float|Max(Float) (G AttnFull) 1.0))))) :DeltaTime Dt :InterpSpeed (G FeedSpeed)))""",
    """      (S CellV (Math|Interpolation|FInterpTo :Current (G CellV) :Target (select (G ChosenIn) 1.0 (* (G AttnMax) (Math|Float|Clamp(Float) (/ (G AttnSum) (Math|Float|Max(Float) (G AttnFull) 1.0))))) :DeltaTime Dt :InterpSpeed (G FeedSpeed)))
      (S CellE (Math|Interpolation|FInterpTo :Current (G CellE) :Target (G CellV) :DeltaTime Dt :InterpSpeed (G FeedSpeed)))
      (S BloomE (Math|Interpolation|FInterpTo :Current (G BloomE) :Target 0.0 :DeltaTime Dt :InterpSpeed (/ 1.0 (Math|Float|Max(Float) (G BloomTime) 0.1))))
      (S BloomV (Math|Interpolation|FInterpTo :Current (G BloomV) :Target (G BloomE) :DeltaTime Dt :InterpSpeed (G BloomRise)))""")
sub("""      (bind bt (select (< (G LastFeedAt) 0.0) 99.0 (- (G Clock) (G LastFeedAt))))
      (bind bk (Math|Float|Clamp(Float) (/ bt (Math|Float|Max(Float) (G BloomTime) 0.1))))
      (bind bl (* (* (- 1.0 bk) (- 1.0 bk)) (Math|Float|Clamp(Float) (/ bt 0.15))))""",
    """      (bind bl (G BloomV))""")
sub(";; La ameba: CellE va hacia lo que hay que mostrar (FeedSpeed): la atencion",
    ";; La ameba: CellE sigue a CellV, que sigue a lo que hay que mostrar (dos FInterpTo en cascada a FeedSpeed: arranca y\n;; frena suave, sin saltos): la atencion")
sub(";; SleepState a AwakeState y su Agitation de SleepAgit a AwakeAgit. Cada polvo que llega es un destello (bl, BloomTime s):",
    ";; SleepState a AwakeState y su Agitation de SleepAgit a AwakeAgit. Cada polvo que llega le suma FeedKick a una carga\n;; (BloomE) que se descarga en BloomTime s; el destello bl = BloomV la sigue suave (BloomRise), sin reiniciarse de golpe:")
open('thoughts_src.dsl', 'w', encoding='utf-8').write(s)
print('LastFeedAt left:', 'LastFeedAt' in s, '| BloomV:', s.count('BloomV'))
