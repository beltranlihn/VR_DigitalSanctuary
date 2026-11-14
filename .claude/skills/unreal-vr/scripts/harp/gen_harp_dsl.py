import re, json, sys
CATS = {
 '0-Arpa': 'InstrumentType NumStrings Spacing StringLen LenTaper StringRadius bDebugStrum bRecordWav',
 '1-Sonido': 'RootNote ScaleSteps Decay PanWidth DelayTime DelayFeedback DelayWet ReverbWet ReverbDecay Volume MasterGainDb ChorusRate ChorusDelay ChorusDepth SoundIndex SndChorus SndHold PadCutBase PadOctPerCm PadCutMin PadCutMax PadAttack',
 '2-Luz': 'BaseColor RightColor LeftColor Glow VibAmp VibDecay WobbleHz StringMat StringMesh bShowSparks SparkSize SparkGrow SparkLife SparkPool SparkMesh SparkMat HoldGlow HoldSparkAge LitGlow LitSat LitThick LightDecay HoldLight NoteColorMix NoteHueStart NoteHueRange NoteSat SparkVibHz SparkVibOct SparkVibAmp SparkLift HaloGlow HaloSwell HaloSpeed HaloWidth HaloGap HaloReach',
 '3-Toque': 'TipFwd PlaneTol HitHalfWidth VelFull Cooldown HapticScale HapticEffect QCtrlLocR QCtrlRotR QCtrlLocL QCtrlRotL QCtrlScale HeadLocal bHideHands HoldWidth bTriggerLatch IMCRight IMCLeft SnapCatch SnapHold SnapSide bGripLatch',
 '4-Hang': 'HangDecay HangMetal HangShimmer HangT60Tilt HangBodyOther OrbGlow OrbWave OrbWaveHz OrbWaveIn OrbCore OrbRim OrbBeamW OrbKick OrbDrag OrbAhead OrbSoft OrbBelow OrbTailW OrbAlong OrbBeamI bShowOrbs OrbPool OrbSize OrbLift OrbSpeed OrbAccel OrbLife OrbRise OrbSpread OrbTrail OrbVib HangSteps PadColorV HangLoc HangRot PadHitAbove PadSlop PadHoldAbove PadHoldBelow PadKeep PadTopH PadHitSink PadHoldSink PadSinkTime PadFlash PadIdleGlow PadHitGlow RingLife RingGlow RingHoldR RingHoldGlow RingVib RingW RingLobes PadLoc PadUp PadRad PadNote HangBodyMesh HangPadMesh HangDingMesh RingMesh MatHangBody MatHangPocket MatHangGroove MatPadTop MatPadSide MatRing',
 '9-Sinte': 'VNS VName VVar LFrom LOut LTo LIn DNode DIn DVal VSnd LSnd DSnd',
 'Z-Estado': 'Strings MIDs Energy LastPluck PluckN VelN CutN Builder Handles VoiceL VoiceR SumL SumR AudioOuts HandR HandL PrevR PrevL bReady BuildFails bHasR bHasL QCtrlR QCtrlL bHandsHidden SparkComps SparkAge SparkNext HeldR1 HeldL1 HoldZ0R HoldZ0L HoldSparkR HoldSparkL LastSpark bInputReady bTrigR bTrigL LatchR1 LatchL1 LatchComps Light LightSeen Latch1 bGripR bGripL HaloT0 HaloT1 HaloOn PadC PadN PadR bHangReady PadRel PadHeldPrev PadQuiet HangBody HangPads HangRings OrbComps OrbBeams OrbSeed OrbAge OrbP0 OrbDir OrbVel OrbNext PadSeen SynLastHz',
}
CAT = {}
for c, names in CATS.items():
    for n in names.split():
        key = n[1:] if (n.startswith('b') and n[1:2].isupper()) else n
        if key in CAT: sys.exit('collision ' + key)
        CAT[key] = c
src = open('harp_src.dsl', encoding='utf-8').read()
blocks = {}
cur = None
for line in src.splitlines():
    m = re.match(r';;@\s*(\S+)', line)
    if m:
        cur = m.group(1); blocks[cur] = []; continue
    if line.strip().startswith(';;') or cur is None: continue
    blocks[cur].append(line)
def expand(code):
    def g(m):
        n = m.group(1)
        if n not in CAT: raise SystemExit('unknown var ' + n)
        return '(Variables|%s|Get%s)' % (CAT[n], n)
    def s(m):
        n = m.group(1)
        if n not in CAT: raise SystemExit('unknown var ' + n)
        return '(Variables|%s|Set%s ' % (CAT[n], n)
    code = re.sub(r'\(G ([A-Za-z0-9]+)\)', g, code)
    code = re.sub(r'\(S ([A-Za-z0-9]+) ', s, code)
    return code
out = {k: expand('\n'.join(v).strip()) for k, v in blocks.items()}
for k, v in out.items():
    if v.count('(') != v.count(')'): sys.exit('paren mismatch in ' + k)
    if '(G ' in v or '(S ' in v: sys.exit('unexpanded in ' + k)
json.dump(out, open('harp_dsl.json', 'w', encoding='utf-8'), indent=1)
print(len(out), 'graphs:', ', '.join(out.keys()))
