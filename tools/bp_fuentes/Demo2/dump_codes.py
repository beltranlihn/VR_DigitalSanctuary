# dump_codes.py <modulo> <bp_refpath> [graphs,...] -> <modulo>_codes.json, lo lee el escritor generico dentro de Unreal
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
only = sys.argv[3].split(',') if len(sys.argv) > 3 else None
order = [g for g in m.ORDER if not only or g in only]
d = {'bp': sys.argv[2], 'order': order, 'codes': {g: m.CODES[g] for g in order}, 'evg': getattr(m, 'EVG', '') if (not only or 'EventGraph' in only) else ''}
json.dump(d, open(sys.argv[1] + '_codes.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('ok', order, 'evg' if d['evg'] else '')
