"""gen_partitura_doc.py - escribe docs/PARTITURA.md desde partitura_def.py (la lista de perillas de tiempo).

  python tools/unreal/gen_partitura_doc.py

Los valores que muestra son los de CREACION del asset. El valor vigente es el de DA_Partitura_Obra en el
editor: si alguien lo cambio alli, este documento muestra el original (la columna dice "valor inicial").
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from partitura_def import P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
out = []
out.append("# Partitura de la Obra · `DA_Partitura_Obra`")
out.append("")
out.append("> Generado por `tools/unreal/gen_partitura_doc.py` desde `tools/unreal/partitura_def.py`. No editar a mano.")
out.append("")
out.append("**Qué es:** el único lugar donde viven los tiempos narrativos de la Obra (cuándo entra Alma, cuánto duran")
out.append("las instrucciones, cuándo se le pide a una etapa que cierre, el final, los créditos...). La Obra")
out.append("(`BP_Obra_SC`) y los ensayos de cada etapa (`BP_StageRunner_SC`) la leen al arrancar.")
out.append("")
out.append("**Cómo se ajusta:** en el editor, abrir `/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra` (doble clic),")
out.append("cambiar el número, **guardar**. No hace falta tocar ningún Blueprint. Después: `python tools/unreal/smoke_obra.py`")
out.append("y probar en el visor. Las variables de la categoría *Partitura* dentro de `BP_Obra_SC` son **copias de trabajo**:")
out.append("se pisan al arrancar con lo que dice el DA. No se editan.")
out.append("")
out.append("**Unidades:** segundos del reloj del director. `PT` = tiempo dentro de la fase actual; `T` = tiempo de la etapa")
out.append("(en la fase 0 el reloj de la etapa salta a 9 cuando entra Alma). Las perillas *por etapa* son 5 números en orden:")
out.append("Entering, Recognizing, Loving, Attracting, Surrounding.")
out.append("")
cat = None
for (n, t, v, c, d) in P:
    if c != cat:
        cat = c
        out.append("## %s" % c)
        out.append("")
        out.append("| Perilla | Valor inicial | Qué hace |")
        out.append("|---|---|---|")
    vs = ("[" + ", ".join(("%g" % x).replace(".", ",") for x in v) + "]") if isinstance(v, list) else ("%g" % v).replace(".", ",")
    out.append("| `%s` | %s | %s |" % (n, vs, d))
    nxt = P[P.index((n, t, v, c, d)) + 1][3] if P.index((n, t, v, c, d)) + 1 < len(P) else None
    if nxt != c:
        out.append("")
out.append("## Lo que NO está en la Partitura (y dónde vive)")
out.append("")
out.append("- **Dónde pasa cada cosa** (Alma, la carga, el título de cada etapa): los TargetPoints `sc<K>_alma_in`, `sc<K>_alma_side`,")
out.append("  `sc<K>_charge`, `sc<K>_title` en el nivel de test de cada etapa. Se mueven en el viewport.")
out.append("- **El color del velo de cada etapa** (`CTop`/`CHor`): en el `BP_StageRunner_SC` del nivel de test de la etapa.")
out.append("- **Cómo se ve y se siente cada mecánica**: sus perillas, en su Blueprint o en la instancia de su nivel de test. Ver `docs/PERILLAS.md`.")
out.append("- **Coreografías internas** (la carga del anillo, el nado del alma en SHARE, la presentación del dibujo): sus Blueprints.")
out.append("- **Tiempos acoplados a la animación de la carga final** (`ReadCharge` 5,6 + carga, `FlowVeil` 5,5 + carga): quedan en el grafo,")
out.append("  pero ya son relativos a `Carga_Dur[4]`: si se cambia la carga final, se mueven solos.")
out.append("")
open(os.path.join(ROOT, "docs", "PARTITURA.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("docs/PARTITURA.md: %d perillas" % len(P))
