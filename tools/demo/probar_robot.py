"""probar_robot.py - prueba el robot (receptor) sin visor, con un emisor simulado, y resume los logs.

  python tools/demo/probar_robot.py --emisor juego          # un proceso del juego forzado a emitir (-MirrorRole=1): prueba el codigo del EMISOR
  python tools/demo/probar_robot.py --emisor guion          # tools/demo/mirror_test_send.py (cabeza, laser, clics, nivel)
  python tools/demo/probar_robot.py --emisor guion --guion sesion_draw   # otra escena de mirror_test_send.py
  python tools/demo/probar_robot.py --robot editor          # el receptor corre con el editor en -game (sin recocinar) en vez del .exe empaquetado

Muestra las lineas MIRROR/DEMO/ENSAYO de cada proceso, cuenta errores de Blueprint y cierra todo al final.
"""
import argparse, os, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
EDITOR = os.environ.get("UE_EDITOR", r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")
ROBOT = os.path.join(ROOT, "VR_Test", "Saved", "Packaged", "Win64_Robot", "VR_Test.exe")
OUT = os.path.join(ROOT, "VR_Test", "Saved", "Smoke")
MENU = "/Game/SoulCharger/Demo/Maps/L_Demo_Menu"
ERR = re.compile(r"Accessed None|Blueprint Runtime Error|Infinite loop|LogScript: Error|Attempted to access", re.I)
VER = re.compile(r"LogBlueprintUserMessages: \[(\w+)\] ((MIRROR|DEMO|ENSAYO|BREATHSTAGE|BREATH:|TB:|RIG: Results).*)")

def esperar(path, texto, seg):
    t0 = time.time()
    while time.time() - t0 < seg:
        if os.path.exists(path) and texto in open(path, encoding="utf-8", errors="ignore").read():
            return True
        time.sleep(0.5)
    return False

def resumen(nombre, path, filtro=None):
    if not os.path.exists(path):
        print("== %s: SIN LOG (%s)" % (nombre, path)); return 1
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    print("== %s" % nombre)
    for l in lines:
        m = VER.search(l)
        if m and (not filtro or re.search(filtro, m.group(2))):
            print("  %s %s" % (l[1:24], m.group(2)[:150]))
    errs = [l for l in lines if ERR.search(l)]
    print("  errores de Blueprint: %d" % len(errs))
    for e in errs[:6]:
        print("    " + e.strip()[:220])
    return len(errs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emisor", choices=["juego", "guion", "ninguno"], default="guion")
    ap.add_argument("--guion", default="menu", help="escena de mirror_test_send.py")
    ap.add_argument("--robot", choices=["exe", "editor"], default="exe")
    ap.add_argument("--segundos", type=float, default=40)
    ap.add_argument("--retardo", type=float, default=4)
    ap.add_argument("--filtro", default=None, help="regex sobre las lineas a mostrar")
    ap.add_argument("--extra", default="", help="argumentos extra para mirror_test_send.py, ej. \"--yaw-respira 90\"")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    tag = time.strftime("%H%M%S")
    rlog = os.path.join(OUT, "robot_%s.log" % tag)
    slog = os.path.join(OUT, "emisor_%s.log" % tag)
    procs = []
    subprocess.call(["taskkill", "/IM", "VR_Test.exe", "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if a.robot == "exe":
            cmd = [ROBOT, "-nohmd", "-unattended", "-MirrorRole=2", "-windowed", "-ResX=640", "-ResY=360", "-FeatureLevelES31", "-MirrorMyIP=127.0.0.1", "-abslog=" + rlog]
        else:
            cmd = [EDITOR, UPROJECT, MENU, "-game", "-nohmd", "-MirrorRole=2", "-windowed", "-ResX=640", "-ResY=360", "-unattended", "-nosplash", "-MirrorMyIP=127.0.0.1", "-abslog=" + rlog]
        procs.append(subprocess.Popen(cmd))
        if not esperar(rlog, "receptor escuchando", 90):
            print("el robot no llego a escuchar")
        if a.emisor == "juego":
            procs.append(subprocess.Popen([EDITOR, UPROJECT, MENU, "-game", "-nohmd", "-MirrorRole=1", "-MirrorIP=127.0.0.1", "-windowed",
                                           "-ResX=640", "-ResY=360", "-unattended", "-nosplash", "-abslog=" + slog]))
            esperar(slog, "MIRROR: emisor", 90)
            time.sleep(a.segundos)
        elif a.emisor == "guion":
            subprocess.call([sys.executable, os.path.join(ROOT, "tools", "demo", "mirror_test_send.py"), "--guion", a.guion,
                             "--segundos", str(a.segundos), "--retardo", str(a.retardo)] + a.extra.split())
            time.sleep(6)
        else:
            time.sleep(a.segundos)
    finally:
        # el .exe empaquetado es un lanzador que abre otro proceso: se cierra el arbol entero, y por las dudas por nombre
        for p in procs:
            subprocess.call(["taskkill", "/PID", str(p.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill", "/IM", "VR_Test.exe", "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    n = resumen("robot", rlog, a.filtro)
    if a.emisor == "juego":
        n += resumen("emisor", slog, a.filtro)
    sys.exit(1 if n else 0)

if __name__ == "__main__":
    main()
