"""empaquetar_pantalla.py - Inner Canvas: arma la PANTALLA del PC (Win64, Development): el nivel L_InnerCanvas_Wall, que recibe por
OSC/UDP (puerto 9300) lo que dibuja cada visor Pico y muestra los 8 dibujos en vivo (4 x 2) con nombre, tiempo y tinta.

  python tools/innercanvas/empaquetar_pantalla.py             # renderer de escritorio (como se probo con probar_nivel)
  python tools/innercanvas/empaquetar_pantalla.py --en-seco   # muestra el comando y el cambio al ini, no cocina

Mientras corre UAT, DefaultEngine.ini lleva GameDefaultMap = L_InnerCanvas_Wall (se restaura al final, via ini_respaldo).
Archivo en VR_Test/Saved/Packaged/Win64_InnerCanvas; copia en "Recursos/Inner Canvas/Pantalla/<fecha>". Deja al lado del .exe:
  InnerCanvas_Pantalla.bat  pantalla completa en la SEGUNDA pantalla (o la unica), -nohmd, -ICPort=9300; antes muestra la IP de este PC
                            (la que va en -ICWall= de cada visor: tools/innercanvas/instalar_pico_ic.ps1 -Wall <IP>)
  InnerCanvas_Ventana.bat   lo mismo en ventana 1920x1080
La primera vez Windows pregunta por el firewall: permitir en redes PRIVADAS (si no, no llega nada por UDP 9300).
Antes: Save All en el editor y NO guardar assets mientras cocina.
"""
import argparse, datetime, difflib, glob, os, re, shutil, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
ENGINE = os.environ.get("UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")
INI = os.path.join(ROOT, "VR_Test", "Config", "DefaultEngine.ini")
MAPA = "/Game/InnerCanvas/Maps/L_InnerCanvas_Wall"
MAPA_INICIO = MAPA + ".L_InnerCanvas_Wall"
UMAP = os.path.join(ROOT, "VR_Test", "Content", "InnerCanvas", "Maps", "L_InnerCanvas_Wall.umap")
ARCH = os.path.join(ROOT, "VR_Test", "Saved", "Packaged", "Win64_InnerCanvas")
COPIA = os.path.join(ROOT, "Recursos", "Inner Canvas", "Pantalla")


def ini_para(ini0):
    ini = re.sub(r"^GameDefaultMap=.*$", "GameDefaultMap=" + MAPA_INICIO, ini0, flags=re.M)
    if not re.search("^GameDefaultMap=" + re.escape(MAPA_INICIO) + "$", ini, flags=re.M):
        sys.exit("DefaultEngine.ini no tiene GameDefaultMap para reescribir: no cocino.")
    return ini


def guardia():
    # el nivel no puede llevar el actor de capturas de prueba (saca una foto cada pocos segundos)
    b = open(UMAP, "rb").read()
    if b"BP_DemoShots_SC" in b:
        sys.exit("L_InnerCanvas_Wall tiene BP_DemoShots_SC (capturas de prueba): sacarlo antes de cocinar.")


def comando_uat():
    return [os.path.join(ENGINE, "Engine", "Build", "BatchFiles", "RunUAT.bat"), "BuildCookRun",
            "-project=" + UPROJECT, "-unrealexe=" + os.path.join(ENGINE, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe"),
            "-platform=Win64", "-clientconfig=Development", "-cook", "-map=" + MAPA,
            "-skipbuildeditor", "-nocompileeditor",
            "-AdditionalCookerOptions=-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False",
            "-build", "-stage", "-pak", "-iostore", "-compressed", "-archive", "-archivedirectory=" + ARCH,
            "-prereqs", "-utf8output", "-nop4"]


def destrabar(*rutas):
    for r in rutas:
        for d, dirs, _ in os.walk(r):
            for x in [d] + [os.path.join(d, n) for n in dirs]:
                try:
                    os.chmod(x, 0o777)
                except OSError:
                    pass


def lanzadores(exe):
    # 2026-11-13: el juego NO reconoce la escala de Windows (Unreal solo lo hace con bAllowHighDPIInGameMode): en un TV 4K al 300 %
    # Windows le daba 1280 x 720 y lo estiraba x3 (texto y dibujos pixelados). __COMPAT_LAYER=HighDpiAware lo deja por monitor
    # (verificado: awareness 2, DPI 288) y dibuja en 4K real. Abrir SIEMPRE con los .bat, no con el .exe.
    carpeta = os.path.dirname(exe)
    with open(os.path.join(carpeta, "mi_ip.ps1"), "w", newline="") as f:
        # la IP de este PC en la red del router de los visores: el adaptador con puerta de enlace (o el primero 192.168.x)
        f.write("$c = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1\r\n"
                "if ($c) { $c.IPv4Address[0].IPAddress; exit }\r\n"
                "$r = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -like '192.168.*' -and $_.AddressState -eq 'Preferred' } | Select-Object -First 1\r\n"
                "if ($r) { $r.IPAddress } else { 'desconocida' }\r\n")
    with open(os.path.join(carpeta, "pantalla.ps1"), "w", newline="") as f:
        # La pantalla 2 (la que no es la principal) en PIXELES REALES con EnumDisplaySettings. 2026-11-13: Screen.Bounds, aun con
        # SetProcessDPIAware, daba 1280 x 720 para un TV 4K al 300 % (la escala del sistema es la de la principal) -> el juego salia
        # en 720p y el TV lo agrandaba 3 veces (textos y dibujos pixelados). DEVMODE da posicion y tamano en pixeles del escritorio.
        f.write("Add-Type -TypeDefinition @'\r\n"
                "using System; using System.Runtime.InteropServices;\r\n"
                "public class ICMon {\r\n"
                "  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]\r\n"
                "  public struct DEVMODE {\r\n"
                "    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName;\r\n"
                "    public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra;\r\n"
                "    public int dmFields, dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput;\r\n"
                "    public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;\r\n"
                "    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName;\r\n"
                "    public short dmLogPixels;\r\n"
                "    public int dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency, dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight;\r\n"
                "  }\r\n"
                "  [DllImport(\"user32.dll\", CharSet = CharSet.Ansi)] public static extern bool EnumDisplaySettings(string dev, int mode, ref DEVMODE dm);\r\n"
                "  public static string Get(string dev) {\r\n"
                "    DEVMODE m = new DEVMODE(); m.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));\r\n"
                "    if (!EnumDisplaySettings(dev, -1, ref m)) return null;\r\n"
                "    return m.dmPositionX + \" \" + m.dmPositionY + \" \" + m.dmPelsWidth + \" \" + m.dmPelsHeight;\r\n"
                "  }\r\n"
                "}\r\n"
                "'@\r\n"
                "Add-Type -AssemblyName System.Windows.Forms\r\n"
                "$s = [System.Windows.Forms.Screen]::AllScreens | Where-Object { -not $_.Primary } | Select-Object -First 1\r\n"
                "if (-not $s) { $s = [System.Windows.Forms.Screen]::PrimaryScreen }\r\n"
                "$r = [ICMon]::Get($s.DeviceName)\r\n"
                "if (-not $r) { $b = $s.Bounds; $r = \"{0} {1} {2} {3}\" -f $b.X, $b.Y, $b.Width, $b.Height }\r\n"
                "$r\r\n")
    ip = ('for /f "usebackq delims=" %%i in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mi_ip.ps1"`) do set MYIP=%%i\r\n'
          'echo.\r\necho   Inner Canvas - pantalla del PC\r\necho   IP de este PC (va en -Wall de instalar_pico_ic.ps1): %MYIP%   puerto UDP 9300\r\necho.\r\n')
    base = "-nohmd -unattended -ICPort=9300 -log"
    with open(os.path.join(carpeta, "InnerCanvas_Pantalla.bat"), "w", newline="") as f:
        f.write('@echo off\r\ncd /d "%~dp0"\r\nset MYIP=desconocida\r\n' + ip +
                'set WX=0\r\nset WY=0\r\nset WW=1920\r\nset WH=1080\r\n'
                'for /f "usebackq tokens=1-4" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pantalla.ps1"`) do (\r\n'
                '  set WX=%%a\r\n  set WY=%%b\r\n  set WW=%%c\r\n  set WH=%%d\r\n)\r\n'
                'echo   Pantalla: %WW% x %WH% (pantalla completa; 3840 x 2160 = 4K)\r\necho.\r\n'
                'set __COMPAT_LAYER=HighDpiAware\r\n' + 'start "" "' + os.path.basename(exe) + '" ' + base + ' -WinX=%WX% -WinY=%WY% -ResX=%WW% -ResY=%WH% -fullscreen\r\n'
                'timeout /t 8\r\n')
    # Configurar_IP_Picos.bat: en la red del evento (sin internet), escribe en cada Pico conectada por USB su numero
    # (tools/innercanvas/visores_ic.json) y la IP que el router le dio a este PC; reinicia la app. No reinstala.
    with open(os.path.join(carpeta, "Configurar_IP_Picos.bat"), "w", newline="") as f:
        f.write('@echo off\r\ncd /d "%~dp0"\r\nset MYIP=desconocida\r\n' + ip +
                'echo   Conecta las Pico por USB (con el PC ya en la red del router).\r\n'
                # 2026-11-13: confirmar antes de escribir (en otra red dejaria las 8 Pico apuntando a una IP equivocada;
                # Beltran las quiere en el router de Alma, PC = 192.168.0.190)
                'echo   OJO: las Pico quedan apuntando a %MYIP%. En el router de Alma tiene que ser 192.168.0.190.\r\necho.\r\n'
                'choice /c SN /m "   Escribir %MYIP% en las Pico conectadas"\r\nif errorlevel 2 goto fin\r\n'
                'powershell -NoProfile -ExecutionPolicy Bypass -File "' + os.path.join(ROOT, 'tools', 'innercanvas', 'instalar_pico_ic.ps1') + '" -Todos -Wall %MYIP% -SoloLinea -Lanzar\r\n'
                ':fin\r\necho.\r\npause\r\n')
    # InnerCanvas_Ventana.bat: ventana (no pantalla completa) centrada en la PANTALLA 2 (la misma que elige pantalla.ps1), de
    # 1920 x 1080 o menos si esa pantalla es mas chica
    with open(os.path.join(carpeta, "InnerCanvas_Ventana.bat"), "w", newline="") as f:
        f.write('@echo off\r\ncd /d "%~dp0"\r\nset MYIP=desconocida\r\n' + ip +
                'set WX=0\r\nset WY=0\r\nset WW=1920\r\nset WH=1080\r\n'
                'for /f "usebackq tokens=1-4" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pantalla.ps1"`) do (\r\n'
                '  set WX=%%a\r\n  set WY=%%b\r\n  set WW=%%c\r\n  set WH=%%d\r\n)\r\n'
                'set VW=1920\r\nset VH=1080\r\nif %WW% LSS 1920 set VW=%WW%\r\nif %WH% LSS 1080 set VH=%WH%\r\n'
                'set /a OX=%WX%+(%WW%-%VW%)/2\r\nset /a OY=%WY%+(%WH%-%VH%)/2\r\n'
                'echo   Ventana %VW% x %VH% en la pantalla 2 (%WW% x %WH%)\r\necho.\r\n'
                'set __COMPAT_LAYER=HighDpiAware\r\n' + 'start "" "' + os.path.basename(exe) + '" ' + base + ' -windowed -WinX=%OX% -WinY=%OY% -ResX=%VW% -ResY=%VH%\r\n'
                'timeout /t 8\r\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--en-seco", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(ROOT, "tools", "unreal"))
    import ini_respaldo
    guardia()
    ini0 = ini_respaldo.ini_limpio(INI)
    ini = ini_para(ini0)
    cmd = comando_uat()
    if a.en_seco:
        print("\n".join(difflib.unified_diff(ini0.splitlines(), ini.splitlines(), "DefaultEngine.ini", "(UAT)", lineterm="", n=0)))
        print("comando UAT:\n  " + " ".join(cmd))
        return
    destrabar(os.path.join(ROOT, "VR_Test", "Saved", "StagedBuilds"), os.path.join(ROOT, "VR_Test", "Saved", "Packaged"))
    shutil.rmtree(ARCH, ignore_errors=True)
    log = os.path.join(ROOT, "VR_Test", "Saved", "Logs", "empaquetar_pantalla_ic_%s.log" % time.strftime("%Y%m%d-%H%M%S"))
    t0 = time.time()
    print("cocinando la pantalla de Inner Canvas (Win64)... log: %s" % log, flush=True)
    try:
        if ini != ini0:
            ini_respaldo.escribir_temporal(INI, ini)
        with open(log, "w", encoding="utf-8", errors="ignore") as f:
            rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    finally:
        ini_respaldo.restaurar(INI, ini0)
        import mcp_config; mcp_config.asegurar_autostart()
    print("UAT termino con codigo %d en %d min" % (rc, (time.time() - t0) / 60))
    exes = [e for e in glob.glob(os.path.join(ARCH, "**", "*.exe"), recursive=True) if "CrashReport" not in e and "Prereq" not in e]
    if not exes:
        print("NO hay .exe. Ultimas lineas del log:")
        print("\n".join(open(log, encoding="utf-8", errors="ignore").read().splitlines()[-25:]))
        sys.exit(1)
    exe = min(exes, key=len)
    lanzadores(exe)
    dst = os.path.join(COPIA, "Inner Canvas Pantalla " + datetime.datetime.now().strftime("%Y-%m-%d %H%M"))
    shutil.copytree(os.path.dirname(os.path.dirname(exe)) if os.path.basename(os.path.dirname(exe)) == "Windows" else os.path.dirname(exe), dst)
    print("pantalla: %s\nlanzador: InnerCanvas_Pantalla.bat (pantalla completa en la segunda pantalla)\ncopia: %s" % (exe, dst))


if __name__ == "__main__":
    main()
