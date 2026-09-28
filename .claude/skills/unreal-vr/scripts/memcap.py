# memcap.py - corre un script de Python con TOPE DE MEMORIA (Job Object de Windows, 2 GB) - gotcha 492.
# Uso:  python memcap.py <script.py> [args...]   (el codigo de salida es el del script)
import ctypes, subprocess, sys
from ctypes import wintypes
k = ctypes.WinDLL("kernel32", use_last_error=True)
class IO(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("r","w","o","rt","wt","ot")]
class BASIC(ctypes.Structure):
    _fields_ = [("a", ctypes.c_longlong), ("b", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD),
                ("mn", ctypes.c_size_t), ("mx", ctypes.c_size_t), ("ac", wintypes.DWORD),
                ("aff", ctypes.c_size_t), ("pc", wintypes.DWORD), ("sc", wintypes.DWORD)]
class EXT(ctypes.Structure):
    _fields_ = [("B", BASIC), ("IO", IO), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("p1", ctypes.c_size_t), ("p2", ctypes.c_size_t)]
class MS(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] +                [(n, ctypes.c_ulonglong) for n in ("tp", "ap", "tpf", "apf", "tv", "av", "aev")]
ms = MS(); ms.dwLength = ctypes.sizeof(MS)
k.GlobalMemoryStatusEx(ctypes.byref(ms))
if ms.ap < (8 << 30):   # pedido de Narrativa (2026-09-29): con el editor compartido, no arrancar con < 8 GB libres
    sys.exit("memcap: el sistema tiene %.1f GB libres (< 8): no arranco" % (ms.ap / 2**30))
job = k.CreateJobObjectW(None, None)
info = EXT(); info.B.LimitFlags = 0x100 | 0x2000; info.ProcessMemoryLimit = 2 << 30
k.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
p = subprocess.Popen([sys.executable, "-u"] + sys.argv[1:])
h = k.OpenProcess(0x1F0FFF, False, p.pid); k.AssignProcessToJobObject(job, h)
sys.exit(p.wait())
