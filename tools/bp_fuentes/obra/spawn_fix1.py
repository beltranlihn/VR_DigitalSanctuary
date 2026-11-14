# spawn_fix1.py (2026-09-30 ~23:40) - lo que nace cargado y no deberia. IDEMPOTENTE.
# 1) BP_StageRunner_SC: Title / Veil / Ghost nacen OCULTOS (bVisible false en el CDO). RBoot/RStep ya los prenden
#    explicitamente cuando corresponde; antes se veian en la Obra entre que la celda se registra y su BeginPlay.
# 2) BP_AlmaAura_SC.AuraDrive: rama "Is Not Valid" de AlmaRef -> DestroyActor (self). El aura muere con su Alma
#    (las Almas de ensayo TestOnly se destruyen al arrancar la Obra y dejaban 5 auras huerfanas en las celdas).
import json
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
RUN = '/Game/SoulCharger/Obra/BP_StageRunner_SC'
AU = '/Game/SoulCharger/Core/Alma/BP_AlmaAura_SC'
G = {'refPath': AU + '.BP_AlmaAura_SC:AuraDrive'}
ERRS = []
LOG = []
def T(n, p):
    try:
        return True, execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1] + ' :: ' + str(e)[:300]); return False, None
def infos():
    ok, ns = T(BT + 'find_nodes', {'graph': G, 'title': ''})
    ok, inf = T(BT + 'get_node_infos', {'nodes': ns or []})
    return inf or []
def run():
    out = {}
    try:
        for c in ['Title', 'Veil', 'Ghost']:
            ref = RUN + '.BP_StageRunner_SC_C:' + c + '_GEN_VARIABLE'
            T(OT + 'set_properties', {'instance': {'refPath': ref}, 'values': json.dumps({'bVisible': False})})
            ok, v = T(OT + 'get_properties', {'instance': {'refPath': ref}, 'properties': ['bVisible']})
            out['run_' + c] = str(v)
        ok, r = T(BT + 'compile_blueprint', {'blueprint': {'refPath': RUN + '.BP_StageRunner_SC'}})
        out['run_compile'] = str(r)[:200]
        inf = infos()
        if len([i for i in inf if i['type_id'] == 'Actor|DestroyActor']) == 0:
            mac = [i for i in inf if 'MacroInstance' in json.dumps(i.get('node', i))[:400] or i['type_id'].find('IsValid') >= 0]
            out['mac'] = [(m['type_id'], [p['name'] for p in m['output_pins']]) for m in mac][:3]
            if len(mac) == 1:
                m = mac[0]
                nv = [p for p in m['output_pins'] if p['name'] == 'Is Not Valid']
                pos = {'x': m['position']['x'] + 300, 'y': m['position']['y'] + 260}
                ok, r = T(BT + 'create_node', {'graph': G, 'type_id': 'Actor|DestroyActor', 'pos': pos})
                LOG.append('create ' + str(ok))
                inf2 = infos()
                da = [i for i in inf2 if i['type_id'] == 'Actor|DestroyActor']
                if len(da) == 1 and nv:
                    ex = [p for p in da[0]['input_pins'] if p['name'] in ('execute', 'exec', '')]
                    out['da_in'] = [p['name'] for p in da[0]['input_pins']]
                    if ex:
                        ok, _ = T(BT + 'connect_pins', {'output_pin': nv[0]['pin_id'], 'input_pin': ex[0]['pin_id']})
                        LOG.append('connect ' + str(ok))
        else:
            LOG.append('ya tenia DestroyActor')
        ok, r = T(BT + 'compile_blueprint', {'blueprint': {'refPath': AU + '.BP_AlmaAura_SC'}})
        out['aura_compile'] = str(r)[:200]
        ok, d = T(BT + 'read_graph_dsl', {'graph': G})
        out['aura_dsl'] = str(d)[-500:]
        out['save'] = T(AS + 'save_assets', {'asset_paths': [RUN, AU]})[0]
    except BaseException as e:
        ERRS.append('run :: ' + str(e)[:300])
    out['log'] = LOG
    out['errs'] = ERRS
    return out
