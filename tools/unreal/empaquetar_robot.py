"""empaquetar_robot.py - arma el ROBOT: la demo en Windows (Win64, Development) que recibe por OSC lo que hace el visor.

  python tools/unreal/empaquetar_robot.py              # renderer movil (se ve como el Quest)
  python tools/unreal/empaquetar_robot.py --escritorio # renderer de escritorio (SM6), sin el formato movil
  python tools/unreal/empaquetar_robot.py --en-seco    # muestra comando y cambios al ini, no cocina

Es el MISMO contenido que el APK de la demo (L_Demo_Menu, L_Demo_Breath, L_Demo_Draw, L_Demo_Heart). En cada nivel, BP_MirrorLink_SC decide
su rol solo: con visor emite (el Quest), sin visor recibe (este .exe) y mueve la camara y los mandos del VR Pawn con lo que llega.

Mientras corre UAT reescribe DefaultEngine.ini (y lo restaura al final):
  - GameDefaultMap = L_Demo_Menu
  - con renderer movil: agrega PCD3D_ES31 a los formatos de shader de Windows (D3D12 y D3D11) para poder lanzar con -FeatureLevelES31.
Archivo en VR_Test/Saved/Packaged/Win64_Robot; deja Robot.bat al lado del .exe:
  -nohmd (aunque haya un visor por Link, el robot no lo usa) · -MirrorRole=2 (receptor) · -FeatureLevelES31 (si es movil) · ventana 1920x1080.
Antes: Save All en el editor y NO guardar assets mientras cocina.
"""
import argparse, difflib, glob, os, re, shutil, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
ENGINE = os.environ.get("UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")
INI = os.path.join(ROOT, "VR_Test", "Config", "DefaultEngine.ini")
DEMO = "/Game/SoulCharger/Demo/Maps/"
MAPS = [DEMO + "L_Demo_Menu", DEMO + "L_Demo_Breath", DEMO + "L_Demo_Draw", DEMO + "L_Demo_Heart"]
MAPA_INICIO = DEMO + "L_Demo_Menu.L_Demo_Menu"
SECCION = "[/Script/WindowsTargetPlatform.WindowsTargetSettings]"

def ini_para(ini0, movil):
    ini = re.sub(r"^GameDefaultMap=.*$", "GameDefaultMap=" + MAPA_INICIO, ini0, flags=re.M)
    if not re.search("^GameDefaultMap=" + re.escape(MAPA_INICIO) + "$", ini, flags=re.M):
        sys.exit("DefaultEngine.ini no tiene GameDefaultMap para reescribir: no cocino.")
    if movil:
        if SECCION not in ini:
            sys.exit("DefaultEngine.ini no tiene la seccion de Windows: no cocino.")
        extra = "+D3D12TargetedShaderFormats=PCD3D_ES31\n+D3D11TargetedShaderFormats=PCD3D_ES31\n"
        ini = ini.replace(SECCION + "\n", SECCION + "\n" + extra, 1)
    return ini

def comando_uat(arch):
    return [os.path.join(ENGINE, "Engine", "Build", "BatchFiles", "RunUAT.bat"), "BuildCookRun",
            "-project=" + UPROJECT, "-unrealexe=" + os.path.join(ENGINE, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe"),
            "-platform=Win64", "-clientconfig=Development", "-cook", "-map=" + "+".join(MAPS),
            "-skipbuildeditor", "-nocompileeditor",
            "-AdditionalCookerOptions=-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False",
            "-build", "-stage", "-pak", "-iostore", "-compressed", "-archive", "-archivedirectory=" + arch,
            "-prereqs", "-utf8output", "-nop4"]

def destrabar(*rutas):
    # carpetas de build marcadas solo lectura hacen fallar el staging (paso el 2026-10-16)
    for r in rutas:
        for d, dirs, _ in os.walk(r):
            for x in [d] + [os.path.join(d, n) for n in dirs]:
                try:
                    os.chmod(x, 0o777)
                except OSError:
                    pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escritorio", action="store_true", help="renderer de escritorio en vez del movil")
    ap.add_argument("--en-seco", action="store_true")
    a = ap.parse_args()
    movil = not a.escritorio
    arch = os.path.join(ROOT, "VR_Test", "Saved", "Packaged", "Win64_Robot")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ini_respaldo
    ini0 = ini_respaldo.ini_limpio(INI)
    ini = ini_para(ini0, movil)
    cmd = comando_uat(arch)
    args = ["-nohmd", "-unattended", "-MirrorRole=2", "-windowed", "-ResX=1920", "-ResY=1080", "-log"] + (["-FeatureLevelES31"] if movil else [])
    # el robot repite la demo: tampoco se cocina con las perillas de prueba encendidas (tools/demo/verificar_perillas.py)
    sys.path.insert(0, os.path.join(ROOT, "tools", "demo"))
    import verificar_perillas
    verificar_perillas.main()
    if a.en_seco:
        print("renderer: " + ("movil (ES3.1)" if movil else "escritorio"))
        print("\n".join(difflib.unified_diff(ini0.splitlines(), ini.splitlines(), "DefaultEngine.ini", "(UAT)", lineterm="", n=0)))
        print("comando UAT:\n  " + " ".join(cmd))
        print("Robot.bat: VR_Test.exe " + " ".join(args) + " -MirrorMyIP=<IP de este PC>")
        return
    destrabar(os.path.join(ROOT, "VR_Test", "Saved", "StagedBuilds"), os.path.join(ROOT, "VR_Test", "Saved", "Packaged"))
    shutil.rmtree(arch, ignore_errors=True)
    log = os.path.join(ROOT, "VR_Test", "Saved", "Logs", "empaquetar_robot_%s.log" % time.strftime("%Y%m%d-%H%M%S"))
    t0 = time.time()
    print("cocinando el robot (Win64, %s)... log: %s" % ("movil" if movil else "escritorio", log), flush=True)
    try:
        if ini != ini0:
            ini_respaldo.escribir_temporal(INI, ini)
        with open(log, "w", encoding="utf-8", errors="ignore") as f:
            rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    finally:
        ini_respaldo.restaurar(INI, ini0)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import mcp_config; mcp_config.asegurar_autostart()
    print("UAT termino con codigo %d en %d min" % (rc, (time.time() - t0) / 60))
    exes = [e for e in glob.glob(os.path.join(arch, "**", "*.exe"), recursive=True) if "CrashReport" not in e and "Prereq" not in e]
    if not exes:
        print("NO hay .exe. Ultimas lineas del log:")
        print("\n".join(open(log, encoding="utf-8", errors="ignore").read().splitlines()[-25:]))
        sys.exit(1)
    exe = min(exes, key=len)
    bat = os.path.join(os.path.dirname(exe), "Robot.bat")
    # 2026-10-20 noche: el robot muestra en pantalla el estado de la conexion con el Quest y la IP de este PC (la que hay que
    # darle al Quest con quest_ip_espejo.ps1). La calcula mi_ip.ps1: la del hotspot de Windows si este PC lo comparte
    # (192.168.137.x, 20-10 noche: la wifi de invitados del lab aisla a los equipos), si no el adaptador con puerta de enlace.
    # Sin puerta de enlace (router aislado) sale "unknown": escribirla a mano en el .bat (set MYIP=192.168.x.x).
    ps1 = os.path.join(os.path.dirname(exe), "mi_ip.ps1")
    with open(ps1, "w", newline="") as f:
        # 1) la wifi local "Alma Digital" (192.168.0.x, 21-10: el laptop 192.168.0.190, el Quest 192.168.0.139);
        # 2) si este PC comparte un hotspot de Windows (192.168.137.1), esa es la IP que ve el Quest conectado a el
        f.write("$r = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -like '192.168.0.*' -and $_.AddressState -eq 'Preferred' } | Select-Object -First 1\r\nif ($r) { $r.IPAddress; exit }\r\n$h = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -like '192.168.137.*' } | Select-Object -First 1\r\nif ($h) { $h.IPAddress; exit }\r\n$c = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1\r\nif ($c) { $c.IPv4Address[0].IPAddress } else { 'unknown' }\r\n")
    with open(bat, "w", newline="") as f:
        f.write('@echo off\r\ncd /d "%~dp0"\r\nset MYIP=unknown\r\n'
                'for /f "usebackq delims=" %%i in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mi_ip.ps1"`) do set MYIP=%%i\r\n'
                'start "" "' + os.path.basename(exe) + '" ' + " ".join(args) + ' -MirrorMyIP=%MYIP%\r\n')
    print("robot: %s\nlanzador: %s" % (exe, bat))

if __name__ == "__main__":
    main()
