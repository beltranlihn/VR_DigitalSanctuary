"""smoke_obra.py - prueba de humo de la Obra entera, sin visor y sin Claude.

Lanza L_SoulCharger_Obra en modo juego (-game, sin visor) con:
  -ObraSmoke      sin aviso, datos simulados, arranque normal, y se cierra sola al terminar
  -ObraSpeed=N    acelera el reloj del director (las mecanicas corren en tiempo real)
Lee el log mientras corre, comprueba que las marcas del recorrido aparezcan EN ORDEN y que
no haya errores de Blueprint. Sale con codigo 0 si todo paso, 1 si algo fallo.

Uso:
  python tools/unreal/smoke_obra.py                 # Speed 4, tope 30 min
  python tools/unreal/smoke_obra.py --speed 6 --timeout 1500
  python tools/unreal/smoke_obra.py --log ruta.log  # solo analiza un log ya escrito

Se puede correr con el editor abierto (es otro proceso). Cuando cambies algo en
BP_Obra_SC, en la Partitura o en una etapa: guarda, corre esto, y recien despues empaqueta.
Reporte en VR_Test/Saved/Smoke/smoke_<fecha>.json (y el log al lado).
"""
import argparse, json, os, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
EDITOR = os.environ.get("UE_EDITOR", r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")
MAP = "/Game/SoulCharger/Obra/L_SoulCharger_Obra"
OUTDIR = os.path.join(ROOT, "VR_Test", "Saved", "Smoke")

# Marcas que tienen que aparecer, en este orden. (nombre legible, regex sobre la linea del log)
def expected():
    m = [("modo humo", r"OBRA SMOKE: modo prueba de humo"),
         ("config", r"OBRA CONFIG: Speed="),
         ("Hall: inicio", r"OBRA: Hall - inicio"),
         ("Hall: HallIntro", r"OBRA: Hall - HallIntro"),
         ("Hall: salida a las etapas", r"OBRA: Hall - salida a las etapas")]
    names = ["Entering", "Recognizing", "Loving", "Attracting", "Surrounding"]
    for k, n in enumerate(names):
        m += [(n + ": entra Alma", r"OBRA SMOKE: fase 4 etapa %d\b" % k),
              (n + ": StageIntro", r"OBRA: StageIntro"),
              (n + ": StageBegin", r"OBRA: StageBegin"),
              (n + ": StageOutro", r"OBRA: StageOutro, por fin propio = "),
              (n + ": carga", r"OBRA: carga de la etapa %d\b" % k)]
    m += [("final: regreso al Hall", r"OBRA: regreso al Hall"),
          ("final: resultados", r"OBRA SMOKE: fase 12 "),
          ("final: salida del Hall", r"OBRA SMOKE: fase 13 "),
          ("final: creditos", r"OBRA SMOKE: fase 14 "),
          ("final: fundido", r"OBRA: fundido final"),
          ("fin", r"OBRA SMOKE: FIN OK")]
    return m

ERR = re.compile(r"Accessed None|Blueprint Runtime Error|Infinite loop|LogScript: Error|LogScript: Warning: Script Msg|Attempted to access|pending kill", re.I)
TS = re.compile(r"^\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d):(\d{3})\]")

def stamp(line):
    m = TS.match(line)
    if not m:
        return None
    t = time.strptime(m.group(1), "%Y.%m.%d-%H.%M.%S")
    return time.mktime(t) + int(m.group(2)) / 1000.0

def analyze(lines):
    exp = expected(); i = 0; hits = []; errors = []; outro = []; t0 = None
    for line in lines:
        s = stamp(line)
        if s and t0 is None and "OBRA" in line:
            t0 = s
        if ERR.search(line):
            errors.append(line.strip()[:300])
        if "por fin propio" in line:
            outro.append(line.strip().split("OBRA: ")[-1])
        if i < len(exp) and re.search(exp[i][1], line):
            hits.append((exp[i][0], round((s - t0) if (s and t0) else -1, 1)))
            i += 1
    missing = [e[0] for e in exp[i:]]
    return {"ok": not missing and not errors, "hits": hits, "missing": missing,
            "errors": errors[:40], "n_errors": len(errors), "outros": outro}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=4.0)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--log", default=None, help="analizar un log existente en vez de lanzar")
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    tag = time.strftime("%Y%m%d-%H%M%S")
    if a.log:
        logp = a.log
    else:
        logp = os.path.join(OUTDIR, "smoke_%s.log" % tag)
        cmd = [EDITOR, UPROJECT, MAP, "-game", "-nohmd", "-windowed", "-ResX=960", "-ResY=540",
               "-ObraSmoke", "-ObraSpeed=%g" % a.speed, "-log", "-abslog=" + logp, "-nosplash",
               "-unattended"]
        # 🔴 NO pasar -ini:EditorPerProjectUserSettings:...bAutoStartServer=False: el proceso -game GUARDA esa
        # config al salir y el editor deja de arrancar el servidor MCP (paso el 2026-10-02).
        print("lanzando la Obra (Speed %g, tope %d s)..." % (a.speed, a.timeout), flush=True)
        p = subprocess.Popen(cmd)
        t_start = time.time(); seen = 0
        while p.poll() is None:
            time.sleep(5)
            if os.path.exists(logp):
                with open(logp, encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                n = txt.count("OBRA SMOKE: fase")
                if n != seen:
                    last = [l for l in txt.splitlines() if "OBRA SMOKE: fase" in l][-1].split("OBRA SMOKE: ")[-1]
                    print("  %4d s  %s" % (time.time() - t_start, last), flush=True)
                    seen = n
            if time.time() - t_start > a.timeout:
                print("TOPE de tiempo: se corta el proceso", flush=True)
                p.kill()
                break
    with open(logp, encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    r = analyze(lines)
    r["log"] = logp
    rep = os.path.join(OUTDIR, "smoke_%s.json" % tag)
    with open(rep, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1, ensure_ascii=False)
    print("\n== PRUEBA DE HUMO: %s ==" % ("OK" if r["ok"] else "FALLO"))
    for name, t in r["hits"]:
        print("  %7.1f s  %s" % (t, name))
    if r["missing"]:
        print("  FALTAN (en orden): " + ", ".join(r["missing"][:8]) + (" ..." if len(r["missing"]) > 8 else ""))
    for o in r["outros"]:
        print("  " + o)
    print("  errores de Blueprint: %d" % r["n_errors"])
    for e in r["errors"][:10]:
        print("    " + e)
    print("reporte: " + rep)
    sys.exit(0 if r["ok"] else 1)

if __name__ == "__main__":
    main()
