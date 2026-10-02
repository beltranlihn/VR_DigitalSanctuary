"""probar_nivel.py - corre un nivel en modo juego (sin visor) durante N segundos y resume su log.

Sirve para probar una mecanica en su nivel de test (Test_Breath, Test_Heart, Test_Mind,
Test_Sequencer, Test_Draw, Test_Hall...) sin ponerse el visor y sin abrir el editor:
el ensayo (BP_StageRunner_SC) corre la etapa con los tiempos de la Partitura.

  python tools/unreal/probar_nivel.py Test_Breath
  python tools/unreal/probar_nivel.py Test_Heart --segundos 120 --filtro "ENSAYO|HEART"
  (nombres cortos: Test_Breath, Test_Heart, Test_Mind, Test_Sequencer, Test_Draw, Test_Hall y los demas Test_* de Shared; o la ruta /Game/... completa)

Muestra las lineas que coinciden con --filtro (por defecto las del ensayo y las etapas) y cuenta los
errores de Blueprint (Accessed None, Script Msg...). Sale con 1 si hubo errores.
Se puede correr con el editor abierto (es otro proceso).
"""
import argparse, os, re, subprocess, sys, time

_M = "/Game/SoulCharger/Mechanics/"
CORTOS = {"Test_Breath": _M + "Breath/Maps/Test_Breath", "Test_Heart": _M + "Heart/Maps/Test_Heart",
          "Test_Mind": _M + "Mind/Maps/Test_Mind", "Test_Sequencer": _M + "Sequencer/Maps/Test_Sequencer",
          "Test_Draw": _M + "Draw/Maps/Test_Draw", "Test_DrawPalette": _M + "Draw/Maps/Test_DrawPalette",
          "Test_Hall": "/Game/SoulCharger/Hall/Maps/Test_Hall", "Obra": "/Game/SoulCharger/Obra/L_SoulCharger_Obra",
          "Test_Results": "/Game/SoulCharger/Shared/Results/Maps/Test_Results",
          "Test_Appear": "/Game/SoulCharger/Shared/Appear/Test_Appear",
          "Test_QuestCtrl": "/Game/SoulCharger/Shared/QuestController/Test_QuestCtrl",
          # nombres de antes del 2026-10-02
          "Test_Entering": _M + "Breath/Maps/Test_Breath", "Test_Fluid": _M + "Mind/Maps/Test_Mind",
          "L_TBTest_SC": _M + "Draw/Maps/Test_Draw"}

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
EDITOR = os.environ.get("UE_EDITOR", r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")
OUTDIR = os.path.join(ROOT, "VR_Test", "Saved", "Smoke")
ERR = re.compile(r"Accessed None|Blueprint Runtime Error|Infinite loop|LogScript: Error|LogScript: Warning: Script Msg|Attempted to access|pending kill", re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapa", help="nombre corto (Test_Breath) o ruta del nivel")
    ap.add_argument("--segundos", type=int, default=150)
    ap.add_argument("--filtro", default=r"ENSAYO|BREATH|HEART|LOVING|SEQ:|TB:|HALL|OBRA")
    a = ap.parse_args()
    m = a.mapa.replace("\\", "/")
    if "/Game/" in m and not m.startswith("/Game/"):
        m = m[m.index("/Game/"):]          # Git Bash convierte /Game/X en C:/Program Files/Git/Game/X
    if not m.startswith("/Game/"):
        m = CORTOS.get(m, "/Game/" + m.lstrip("/"))
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
    import mcp_config; mcp_config.asegurar_autostart()
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()
