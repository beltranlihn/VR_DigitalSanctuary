"""empaquetar_obra.py - arma el APK de la Obra (Quest 3, Development) y lo copia a Recursos.

  python tools/unreal/empaquetar_obra.py                 # paquete com.almadigital.soulcharger  "Soul Charger"
  python tools/unreal/empaquetar_obra.py --variante v2   # paquete com.almadigital.soulchargerv2 "Soul Charger V2" (convive con el otro)

Antes de empaquetar:
  1. Guardar todo en el editor (Ctrl+Shift+S). Mientras cocina, NO guardar assets.
  2. Correr la prueba de humo: python tools/unreal/smoke_obra.py  (tiene que dar OK).
  3. Revisar el checklist de build de publico en docs/GUIA-DE-DIRECCION.md (bSimulated, DebugStart, Speed...).
Cocina SOLO la Obra y sus 6 celdas (las mismas que lista DefaultGame.ini). Archivo en
VR_Test/Saved/Packaged/Android_Obra[V2]; copia en Recursos/Soul Charger - Escritorio 2026-10/APK/<nombre> <fecha>.
Para instalar en el visor: tools/unreal/instalar_quest.ps1 [-Variante v2].
"""
import argparse, glob, os, re, shutil, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
ENGINE = os.environ.get("UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")
INI = os.path.join(ROOT, "VR_Test", "Config", "DefaultEngine.ini")
USERINI = os.path.join(ROOT, "VR_Test", "Saved", "Config", "WindowsEditor", "EditorPerProjectUserSettings.ini")
MAPS = ["/Game/SoulCharger/Obra/L_SoulCharger_Obra", "/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath", "/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart", "/Game/SoulCharger/Mechanics/Mind/Maps/Test_Mind",
        "/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer", "/Game/SoulCharger/Mechanics/Draw/Maps/Test_Draw", "/Game/SoulCharger/Hall/Maps/Test_Hall"]
VARIANTES = {"obra": ("com.almadigital.soulcharger", "Soul Charger", "Android_Obra"),
             "v2": ("com.almadigital.soulchargerv2", "Soul Charger V2", "Android_ObraV2")}

def fix_mcp_autostart():
    # el cocinado arranca con bAutoStartServer=False para no pelear el puerto 8000 con el editor; si esa
    # config queda guardada, el editor deja de levantar el servidor MCP la proxima vez que abre.
    if not os.path.exists(USERINI):
        return
    s = open(USERINI, encoding="utf-8", errors="surrogateescape").read()
    h = "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]\n"
    if h in s and "bAutoStartServer=False" in s:
        s = s.replace("bAutoStartServer=False", "bAutoStartServer=True")
        open(USERINI, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("config del MCP restaurada (bAutoStartServer=True)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variante", choices=sorted(VARIANTES), default="obra")
    ap.add_argument("--sin-copia", action="store_true")
    a = ap.parse_args()
    pkg, nombre, carpeta = VARIANTES[a.variante]
    arch = os.path.join(ROOT, "VR_Test", "Saved", "Packaged", carpeta)
    ini0 = open(INI, encoding="utf-8").read()
    ini = re.sub(r"^PackageName=.*$", "PackageName=" + pkg, ini0, flags=re.M)
    ini = re.sub(r"^ApplicationDisplayName=.*$", "ApplicationDisplayName=" + nombre, ini, flags=re.M)
    ini = re.sub(r"^GameDefaultMap=.*$", "GameDefaultMap=/Game/SoulCharger/Obra/L_SoulCharger_Obra.L_SoulCharger_Obra", ini, flags=re.M)
    shutil.rmtree(arch, ignore_errors=True)
    log = os.path.join(ROOT, "VR_Test", "Saved", "Logs", "empaquetar_%s_%s.log" % (a.variante, time.strftime("%Y%m%d-%H%M%S")))
    cmd = [os.path.join(ENGINE, "Engine", "Build", "BatchFiles", "RunUAT.bat"), "BuildCookRun",
           "-project=" + UPROJECT, "-unrealexe=" + os.path.join(ENGINE, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe"),
           "-platform=Android", "-cookflavor=ASTC", "-clientconfig=Development", "-cook", "-map=" + "+".join(MAPS),
           "-skipbuildeditor", "-nocompileeditor",
           "-AdditionalCookerOptions=-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False",
           "-build", "-stage", "-pak", "-iostore", "-compressed", "-package", "-archive", "-archivedirectory=" + arch,
           "-prereqs", "-utf8output", "-nop4"]
    t0 = time.time()
    print("cocinando %s (%s)... log: %s" % (nombre, pkg, log), flush=True)
    try:
        if ini != ini0:
            open(INI, "w", encoding="utf-8").write(ini)
        with open(log, "w", encoding="utf-8", errors="ignore") as f:
            rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    finally:
        open(INI, "w", encoding="utf-8").write(ini0)
        fix_mcp_autostart()
        import mcp_config; mcp_config.asegurar_autostart()
    print("UAT termino con codigo %d en %d min" % (rc, (time.time() - t0) / 60))
    apks = sorted(glob.glob(os.path.join(arch, "**", "*.apk"), recursive=True), key=os.path.getmtime)
    if not apks:
        print("NO hay APK. Ultimas lineas del log:")
        print("\n".join(open(log, encoding="utf-8", errors="ignore").read().splitlines()[-25:]))
        sys.exit(1)
    apk = apks[-1]
    print("APK: %s (%.0f MB)" % (apk, os.path.getsize(apk) / 1e6))
    # rc 1 con APK presente = la regla del proyecto: 'Cook failed' por logs Error: que no rompen (ver memoria packaging-cook-exit-code)
    if not a.sin_copia:
        dest = os.path.join(ROOT, "Recursos", "Soul Charger - Escritorio 2026-10", "APK", "%s APK %s" % (nombre, time.strftime("%Y-%m-%d %H%M")))
        shutil.copytree(os.path.dirname(apk), dest)
        print("copia: " + dest)

if __name__ == "__main__":
    main()
