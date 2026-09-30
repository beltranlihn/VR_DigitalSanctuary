import json
# ghost_dump.py - despues de una tanda de grabacion: los DA_Ghost_<ID> que tienen toma se MARCAN (set de Note, porque la
# escritura runtime del grabador no ensucia el paquete), se GUARDAN con ruta explicita y dejan un RESPALDO JSON en
# Saved/ClaudeScripts/ghost/ (despues se copia al repo: scripts/ghost/takes/). Los datos NO salen del editor: el
# script devuelve solo el resumen. Se pega ENTERO como `script` de execute_tool_script.
# SOLO_RESPALDO = True  -> con el PIE ABIERTO (en plena sesion): solo escribe el JSON de cada toma (guardar assets en
#                          PIE falla). Si el editor se cae, las tomas se reponen desde esos JSON.
# SOLO_RESPALDO = False -> con el PIE DETENIDO: marca, guarda con ruta explicita y escribe el JSON.
SOLO_RESPALDO = False
NOTE = 'grabado por Beltran, sesion 2026-09-30'
SPEC = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/ghost_spec.json'
DIR = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/ghost/'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
LOG = []
PROPS = ['Id', 'Text', 'Hz', 'Frames', 'Stride', 'Data', 'bUseRight', 'bUseLeft', 'bBeamRight', 'bBeamLeft', 'Note']


def T(name, payload):
    try:
        r = execute_tool(name, json.dumps(payload))
        v = r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r
        return True, v
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:200])
        return False, None


def G(ref, props):
    ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': props})
    if not ok or v is None:
        return None
    try:
        return json.loads(v) if isinstance(v, str) else v
    except BaseException:
        return None


def run():
    ok, txt = T(AS + 'read_file', {'file_path': SPEC})
    if not ok:
        return {'err': 'no pude leer la spec', 'log': LOG}
    spec = json.loads(txt)
    folder = spec['DA']['folder']
    out, guardar = {}, []
    for it in spec['DA']['items']:
        a = it['asset']
        ref = folder + '/' + a + '.' + a
        v = G(ref, PROPS)
        if not v:
            out[a] = 'no se pudo leer'
            continue
        n = v['Frames'] if 'Frames' in v else 0
        data = v['Data'] if 'Data' in v else []
        st = v['Stride'] if 'Stride' in v else 28
        rec = {'cuadros': n, 'floats': len(data), 'seg': round(n / 30.0, 2)}
        if n > 1 and len(data) >= n * st:
            rec['respaldo'] = T(AS + 'write_file', {'file_path': DIR + a + '_take.json', 'content': json.dumps(v)})[0]
            if not SOLO_RESPALDO:
                rec['marcado'] = T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps({'Note': NOTE})})[0]
                guardar.append(folder + '/' + a)
        elif n > 0:
            rec['OJO'] = 'Frames y Data no coinciden: no se guarda'
        out[a] = rec
    if guardar:
        out['guardados'] = T(AS + 'save_assets', {'asset_paths': guardar})[0]
        out['rutas'] = [g.split('/')[-1] for g in guardar]
    out['log'] = LOG[:20]
    return out
