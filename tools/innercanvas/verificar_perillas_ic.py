"""verificar_perillas_ic.py - Inner Canvas no se cocina con las perillas de prueba encendidas.

Lee L_InnerCanvas.umap (mismo lector que tools/demo/verificar_perillas.py) y compara cada perilla con su valor de publico.
Una perilla que no aparece en el .umap vale lo del Blueprint (el CDO ya trae el valor de publico).

  python tools/innercanvas/verificar_perillas_ic.py            # informe; sale con 1 si algo no es de publico
  python tools/innercanvas/verificar_perillas_ic.py --mostrar  # ademas lista cada valor encontrado

Perillas de prueba (para probar sin visor con tools/unreal/probar_nivel.py): en BP_ICFlow_IC del nivel, AutoLang 0/1 (elige
idioma solo), AutoName (escribe ese nombre), AutoHand 1/2 (toma el pincel), bTestSynth (trazo sintetico), y tiempos cortos.
"""
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'demo'))
import verificar_perillas as vp   # leer(), valores()

MAPA = os.path.join(ROOT, 'VR_Test', 'Content', 'InnerCanvas', 'Maps', 'L_InnerCanvas.umap')
PUBLICO = {
    'AutoLang': ('igual', -1), 'AutoHand': ('igual', 0), 'AutoGo': ('igual', 0.0), 'bTestSynth': ('igual', False),
    'DrawTime': ('igual', 300.0), 'ResetMode': ('igual', 0), 'GrabWait': ('positivo', 0), 'PracticeWait': ('positivo', 0),
    'SpinShow': ('igual', 30.0), 'CloseHold': ('igual', 7.0),
    'bForceTour': ('exigir', True), 'bContractTest': ('igual', False), 'bSynth': ('igual', False), 'bSynthDry': ('igual', False),
    'Every': ('igual', 0.0),
}


def revisar(mostrar=False):
    errores = []
    if not os.path.exists(MAPA):
        return ['no existe ' + MAPA]
    b, names = vp.leer(MAPA)
    if b'BP_DemoShots_SC' in b:
        errores.append('quedo un BP_DemoShots_SC (capturas de prueba) en el nivel')
    if b'AutoName' in b and b'Prueba' in b:
        errores.append('AutoName tiene un nombre de prueba (tiene que estar vacio)')
    for prop, (regla, pub) in PUBLICO.items():
        vs = vp.valores(b, names, prop)
        if mostrar:
            print('  %-14s %s' % (prop, [round(v, 3) if isinstance(v, float) else v for _, v in vs] or '(lo del Blueprint)'))
        if regla == 'exigir' and not vs:
            errores.append('%s no esta puesto en el nivel (tiene que valer %s)' % (prop, pub))
        for _, v in vs:
            if regla in ('igual', 'exigir') and abs(float(v) - float(pub)) > 1e-4:
                errores.append('%s = %s (publico: %s)' % (prop, v, pub))
            if regla == 'positivo' and float(v) <= 0.0:
                errores.append('%s = %s (un tiempo limite en 0 apaga la salida automatica)' % (prop, v))
    return errores


def main():
    errores = revisar('--mostrar' in sys.argv)
    if errores:
        print('PERILLAS DE PRUEBA ENCENDIDAS - no se cocina Inner Canvas asi:')
        for e in errores:
            print('  - ' + e)
        sys.exit(1)
    print('perillas de Inner Canvas: valores de publico OK')


if __name__ == '__main__':
    main()
