import re, json, sys, os
# gen_focus_dsl.py - copia de gen_harp_dsl.py para BP_FocusDirector_SC (3.a vuelta 2026-10-29). Expande (G X)/(S X v) con la categoria de cada variable.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
CATS = {
 '1-Foco': 'Cells HoldTime FadeBack GazeDeg GazeOut StartDelay RevealDelay RevealTime RevealGap HintDelay',
 '2-Ameba': 'SleepState AwakeState SleepScale SleepDim SleepMix SleepTint BloomTime BloomScale BloomLight DriftAmp DriftHz DriftSleep WanderRot HintLight HintHz SleepAgit AwakeAgit ChargeAgit ChargePulse ChargePulseHz AwakeLife ChargeLife AwakeCurl ChargeCurl LifeSteps ExciteSpeed',
 '3-Punto': 'DotAngle DotIdle DotColor DotOpacity DotIdleOpacity DotMat DotMesh',
 '4-Final': 'FinaleHold',
 '5-Sonido': 'RevealSound ChargeSound LockSound FinaleSound SfxVol HapticEffect',
 '6-Mundo': 'Fluid FluidCalm FluidActive EnvHue EnvSat EnvBright EnvSpeed',
 '7-Particulas': 'MoteSystem MoteRate MoteLife MoteSize MoteRadius MoteNoise MotePull MoteRelease MoteAlpha MoteFade',
 '9-Prueba': 'DebugTarget bDebugAuto',
 'Z-Estado': 'Charge Locked Reveal RevealAt LockAt LightP Excite MoteF MoteOn Motes Home HomeRot BaseSc BaseLife BasePulse WF WP OrigCol DotComp ChargeAC Target GBest GBestDot Clock PhaseT Phase NoLook DotD DotRing LockedN HintI ChargeOn LightSum RevSnd EnvBase EnvP EnvShown EnvH EnvS EnvB bStageDone',
}
CAT = {}
for c, names in CATS.items():
    for n in names.split():
        key = n[1:] if (n.startswith('b') and n[1:2].isupper()) else n
        if key in CAT: sys.exit('collision ' + key)
        CAT[key] = c
src = open('focus_src.dsl', encoding='utf-8').read()
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
json.dump(out, open('focus_dsl.json', 'w', encoding='utf-8'), indent=1)
print(len(out), 'graphs:', ', '.join(out.keys()))
