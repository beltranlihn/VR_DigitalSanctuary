import json
# hall_wave_capture.py - CONTROL POSITIVO de la onda: pone la cámara del editor DENTRO del Hall (mirando la puerta Este y la
# bóveda) y guarda la captura en base64 a caps/cap_<NAME>.txt. Solo cámara + captura + write_file (nada del nivel).
# NAME: 'base' (antes del empalme) · 'g2000' (después, MPC GrooveFront 2000) · 'g0' (MPC GrooveFront 0). Sin `result = run()`.
NAME = 'base'
EA = 'EditorToolset.EditorAppToolset.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/Hall/caps/'
def run():
  try:
    xf = {'location': {'x': -300.0, 'y': 0.0, 'z': 170.0}, 'rotation': {'pitch': 18.0, 'yaw': 0.0, 'roll': 0.0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}
    execute_tool(EA + 'SetCameraTransform', json.dumps({'transform': xf}))
    r = execute_tool(EA + 'CaptureViewport', json.dumps({'captureTransform': xf, 'annotations': [], 'bShowUI': False}))['returnValue']
    s = json.dumps(r) if not isinstance(r, str) else r
    execute_tool(AS + 'write_file', json.dumps({'file_path': OUT + 'cap_' + NAME + '.txt', 'content': s}))
    return {'name': NAME, 'len': len(s)}
  except BaseException as e:
    return {'err': str(e)[:300]}
