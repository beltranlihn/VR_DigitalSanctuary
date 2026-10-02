"""mcp_config.py - asegura que el editor levante el servidor MCP al abrir (bAutoStartServer=True).

Los procesos -game (prueba de humo, probar_nivel) y el cocinado re-guardan EditorPerProjectUserSettings.ini y a veces
se llevan la clave: el editor abre sin MCP y Claude no lo puede manejar. Lo llaman smoke_obra.py, probar_nivel.py y
empaquetar_obra.py al terminar. A mano: python tools/unreal/mcp_config.py
"""
import os

USERINI = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "VR_Test", "Saved",
                                       "Config", "WindowsEditor", "EditorPerProjectUserSettings.ini"))
H = "[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]"


def asegurar_autostart():
    if not os.path.exists(USERINI):
        return False
    s = open(USERINI, encoding="utf-8", errors="surrogateescape").read()
    if H not in s:
        s = s.rstrip("\n") + "\n\n" + H + "\nbAutoStartServer=True\n"
    else:
        i = s.index(H) + len(H)
        j = s.find("\n[", i)
        end = j if j >= 0 else len(s)
        sec = s[i:end]
        if "bAutoStartServer=True" in sec:
            return False
        if "bAutoStartServer=False" in sec:
            sec = sec.replace("bAutoStartServer=False", "bAutoStartServer=True")
        else:
            sec = "\nbAutoStartServer=True" + sec
        s = s[:i] + sec + s[end:]
    open(USERINI, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("config del MCP restaurada (bAutoStartServer=True)")
    return True


if __name__ == "__main__":
    asegurar_autostart()
