# dump_ic.py - vuelca los grafos de los DSL de Inner Canvas a codes_<bp>.json para el escritor (write_ic.py, dentro de Unreal).
#   python dump_ic.py                 -> todos
#   python dump_ic.py kit kb          -> solo esos modulos
#   python dump_ic.py flow:FBoot,FVeil -> solo esas funciones (sin EventGraph salvo que se nombre)
import importlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MODS = {'tutor2': ('ic_tutor2_dsl', 'BP_ICTutor_IC'), 'flow': ('ic_flow_dsl', 'BP_ICFlow_IC'), 'kit': ('ic_kit_dsl', 'BP_ICHudKit_IC'), 'kb': ('ic_kb_dsl', 'BP_ICKeyboard_IC'),
        'link': ('ic_link_dsl', 'BP_ICLink_IC'), 'space': ('ic_space_dsl', 'BP_ICSpace_IC'), 'wall': ('ic_wall_dsl', 'BP_ICWall_IC'), 'hud': ('ic_hud_dsl', 'BP_ICWallHUD_IC'), 'tutor': ('ic_tutor_dsl', 'BP_ICTutor_IC'), 'flow2': ('ic_flow2_dsl', 'BP_ICFlow_IC')}
args = sys.argv[1:] or list(MODS)
for a in args:
    key, _, only = a.partition(':')
    mod, bp = MODS[key]
    m = importlib.import_module(mod)
    sel = only.split(',') if only else None
    order = [g for g in m.ORDER if not sel or g in sel]
    d = {'bp': '/Game/InnerCanvas/Blueprints/%s.%s' % (bp, bp), 'order': order, 'codes': {g: m.CODES[g] for g in order},
         'evg': m.EVG if (not sel or 'EventGraph' in sel) else '', 'evg2': getattr(m, 'EVG2', '') if (not sel or 'EventGraph' in sel) else ''}
    out = os.path.join(HERE, 'codes_%s.json' % key)
    json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok', key, len(order), 'evg' if d['evg'] else '')
