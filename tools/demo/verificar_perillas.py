"""verificar_perillas.py - la demo BDW no se cocina con las perillas de prueba encendidas (2026-10-19)

Lee los .umap de la demo (tabla de nombres + etiquetas de propiedad) y compara cada perilla con su valor de publico.
Una perilla que no aparece en el .umap vale lo del Blueprint (los valores por defecto no se guardan): para las que el
Blueprint ya trae el valor de publico, no aparecer = bien. Las que tienen que estar puestas en el nivel (Cycles) se exigen.

  python tools/demo/verificar_perillas.py            # informe; sale con codigo 1 si algo no es de publico
  python tools/demo/verificar_perillas.py --mostrar  # ademas lista cada valor encontrado

Lo llaman empaquetar_obra.py --variante demo y empaquetar_robot.py antes de cocinar.
Si cambia un valor de publico, cambiarlo en PUBLICO y en docs/demo/DEMO-BDW.md (tabla "Antes del APK").
"""
import os, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAPS = os.path.join(ROOT, "VR_Test", "Content", "SoulCharger", "Demo", "Maps")

# nombre de la propiedad -> (regla, valor). 'igual' = si aparece tiene que valer eso; 'exigir' = tiene que aparecer y valer eso;
# 'positivo' = si aparece tiene que ser > 0 (un tiempo limite en 0 apaga la salida automatica de esa espera)
# MirrorRole 0 = el enlace decide solo (con visor emite, sin visor recibe); 2 guardado dejaria al Quest esperando una pose que nadie manda
# bFakeSignal (20-10 noche, pedido de Beltran tras el APK Demo_BDW: "no tenia la data simulada, se veia todo plano"): la demo va con
# la senal SIMULADA del Muse en el BioHub de los 4 niveles. Si se conecta un Muse real, las dos entran por el mismo Ingest y se mezclan.
COMUN = {"bFakeSignal": ("exigir", True), "Every": ("igual", 0.0), "MirrorRole": ("igual", 0), "bLevelSync": ("igual", True)}
PUBLICO = {
    # DrawShowTime = el reloj que muestra el HUD del menu al elegir Draw (tiene que coincidir con DrawTime de L_Demo_Draw)
    "L_Demo_Menu": dict(COMUN, DebugPick=("igual", -1), DrawShowTime=("igual", 150.0)),
    # bAutoStart de la etapa: el Blueprint la trae en TRUE (arrancaria el flujo viejo a los 1,5 s), el nivel tiene que decir false
    "L_Demo_Breath": dict(COMUN, AutoHand=("igual", 0), AutoGo=("igual", 0.0), bTestSynth=("igual", False), Cycles=("exigir", 10),
                          GrabWait=("positivo", 0), ZoneWait=("positivo", 0), GoWait=("positivo", 0), BreathWait=("positivo", 0),
                          bAutoStart=("exigir", False), bContractTest=("igual", False), bShowMandoOnBegin=("igual", False),
                          TopeS=("igual", 170.0)),
    # banderas de prueba del sistema de dibujo (director y herramienta): nunca en un APK.
    # bForceTour SI va en true (2026-10-20): el director del dibujo duerme hasta que DemoFlow llama StageIntro al tomar el mando.
    # Antes lo dormia la etiqueta TOUR del ensayo viejo; sin ella la paleta y el mando aparecian al cargar el nivel.
    "L_Demo_Draw": dict(COMUN, AutoHand=("igual", 0), AutoGo=("igual", 0.0), bTestSynth=("igual", False), DrawTime=("igual", 150.0),
                        GrabWait=("positivo", 0), PracticeWait=("positivo", 0),
                        bForceTour=("exigir", True), bContractTest=("igual", False), bSynth=("igual", False), bSynthDry=("igual", False)),
    # Heart (RECOGNIZING, 2026-10-20): el director y las perillas de prueba del latido (bFakeBeat / bIgnoreTracking / HeartVDropMin -100
    # son las recetas de PIE de escritorio; en el visor tienen que quedar como en el Blueprint)
    "L_Demo_Heart": dict(COMUN, AutoHand=("igual", 0), AutoGo=("igual", 0.0), GrabWait=("positivo", 0), ZoneWait=("positivo", 0),
                         TopeS=("igual", 150.0), bContractTest=("igual", False), bFakeBeat=("igual", False), bIgnoreTracking=("igual", False),
                         HeartVDropMin=("igual", 10.0)),
}


def leer(path):
    b = open(path, "rb").read()
    p = 4
    legacy, = struct.unpack_from("<i", b, p); p += 4
    if legacy != -4:
        p += 4
    p += 4 + 4 + 4 + 20  # ue4, ue5, licencia, guid/cabecera
    p += 4  # tamano total de la cabecera
    ncv, = struct.unpack_from("<i", b, p); p += 4
    p += ncv * 20
    l, = struct.unpack_from("<i", b, p); p += 4
    p += l if l > 0 else -l * 2
    p += 4  # flags
    ncount, noff = struct.unpack_from("<ii", b, p)
    names, q = [], noff
    for _ in range(ncount):
        l, = struct.unpack_from("<i", b, q); q += 4
        if l > 0:
            names.append(b[q:q + l - 1].decode("latin1")); q += l
        else:
            names.append(b[q:q + (-l - 1) * 2].decode("utf-16le")); q += -l * 2
        q += 4  # hashes
    return b, names


def valores(b, names, prop):
    """todas las etiquetas de propiedad llamadas prop: [(tipo, valor)]"""
    if prop not in names:
        return []
    out, pat, pos = [], struct.pack("<ii", names.index(prop), 0), 0
    while True:
        p = b.find(pat, pos)
        if p < 0:
            return out
        pos = p + 1
        if p + 32 > len(b):
            continue
        ti, _ = struct.unpack_from("<ii", b, p + 8)
        if not (0 <= ti < len(names)) or not names[ti].endswith("Property"):
            continue
        t = names[ti]
        fl = b[p + 24]
        vo = p + 25 + (16 if fl & 2 else 0)
        if t == "FloatProperty":
            v = struct.unpack_from("<f", b, vo)[0]
        elif t == "DoubleProperty":
            v = struct.unpack_from("<d", b, vo)[0]
        elif t == "IntProperty":
            v = struct.unpack_from("<i", b, vo)[0]
        elif t == "BoolProperty":
            v = bool(fl & 0x10)
        else:
            continue
        out.append((t, v))


def revisar(mostrar=False):
    errores = []
    for mapa, reglas in PUBLICO.items():
        path = os.path.join(MAPS, mapa + ".umap")
        if not os.path.exists(path):
            errores.append("%s: no existe %s" % (mapa, path)); continue
        b, names = leer(path)
        # 20-10 noche: con Muse Integration la "calma" del BioHub (grafico del HUD = actividad neuronal) es /muse/alpha; el indice de
        # calma llega aparte por /muse/calm_index (CDO del BioHub). La direccion vieja /muse/calm ya no la manda nadie.
        if b"/muse/alpha" not in b:
            errores.append("%s: el BioHub no lee /muse/alpha (AddrCalm de la instancia): la actividad neuronal del HUD quedaria en 0" % mapa)
        for prop, (regla, pub) in reglas.items():
            vs = valores(b, names, prop)
            if mostrar:
                print("  %-14s %-12s %s" % (mapa, prop, [round(v, 3) if isinstance(v, float) else v for _, v in vs] or "(lo del Blueprint)"))
            if regla == "exigir" and not vs:
                errores.append("%s: %s no esta puesto en el nivel (tiene que valer %s)" % (mapa, prop, pub))
            for _, v in vs:
                if regla in ("igual", "exigir") and abs(float(v) - float(pub)) > 1e-4:
                    errores.append("%s: %s = %s (publico: %s)" % (mapa, prop, v, pub))
                if regla == "positivo" and float(v) <= 0.0:
                    errores.append("%s: %s = %s (un tiempo limite en 0 apaga la salida automatica)" % (mapa, prop, v))
    return errores


def main():
    errores = revisar("--mostrar" in sys.argv)
    if errores:
        print("PERILLAS DE PRUEBA ENCENDIDAS - no se cocina la demo asi:")
        for e in errores:
            print("  - " + e)
        print("Arreglarlas en el editor (tabla 'Antes del APK' de docs/demo/DEMO-BDW.md), Save All, y volver a correr.")
        sys.exit(1)
    print("perillas de la demo: valores de publico OK")


if __name__ == "__main__":
    main()
