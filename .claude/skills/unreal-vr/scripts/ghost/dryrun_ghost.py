# -*- coding: utf-8 -*-
"""dryrun_ghost.py - corre ghost_build.py / ghost_write.py / ghost_material.py / ghost_dump.py SIN Unreal, contra un
editor SIMULADO en memoria, dos veces cada uno (idempotencia). Atrapa errores de Python (KeyError, nombres, flujo)
antes del turno; NO prueba el comportamiento de Unreal (eso es el turno).

Simula las trampas conocidas que los scripts manejan:
  - set_properties de un Vector con JSON de campos escribe SOLO la primera componente (toolsets: transforms); el script
    tiene que detectarlo al releer y pasar al formato de texto.
  - un error del DSL ESCAPA del try (se simula con un write_graph_dsl que lanza para un grafo marcado).
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.normpath(os.path.join(AQUI, '..', '..', '..', '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'ghost'))


class DslError(Exception):
    pass


class Editor:
    def __init__(self, dsl_falla=None):
        self.assets = set()
        self.bps = {}      # B -> {'vars': {name: meta}, 'graphs': {name: nodes}}
        self.props = {}    # ref -> {prop: value}
        self.calls = []
        self.files = {}
        self.dsl_falla = dsl_falla
        self.mat = {'exprs': {}, 'n': 0, 'out': {}}

    def tool(self, name, payload):
        p = json.loads(payload)
        short = name.split('.')[-1]
        self.calls.append(short)
        f = getattr(self, 't_' + short, None)
        if f is None:
            raise RuntimeError('tool no simulada: ' + name)
        return {'returnValue': f(p)}

    # ---- AssetTools
    def t_exists(self, p):
        return p['path'] in self.assets

    def t_create_folder(self, p):
        return True

    def t_read_file(self, p):
        path = p['file_path']
        if not path.startswith('C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/'):
            raise RuntimeError('read_file fuera de Saved: ' + path)
        loc = os.path.join(SAVED, path.split('/ghost/')[-1])
        return io.open(loc, encoding='utf-8').read()

    def t_write_file(self, p):
        self.files[p['file_path']] = p['content']
        return True

    def t_save_assets(self, p):
        if not p['asset_paths']:
            raise RuntimeError('save_assets([]) guarda TODO: prohibido')
        return True

    # ---- BlueprintTools
    def t_create(self, p):
        path = p['folder_path'] + '/' + p['asset_name']
        self.assets.add(path)
        B = path + '.' + p['asset_name']
        self.bps[B] = {'vars': {}, 'graphs': {'EventGraph': 3 if 'Actor' in p['asset_type']['refPath'] else 1}}
        return {'refPath': B}

    def t_list_variables(self, p):
        return [{'name': n} for n in self.bps[p['blueprint']]['vars']]

    def t_add_variable(self, p):
        if p['type_name'] not in ('float', 'int', 'bool', 'string', 'name', 'Vector', 'Rotator', 'Transform', 'LinearColor'):
            raise RuntimeError('type_name raro ' + p['type_name'])
        self.bps[p['blueprint']]['vars'][p['name']] = dict(p)
        return True

    def t_add_object_variable(self, p):
        self.bps[p['blueprint']]['vars'][p['name']] = dict(p)
        return True

    def t_set_variable_category(self, p):
        assert p['variable_name'] in self.bps[p['blueprint']]['vars'], p
        return True

    def t_set_variable_instance_editable(self, p):
        assert p['variable_name'] in self.bps[p['blueprint']]['vars'], p
        return True

    def t_list_graphs(self, p):
        B = p['blueprint']
        return [{'refPath': B + ':' + g} for g in self.bps[B]['graphs']]

    def t_add_function_graph(self, p):
        self.bps[p['blueprint']]['graphs'][p['graph_name']] = 1
        return True

    def _g(self, g):
        B, name = g.split(':')
        return B, name

    def t_add_function_param(self, p):
        B, n = self._g(p['graph'])
        assert n in self.bps[B]['graphs'], p
        return True

    t_add_object_function_param = t_add_function_param
    t_add_struct_function_param = t_add_function_param

    def t_compile_blueprint(self, p):
        return None

    def t_find_nodes(self, p):
        B, n = self._g(p['graph'])
        k = self.bps[B]['graphs'][n]
        return [{'refPath': p['graph'] + '.K2Node_%d' % i} for i in range(k)]

    def t_delete_node(self, p):
        B, n = self._g(p['node']['refPath'].rsplit('.', 1)[0])
        self.bps[B]['graphs'][n] = max(0, self.bps[B]['graphs'][n] - 1)
        return True

    def t_write_graph_dsl(self, p):
        B, n = self._g(p['graph'])
        if n == self.dsl_falla:
            self.dsl_falla = None
            raise DslError('DSL: nodo inexistente en ' + n)
        self.bps[B]['graphs'][n] = self.bps[B]['graphs'][n] + 10
        return True

    # ---- ObjectTools
    def t_get_properties(self, p):
        ref = p['instance']['refPath']
        d = self.props.get(ref, {})
        out = {}
        for k in p['properties']:
            if k in d:
                out[k] = d[k]
        return json.dumps(out)

    def t_set_properties(self, p):
        ref = p['instance']['refPath']
        vals = json.loads(p['values'])
        d = self.props.setdefault(ref, {})
        for k, v in vals.items():
            d[k] = self._bug(v)
        return True

    def _bug(self, v):
        # la trampa: un dict x/y/z escribe solo x
        if isinstance(v, dict) and set(v.keys()) == {'x', 'y', 'z'}:
            return {'x': v['x'], 'y': 0.0, 'z': 0.0}
        if isinstance(v, list):
            return [self._bug(x) for x in v]
        if isinstance(v, str):
            m = re.match(r'\(X=([-\d.]+),Y=([-\d.]+),Z=([-\d.]+)\)', v)
            if m:
                return {'x': float(m.group(1)), 'y': float(m.group(2)), 'z': float(m.group(3))}
            m = re.match(r'\(R=([-\d.]+),G=([-\d.]+),B=([-\d.]+),A=([-\d.]+)\)', v)
            if m:
                return {'r': float(m.group(1)), 'g': float(m.group(2)), 'b': float(m.group(3)), 'a': float(m.group(4))}
        return v

    # ---- DataAssetTools
    def t_create_da(self, p):
        path = p['folder_path'] + '/' + p['asset_name']
        self.assets.add(path)
        return {'refPath': path + '.' + p['asset_name']}

    # ---- MaterialTools
    def t_create_material(self, p):
        self.assets.add(p['folder_path'] + '/' + p['asset_name'])
        return True

    def t_get_expressions(self, p):
        return [{'refPath': r} for r in self.mat['exprs']]

    def t_add_expression(self, p):
        self.mat['n'] += 1
        cls = p['expression_class']['refPath'].split('.')[-1]
        r = p['material_or_function']['refPath'] + ':' + cls + '_%d' % self.mat['n']
        self.mat['exprs'][r] = cls
        return {'refPath': r}

    def t_connect_expressions(self, p):
        assert p['from_expression']['refPath'] in self.mat['exprs'], p
        return True

    def t_connect_to_output(self, p):
        self.mat['out'][p['material_property']] = p['expression']['refPath']
        return True


def load(script):
    src = io.open(os.path.join(AQUI, script), encoding='utf-8').read()
    return src


def run_script(ed, script, subs=None):
    src = load(script)
    for a, b in (subs or {}).items():
        src = src.replace(a, b)
    g = {}

    def execute_tool(name, payload):
        if name.endswith('DataAssetTools.create'):
            return ed.tool(name.replace('.create', '.create_da'), payload)
        return ed.tool(name, payload)
    g['execute_tool'] = execute_tool
    exec(compile(src, script, 'exec'), g)
    try:
        return g['run']()
    except DslError as e:
        return {'ESCAPO': str(e)}


def main():
    ed = Editor(dsl_falla='GhPose')
    for parte in ('take', 'player', 'recorder'):
        for vez in (1, 2):
            r = run_script(ed, 'ghost_build.py', {"PARTE = 'take'": "PARTE = '%s'" % parte})
            print('build', parte, vez, {k: (v if k != 'log' else len(v)) for k, v in r.items() if k not in ('cdo_lectura',)})
    for cual in ('ghost_player', 'ghost_recorder'):
        for vez in (1, 2, 3):
            r = run_script(ed, 'ghost_write.py', {"CUAL = 'ghost_player'": "CUAL = '%s'" % cual})
            print('write', cual, vez, {k: (v if k not in ('hechos',) else len(v)) for k, v in r.items()})
    r = run_script(ed, 'ghost_material.py')
    print('material', r)
    r = run_script(ed, 'ghost_material.py')
    print('material 2', {k: v for k, v in r.items() if k != 'params'})
    # una toma simulada en un DA y el volcado
    ref = '/Game/SoulCharger/Mechanics/Ghost/Takes/DA_Ghost_Breath.DA_Ghost_Breath'
    ed.props[ref].update({'Frames': 240, 'Data': [0.0] * (240 * 28)})
    r = run_script(ed, 'ghost_dump.py')
    print('dump', {k: v for k, v in r.items() if k in ('DA_Ghost_Breath', 'DA_Ghost_Bell', 'guardados', 'rutas', 'log')})
    print('archivos', list(ed.files.keys()))


if __name__ == '__main__':
    main()
