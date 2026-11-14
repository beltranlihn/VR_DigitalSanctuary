"""empaquetar_obra.py - arma el APK de la Obra o de la Demo (Quest 3, Development) y lo copia a Recursos.

  python tools/unreal/empaquetar_obra.py                 # paquete com.almadigital.soulcharger  "Soul Charger"
  python tools/unreal/empaquetar_obra.py --variante v2   # paquete com.almadigital.soulchargerv2 "Soul Charger V2" (convive con el otro)
  python tools/unreal/empaquetar_obra.py --variante demo # paquete com.almadigital.soulchargerdemo "Soul Charger Demo" (app aparte: menu + Breath + Draw)
  python tools/unreal/empaquetar_obra.py --variante demo --en-seco   # muestra variante, mapas, comando UAT y cambios al ini; no escribe ni cocina
  python tools/unreal/empaquetar_obra.py --variante demo --nombre Demo_BDW   # la demo con otro nombre en el visor y en la copia

Antes de empaquetar:
  1. Guardar todo en el editor (Ctrl+Shift+S). Mientras cocina, NO guardar assets.
  2. Correr la prueba de humo: python tools/unreal/smoke_obra.py  (tiene que dar OK).
  3. Revisar el checklist de build de publico en docs/GUIA-DE-DIRECCION.md (bSimulated, DebugStart, Speed...).

Cada variante define en VARIANTES su paquete, nombre, carpeta de archivo, MAPS (lo que se pasa a UAT como -map=) y su
mapa de arranque (GameDefaultMap, que se reescribe en DefaultEngine.ini mientras corre UAT y se restaura al final):
  obra / v2: la Obra y sus 6 celdas (las mismas que lista DefaultGame.ini); arranca en L_SoulCharger_Obra.
  demo:      L_Demo_Menu, L_Demo_Breath, L_Demo_Draw y L_Demo_Heart (Content/SoulCharger/Demo/Maps); arranca en L_Demo_Menu. El menu abre las
             otras dos con OpenLevel, que por nombre no asegura que el .umap entre al paquete: los 3 tienen que ir en MAPS (y
             cualquier otro nivel que la demo cargue por LoadLevelInstance o por nombre, tambien).
Archivo en VR_Test/Saved/Packaged/<carpeta> (Android_Obra, Android_ObraV2, Android_Demo); copia en
Recursos/Soul Charger - Escritorio 2026-10/APK/<nombre> <fecha>.
Para instalar en el visor: tools/unreal/instalar_quest.ps1 [-Variante v2|demo].

DefaultGame.ini NO se toca para ninguna variante (verificado en el motor 5.8, Engine/Source/Editor/UnrealEd/Private):
  - UAT pasa -map= al CookCommandlet como -Map= (AutomationUtils/CommandletUtils.cs) y CollectFilesToCook hace
    bFoundMapsToCook = CookMaps.Num() > 0 (CookOnTheFlyServer.cpp): con -map= la lista +MapsToCook se IGNORA, asi que la
    Obra y sus celdas listadas ahi no se suman al cocinado de la demo.
  - DirectoriesToAlwaysCook (/NNEDenoiser) si se suma siempre, pero es un plugin del motor: no mete contenido del juego.
  - Se cocinan siempre, como dependencias de los defaults, GameDefaultMap, GlobalDefaultGameMode y GameInstanceClass
    (DefaultEngine.ini: BP_SoulState). Para la demo eso significa que BP_SoulState (y lo que referencia) viaja en el paquete.
"""
import argparse, difflib, glob, os, re, shutil, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
UPROJECT = os.path.join(ROOT, "VR_Test", "VR_Test.uproject")
ENGINE = os.environ.get("UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")
INI = os.path.join(ROOT, "VR_Test", "Config", "DefaultEngine.ini")
USERINI = os.path.join(ROOT, "VR_Test", "Saved", "Config", "WindowsEditor", "EditorPerProjectUserSettings.ini")
MAPS = ["/Game/SoulCharger/Obra/L_SoulCharger_Obra", "/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath", "/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart", "/Game/SoulCharger/Mechanics/Mind/Maps/Test_Mind",
        "/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer", "/Game/SoulCharger/Mechanics/Draw/Maps/Test_Draw", "/Game/SoulCharger/Hall/Maps/Test_Hall"]
MAPA_OBRA = "/Game/SoulCharger/Obra/L_SoulCharger_Obra.L_SoulCharger_Obra"
DEMO = "/Game/SoulCharger/Demo/Maps/"
VARIANTES = {"obra": dict(pkg="com.almadigital.soulcharger", nombre="Soul Charger", carpeta="Android_Obra", maps=MAPS, mapa_inicio=MAPA_OBRA),
             "v2": dict(pkg="com.almadigital.soulchargerv2", nombre="Soul Charger V2", carpeta="Android_ObraV2", maps=MAPS, mapa_inicio=MAPA_OBRA),
             "demo": dict(pkg="com.almadigital.soulchargerdemo", nombre="Soul Charger Demo", carpeta="Android_Demo",
                          maps=[DEMO + "L_Demo_Menu", DEMO + "L_Demo_Breath", DEMO + "L_Demo_Draw", DEMO + "L_Demo_Heart"], mapa_inicio=DEMO + "L_Demo_Menu.L_Demo_Menu"),
             # 2026-10-24 (feria): la demo con eleccion de idioma (ENGLISH / ESPANOL) como app aparte, para no pisar la instalada
             "demobi": dict(pkg="com.almadigital.soulchargerdemobi", nombre="Soul Charger Demo Bilingual", carpeta="Android_DemoBi",
                          maps=[DEMO + "L_Demo_Menu", DEMO + "L_Demo_Breath", DEMO + "L_Demo_Draw", DEMO + "L_Demo_Heart"], mapa_inicio=DEMO + "L_Demo_Menu.L_Demo_Menu"),
             # 2026-11-11: Inner Canvas, la experiencia de dibujo de pie para 8 visores PICO 4 Ultra Enterprise (docs/innercanvas/PLAN-INNER-CANVAS.md).
             # pico=True: mientras cocina, sin empaquetado de Meta Quest y con 72 Hz pedidos por el plugin PICO OpenXR (docs/PICO-EMPAQUETADO.md).
             "innercanvas": dict(pkg="com.almadigital.innercanvas", nombre="Inner Canvas", carpeta="Android_InnerCanvas",
                                 maps=["/Game/InnerCanvas/Maps/L_InnerCanvas"], mapa_inicio="/Game/InnerCanvas/Maps/L_InnerCanvas.L_InnerCanvas",
                                 pico=True, hz="Rate72", copia=os.path.join("Recursos", "Inner Canvas", "APK")),
             # 2026-11-13: Inner Canvas para Meta Quest (Quest 2/3), app aparte para no pisar la de PICO. Mismo nivel; empaquetado de Meta
             # Quest como la Obra (el de PICO lo apaga y el Quest la abre como ventana 2D: cuadrado negro con audio) y con el hilo RHI.
             "innercanvasquest": dict(pkg="com.almadigital.innercanvasquest", nombre="Inner Canvas", carpeta="Android_InnerCanvasQuest",
                                      maps=["/Game/InnerCanvas/Maps/L_InnerCanvas"], mapa_inicio="/Game/InnerCanvas/Maps/L_InnerCanvas.L_InnerCanvas",
                                      quest=True, copia=os.path.join("Recursos", "Inner Canvas", "APK Quest"))}

PICO_SEC = "[/Script/PICOOpenXRRuntimeSettings.PICOOpenXRRuntimeSettings]"

def ini_pico(ini, hz):
    # solo mientras cocina la variante Pico: sin Meta Quest (paquete y dispositivos soportados), app de VR para PICO y la frecuencia
    ini = re.sub(r"^bPackageForMetaQuest=.*$", "bPackageForMetaQuest=False", ini, flags=re.M)
    ini = re.sub(r'<meta-data android:name="com\.oculus\.supportedDevices"[^>]*/>(\\n)?', "", ini)
    if "pvr.app.type" not in ini:
        ini = re.sub(r"^(\[/Script/AndroidRuntimeSettings\.AndroidRuntimeSettings\]\n)", r'\1ExtraActivitySettings=<meta-data android:name="pvr.app.type" android:value="vr" />\n', ini, flags=re.M)
    if PICO_SEC not in ini:
        ini = ini.rstrip("\n") + "\n\n" + PICO_SEC + "\n"
    if re.search(r"^DisplayRefreshRate=.*$", ini, flags=re.M):
        ini = re.sub(r"^DisplayRefreshRate=.*$", "DisplayRefreshRate=" + hz, ini, flags=re.M)
    else:
        ini = ini.replace(PICO_SEC + "\n", PICO_SEC + "\nDisplayRefreshRate=" + hz + "\n")
    for k in ("bPackageForMetaQuest=False", "DisplayRefreshRate=" + hz):
        if not re.search("^" + re.escape(k) + "$", ini, flags=re.M):
            sys.exit("no pude poner '%s' en el ini para Pico: no cocino." % k)
    return ini

def ini_quest(ini):
    # variante de Meta Quest con el plugin PICO OpenXR activo: el empaquetado de Quest tiene que estar (lo abre en VR, no en 2D) y
    # DisableRHIThread=False, porque el plugin apaga el hilo RHI en Android aunque el visor no sea PICO (docs/PICO-EMPAQUETADO.md)
    ini = re.sub(r"^DisableRHIThread=.*$", "DisableRHIThread=False", ini, flags=re.M)
    for k in ("bPackageForMetaQuest=True",):
        if not re.search("^" + re.escape(k) + "$", ini, flags=re.M):
            sys.exit("el ini no tiene '%s': el APK no abriria en VR en el Quest. No cocino." % k)
    if not re.search(r'com\.oculus\.supportedDevices" android:value="[^"]*quest2', ini):
        sys.exit("el ini no lista quest2 en com.oculus.supportedDevices: no cocino.")
    return ini

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

def ini_para(v, ini0):
    # DefaultEngine.ini con el paquete, el nombre y el mapa de arranque de la variante (no escribe nada)
    ini = re.sub(r"^PackageName=.*$", "PackageName=" + v["pkg"], ini0, flags=re.M)
    ini = re.sub(r"^ApplicationDisplayName=.*$", "ApplicationDisplayName=" + v["nombre"], ini, flags=re.M)
    ini = re.sub(r"^GameDefaultMap=.*$", "GameDefaultMap=" + v["mapa_inicio"], ini, flags=re.M)
    # un re.sub sin coincidencia no avisa: sin esta linea el APK arrancaria en otro mapa (o en uno que no cocino)
    for k in ("PackageName=" + v["pkg"], "ApplicationDisplayName=" + v["nombre"], "GameDefaultMap=" + v["mapa_inicio"]):
        if not re.search("^" + re.escape(k) + "$", ini, flags=re.M):
            sys.exit("DefaultEngine.ini no tiene la linea '%s' para reescribir: no cocino." % k.split("=")[0])
    if v.get("pico"):
        ini = ini_pico(ini, v.get("hz", "Rate72"))
    else:
        # 2026-11-14 (auditoría H5): el plugin PICO OpenXR deja DisableRHIThread=True en el ini compartido y lo aplica en Android aunque
        # el visor no sea PICO; los APK de Quest (Obra, demo) salían sin hilo RHI. Solo la variante PICO lo conserva.
        ini = re.sub(r"^DisableRHIThread=.*$", "DisableRHIThread=False", ini, flags=re.M)
    if v.get("quest"):
        ini = ini_quest(ini)
    return ini

def comando_uat(v, arch):
    return [os.path.join(ENGINE, "Engine", "Build", "BatchFiles", "RunUAT.bat"), "BuildCookRun",
            "-project=" + UPROJECT, "-unrealexe=" + os.path.join(ENGINE, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe"),
            "-platform=Android", "-cookflavor=ASTC", "-clientconfig=Development", "-cook", "-map=" + "+".join(v["maps"]),
            "-skipbuildeditor", "-nocompileeditor",
            "-AdditionalCookerOptions=-ini:EditorPerProjectUserSettings:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False",
            "-build", "-stage", "-pak", "-iostore", "-compressed", "-package", "-archive", "-archivedirectory=" + arch,
            "-prereqs", "-utf8output", "-nop4"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variante", choices=sorted(VARIANTES), default="obra")
    ap.add_argument("--sin-copia", action="store_true")
    ap.add_argument("--en-seco", action="store_true", help="muestra lo que haria (mapas, comando, cambios al ini) sin escribir ni cocinar")
    ap.add_argument("--nombre", help="nombre de la app en el visor, de la copia en Recursos y del .apk copiado (p. ej. Demo_BDW); el paquete no cambia")
    a = ap.parse_args()
    v = dict(VARIANTES[a.variante])
    if a.nombre:
        v["nombre"] = a.nombre
    pkg, nombre, carpeta = v["pkg"], v["nombre"], v["carpeta"]
    arch = os.path.join(ROOT, "VR_Test", "Saved", "Packaged", carpeta)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ini_respaldo
    ini0 = ini_respaldo.ini_limpio(INI)
    ini = ini_para(v, ini0)
    cmd = comando_uat(v, arch)
    if a.variante.startswith("demo"):
        # la demo no se cocina con las perillas de prueba encendidas (autopiloto, senal falsa, reloj corto): ver tools/demo/verificar_perillas.py
        sys.path.insert(0, os.path.join(ROOT, "tools", "demo"))
        import verificar_perillas
        verificar_perillas.main()
    if a.variante.startswith("innercanvas"):
        # Inner Canvas tampoco (idioma/nombre/mano automaticos, trazo sintetico, tiempos cortos, capturas)
        sys.path.insert(0, os.path.join(ROOT, "tools", "innercanvas"))
        import verificar_perillas_ic
        verificar_perillas_ic.main()
    if a.en_seco:
        print("variante %s: %s (%s)  archivo: %s" % (a.variante, nombre, pkg, arch))
        print("GameDefaultMap: " + v["mapa_inicio"])
        print("MAPS (-map=):\n  " + "\n  ".join(v["maps"]))
        print("cambios a DefaultEngine.ini (temporales):")
        print("\n".join(difflib.unified_diff(ini0.splitlines(), ini.splitlines(), "DefaultEngine.ini", "DefaultEngine.ini (UAT)", lineterm="", n=0)) or "  (ninguno)")
        print("comando UAT:\n  " + " ".join(cmd))
        return
    shutil.rmtree(arch, ignore_errors=True)
    log = os.path.join(ROOT, "VR_Test", "Saved", "Logs", "empaquetar_%s_%s.log" % (a.variante, time.strftime("%Y%m%d-%H%M%S")))
    t0 = time.time()
    print("cocinando %s (%s)... log: %s" % (nombre, pkg, log), flush=True)
    try:
        if ini != ini0:
            ini_respaldo.escribir_temporal(INI, ini)
        with open(log, "w", encoding="utf-8", errors="ignore") as f:
            rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    finally:
        ini_respaldo.restaurar(INI, ini0)
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
        base = os.path.join(ROOT, v["copia"]) if v.get("copia") else os.path.join(ROOT, "Recursos", "Soul Charger - Escritorio 2026-10", "APK")
        os.makedirs(base, exist_ok=True)
        dest = os.path.join(base, "%s APK %s" % (nombre, time.strftime("%Y-%m-%d %H%M")))
        shutil.copytree(os.path.dirname(apk), dest)
        if a.nombre:
            # el .apk con el nombre pedido (el OBB conserva el suyo: el sistema lo busca por nombre de paquete)
            os.rename(os.path.join(dest, os.path.basename(apk)), os.path.join(dest, a.nombre + ".apk"))
            for bat in glob.glob(os.path.join(dest, "Install_*.bat")):     # el .bat de instalar a mano busca el nombre viejo
                t = open(bat, encoding="utf-8", errors="ignore").read().replace(os.path.basename(apk), a.nombre + ".apk")
                open(bat, "w", encoding="utf-8").write(t)
        print("copia: " + dest)

if __name__ == "__main__":
    main()
