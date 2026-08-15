# PLANTILLA OBLIGATORIA para todo execute_tool_script — 2026-08-15
#
# 🔴🔴 POR QUÉ EXISTE ESTE ARCHIVO (incidente del 2026-08-15, costó actores del nivel):
# Cada `execute_tool_script` que **termina en excepción** hace que el plugin dispare un
# `Undo` del editor:
#     LogEditorTransaction: Undo Execute tool script
# Ese Undo saca la transacción de ARRIBA de la pila de undo del editor — que es GLOBAL.
# Si mi script no alcanzó a hacer ningún cambio transaccionable, el Undo **se come una
# transacción ANTERIOR que no es mía**. Con 7 fallos seguidos, `L_Persistent` perdió
# BP_StageDirector, BP_BioHub, BP_Finale, BP_SoulArchive y BP_Constellation, y el
# `save_assets` siguiente grabó el nivel ya mutilado.
#
# LA REGLA: **un script nunca debe dejar escapar una excepción.** Si falla, devuelve el
# error como DATO. Un script que retorna `{'errores': [...]}` no dispara Undo.
#
# Y ojo: `except Exception` NO alcanza — varios errores del plugin no derivan de Exception.
# Hay que usar **`except BaseException`**.

import json

BP = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AT = 'editor_toolset.toolsets.asset.AssetTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'

ERRS = []

def T(name, payload):
    """Llamada que NUNCA levanta. Devuelve (ok, valor)."""
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        ERRS.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None

def V(name, payload):
    """Cuando sólo importa el valor."""
    return T(name, payload)[1]

def level_canary():
    """Conteo de actores BP_ del nivel persistente. Correr ANTES y DESPUÉS de cada tanda.
    Si baja, algo se comió actores -> NO GUARDAR, revisar, y si hace falta recuperar del
    último commit (ver gotchas 'El Undo que borra el nivel')."""
    ok, acts = T(SC + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []})
    if not ok or not acts:
        return -1, []
    names = []
    for x in acts:
        rp = x['refPath'] if isinstance(x, dict) else str(x)
        if 'L_Persistent.L_Persistent:' in rp:
            n = rp.split('PersistentLevel.')[-1]
            if n.startswith('BP_'):
                names.append(n)
    return len(names), sorted(names)

def run():
    antes, _ = level_canary()

    # ---- el trabajo va acá, SIEMPRE por T()/V(), nunca execute_tool() pelado ----

    despues, quedan = level_canary()
    return {
        'errores': ERRS,                    # <- si esto no está vacío, el script igual terminó OK
        'canario': str(antes) + ' -> ' + str(despues),
        'perdio_actores': (antes > 0 and despues < antes),
        'actores': quedan,
    }
