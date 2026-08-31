"""Renombra los artefactos de un archive de Android de VR_Test a SoulCharger.

UAT nombra el APK y los .bat con el nombre del .uproject. Este script hace el
post-proceso, y sobre todo BORRA un renombrado anterior antes de rehacerlo: si no,
queda un APK viejo con nombre nuevo junto a un OBB fresco, y el .bat instala la
combinación equivocada sin avisar.

Uso:  python rename_package.py "C:\...\Desktop\SoulCharger\Android_ASTC" [NuevoNombre]

NO se tocan:
  - el .obb   -> Android exige main.<versionCode>.<packageid>.obb
  - la linea "rm -r %STORAGE%/UnrealGame/VR_Test" de los .bat -> carpeta REAL del device
  - la carpeta VR_Test_Symbols_v1 -> la referencia el bat de symbolize
"""
import os
import sys

VIEJO = "VR_Test"


def main(carpeta, nuevo="SoulCharger"):
    if not os.path.isdir(carpeta):
        raise SystemExit("no existe la carpeta: " + carpeta)
    os.chdir(carpeta)

    # 1) limpiar un renombrado anterior (evita mezclar builds)
    for f in (nuevo + "-arm64.apk", "Install_" + nuevo + "-arm64.bat",
              "Uninstall_" + nuevo + "-arm64.bat",
              "SymbolizeCrashDump_" + nuevo + "-arm64.bat"):
        if os.path.exists(f):
            os.remove(f)
            print("borrado (renombrado viejo):", f)

    apk = VIEJO + "-arm64.apk"
    if not os.path.exists(apk):
        raise SystemExit("no hay " + apk + " -> el archive no es fresco")
    os.rename(apk, nuevo + "-arm64.apk")

    src = "Install_" + VIEJO + "-arm64.bat"
    s = open(src, encoding="utf-8", errors="surrogateescape").read()
    n = s.count(apk)
    s = s.replace(apk, nuevo + "-arm64.apk")
    open("Install_" + nuevo + "-arm64.bat", "w",
         encoding="utf-8", errors="surrogateescape").write(s)
    os.remove(src)

    for a in ("Uninstall_", "SymbolizeCrashDump_"):
        viejo = a + VIEJO + "-arm64.bat"
        if os.path.exists(viejo):
            os.rename(viejo, a + nuevo + "-arm64.bat")

    print("listo. referencias al apk parcheadas en el Install:", n)
    for f in sorted(os.listdir(".")):
        print("  ", f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "SoulCharger")
