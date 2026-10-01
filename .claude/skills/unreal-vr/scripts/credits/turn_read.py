import json
# turn_read.py (2026-10-01) - SOLO LECTURA (read_graph_dsl ensucia el BP, gotcha 553; igual se guardan los dos al final).
# 1) BP_SaveMelody_SC: todos sus grafos en DSL a Saved/ClaudeScripts/credits/save_dsl.txt (se busca 'Label' afuera) y el
#    estado del componente Label en el CDO.
# 2) BP_Credits_SC: variables, grafos, nodos del EventGraph (para la cirugia) y el EventGraph en DSL.
# 3) Nivel abierto (tiene que ser L_SoulCharger_Obra, NO se guarda): estrellas CreditStar (nombre, escala, oculta) y el
#    actor de creditos.
# Se pega ENTERO. Nunca levanta excepcion (sin dict.get con default: gotcha 572).
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
SC = 'editor_toolset.toolsets.scene.SceneTools.'
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/credits/'
SAVE = '/Game/SoulCharger/Core/Attracting/BP_SaveMelody_SC.BP_SaveMelody_SC'
SAVE_CDO = '/Game/SoulCharger/Core/Attracting/BP_SaveMelody_SC.Default__BP_SaveMelody_SC_C'
LOG = []


def T(n, p):
    try:
        r = execute_tool(n, json.dumps(p))
        return True, (r['returnValue'] if isinstance(r, dict) and ('returnValue' in r) else r)
    except BaseException as e:
        LOG.append(n.split('.')[-1] + ' :: ' + str(e)[:150])
        return False, None


def refp(x):
    return str(x['refPath'] if isinstance(x, dict) and ('refPath' in x) else x)


def run():
    out = {}
    try:
        ok, lvl = T(SC + 'get_current_level', {})
        out['nivel'] = lvl
        # 1) SAVE
        ok, gs = T(BT + 'list_graphs', {'blueprint': SAVE})
        txt = []
        for g in (gs or []):
            r = refp(g)
            ok, d = T(BT + 'read_graph_dsl', {'graph': {'refPath': r}})
            txt.append(';;==== ' + r.split(':')[-1] + '\n' + str(d))
        T(AS + 'write_file', {'file_path': OUT + 'save_dsl.txt', 'content': '\n'.join(txt)})
        out['save_grafos'] = len(gs or [])
        ok, cs = T(AT + 'get_components', {'actor': {'refPath': SAVE_CDO}})
        for c in (cs or []):
            r = refp(c)
            if 'Label' in r.split('.')[-1]:
                ok, v = T(OT + 'get_properties', {'instance': {'refPath': r}, 'properties': ['Text', 'bHiddenInGame', 'bVisible', 'WorldSize', 'TextRenderColor', 'RelativeScale3D']})
                out['label'] = {'ref': r, 'props': str(v)[:400]}
        # 2) CREDITS
        ok, fa = T(AS + 'find_assets', {'folder_path': '/Game/SoulCharger', 'name': 'BP_Credits_SC'})
        cred = None
        for a in (fa or []):
            p = refp(a).split('.')[0]
            if p.endswith('/BP_Credits_SC'):
                cred = p + '.BP_Credits_SC'
        out['credits_bp'] = cred
        if cred:
            ok, vs = T(BT + 'list_variables', {'blueprint': cred})
            out['credits_vars'] = str(vs)[:900]
            ok, gs = T(BT + 'list_graphs', {'blueprint': cred})
            out['credits_grafos'] = [refp(g).split(':')[-1] for g in (gs or [])]
            eg = cred + ':EventGraph'
            ok, ns = T(BT + 'find_nodes', {'graph': {'refPath': eg}, 'title': ''})
            out['eventgraph_nodos'] = [refp(n).split('.')[-1] for n in (ns or [])]
            ok, d = T(BT + 'read_graph_dsl', {'graph': {'refPath': eg}})
            out['eventgraph_dsl'] = str(d)[:600]
            ids = {}
            for f in ('Transformation|GetActorScale3D', 'Transformation|SetActorScale3D', 'Actor|GetAllActorswithTag'):
                ok, v = T(BT + 'find_node_types', {'graph': {'refPath': eg}, 'type_id_filter': f, 'context_pins': []})
                got = [(x['type_id'] if isinstance(x, dict) and ('type_id' in x) else str(x)) for x in (v or [])]
                ids[f] = 'OK' if f in got else got[:5]
            out['ids'] = ids
        # 3) estrellas y creditos en el nivel
        ok, st = T(SC + 'find_actors', {'name': '', 'tag': 'CreditStar', 'collision_channels': []})
        stars = []
        for a in (st or []):
            r = refp(a)
            ok, xf = T(AT + 'get_actor_transform', {'actor': {'refPath': r}})
            try:
                s = xf['scale']
                stars.append([r.split('.')[-1], round(s['x'], 3), round(s['y'], 3), round(s['z'], 3)])
            except BaseException:
                stars.append([r.split('.')[-1], str(xf)[:80]])
        out['estrellas'] = {'n': len(stars), 'primeras': stars[:6]}
        out['estrella_ref0'] = refp(st[0]) if st else None
        ok, ca = T(SC + 'find_actors', {'name': 'Final_Creditos', 'tag': '', 'collision_channels': []})
        out['creditos_actor'] = [refp(a) for a in (ca or [])][:3]
    except BaseException as e:
        out['err'] = str(e)[:200]
    out['log'] = LOG[:10]
    return out
