# gen_save_melody_text.py - la mascara del texto del boton SAVE MELODY (T_SaveMelody_Text.png), con el Python del
# sistema (PIL). Lee las medidas y text_texture() de gen_save_melody.py sin ejecutar Blender.
# Uso: python gen_save_melody_text.py <dir_salida>
import ast
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
src = ast.parse(open(os.path.join(AQUI, "gen_save_melody.py"), encoding="utf-8").read())
keep = [n for n in src.body if (isinstance(n, ast.Assign) and all(isinstance(t, (ast.Name, ast.Tuple)) for t in n.targets)
        and not any(getattr(t, "id", "") in ("argv", "OUT") for t in n.targets)) or (isinstance(n, ast.FunctionDef) and n.name == "text_texture")]
ns = {"math": math}
exec(compile(ast.Module(body=keep, type_ignores=[]), "gen", "exec"), ns)
out = sys.argv[1] if len(sys.argv) > 1 else "."
print("TEXTO_OK", ns["text_texture"](os.path.join(out, "T_SaveMelody_Text.png")))
