"""grabar_pasada.py (tools/demo, 2026-10-23) <tag> <mapa> <regex_fin> [--exec "cmd1,cmd2"] [--max 600] [--extra 3]
Corre el robot cocinado SIN ventana y SIN sonido (-RenderOffscreen -nosound), a 15 fps fijos (-benchmark -fps=15) y
guardando cada cuadro (-dumpmovie). Corta cuando el log muestra regex_fin (+extra s). Deja los cuadros en rec_<tag>/ y el
log en rec_<tag>.log. Los cuadros se numeran igual que el contador de cuadros del log (0 = primer cuadro)."""
import argparse, glob, os, re, shutil, subprocess, sys, time

ROOT = r"C:\Users\beltr\Desktop\Alma Digital Studio\Projects\VR Unreal\VR_Test\Saved\Packaged\Win64_Robot"
EXE = os.path.join(ROOT, 'VR_Test.exe')
SS = os.path.join(ROOT, 'VR_Test', 'Saved', 'Screenshots', 'Windows')
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'clips')  # cuadros y logs (no se versionan)
os.makedirs(SP, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tag'); ap.add_argument('mapa'); ap.add_argument('fin')
    ap.add_argument('--exec', dest='ex', default='')
    ap.add_argument('--max', type=float, default=600)
    ap.add_argument('--extra', type=float, default=3)
    a = ap.parse_args()
    shutil.rmtree(SS, ignore_errors=True)
    log = os.path.join(SP, 'rec_%s.log' % a.tag)
    if os.path.exists(log):
        os.remove(log)
    m = a.mapa if a.mapa.startswith('/Game/') else '/Game/SoulCharger/Demo/Maps/' + a.mapa
    cmd = [EXE, m, '-nohmd', '-RenderOffscreen', '-nosound', '-ResX=960', '-ResY=540', '-MirrorRole=-1', '-FeatureLevelES31',
           '-benchmark', '-fps=15', '-dumpmovie', '-abslog=' + log] + (['-ExecCmds=' + a.ex] if a.ex else [])
    p = subprocess.Popen(cmd)
    t0 = time.time(); hit = None
    fin = re.compile(a.fin)
    while time.time() - t0 < a.max and p.poll() is None:
        time.sleep(1)
        if os.path.exists(log):
            txt = open(log, encoding='utf-8', errors='ignore').read()
            if fin.search(txt):
                hit = time.time(); break
    if hit:
        time.sleep(a.extra)
    subprocess.run(['powershell', '-NoProfile', '-Command', "Get-Process VR_Test -ErrorAction SilentlyContinue | Stop-Process"])
    time.sleep(2)
    dst = os.path.join(SP, 'rec_' + a.tag)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.move(SS, dst)
    n = len(glob.glob(os.path.join(dst, '*.png')))
    print('%s: %d cuadros (%.0f s de juego) en %.0f s; fin %s' % (a.tag, n, n / 15.0, time.time() - t0, 'OK' if hit else 'NO LLEGO'))


if __name__ == '__main__':
    main()
