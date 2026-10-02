"""probar_nivel.py - corre un nivel en modo juego (sin visor) durante N segundos y resume su log.

Sirve para probar una mecanica en su nivel de test (Test_Entering, Test_Heart, Test_Fluid,
Test_Sequencer, L_TBTest_SC, Test_Hall...) sin ponerse el visor y sin abrir el editor:
el ensayo (BP_StageRunner_SC) corre la etapa con los tiempos de la Partitura.

  python tools/unreal/probar_nivel.py Test_Entering
  python tools/unreal/probar_nivel.py Test_Heart --segundos 120 --filtro "ENSAYO|HEART"
  (nombres cortos: Test_Entering, Test_Heart, Test_Fluid, Test_Sequencer, L_TBTest_SC, Test_Hall; o la ruta /Game/... completa)

Muestra las lineas que coinciden con --filtro (por defecto las del ensayo y las etapas) y cuenta los
errores de Blueprint (Accessed None, Script Msg...). Sale con 1 si hubo errores.
Se puede correr con el editor abierto (es otro proceso).
"""
import argparse, os, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
EDITOR = os.environ.get("UE_EDITOR", r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")
OUTDIR = os.path.join(ROOT, "VR_Test", "Saved", "Smoke")
ERR = re.compile(r"Accessed None|Blueprint Runtime Error|Infinite loop|LogScript: Error|LogScript: Warning: Script Msg|Attempted to access|pending kill", re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapa", help="ruta del nivel, p. ej. /Game/Test_Entering")
    ap.add_argument("--segundos", type=int, default=150)
    ap.add_argument("--filtro", default=r"ENSAYO|BREATH|HEART|LOVING|SEQ:|TB:|HALL|OBRA")
    a = ap.parse_args()
    m = a.mapa.replace("\\", "/")
    if "/Game/" in m and not m.startswith("/Game/"):
        m = m[m.index("/Game/"):]          # Git Bash convierte /Game/X en C:/Program Files/Git/Game/X
    if not m.startswith("/Game/"):
        m = {"Test_Hall": "/Game/SoulCharger/Mechanics/Hall/Test_Hall", "L_TBTest_SC": "/Game/NeuralCanvas/Maps/L_TBTest_SC"}.get(m, "/Game/" + m.lstrip("/"))
    a.mapa = m
    os.makedirs(OUTDIR, exist_ok=True)
    tag = time.strftime("%Y%m%d-%H%M%S")
    logp = os.path.join(OUTDIR, "nivel_%s_%s.log" % (a.mapa.strip("/").replace("/", "_"), tag))
    cmd = [EDITOR, UPROJECT, a.mapa, "-game", "-nohmd", "-windowed", "-ResX=960", "-ResY=540",
           "-log", "-abslog=" + logp, "-nosplash", "-unattended"]
    print("lanzando %s por %d s..." % (a.mapa, a.segundos), flush=True)
    p = subprocess.Popen(cmd)
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < a.segundos:
        time.sleep(2)
    if p.poll() is None:
        p.kill()
    time.sleep(1)
    lines = open(logp, encoding="utf-8", errors="ignore").read().splitlines()
    filt = re.compile(a.filtro)
    shown = [l for l in lines if "LogBlueprintUserMessages" in l and filt.search(l)]
    errs = [l for l in lines if ERR.search(l)]
    for l in shown[:200]:
        print("  " + l.split("LogBlueprintUserMessages: ")[-1][:200])
    print("errores de Blueprint: %d" % len(errs))
    for e in errs[:10]:
        print("    " + e.strip()[:240])
    print("log: " + logp)
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()
