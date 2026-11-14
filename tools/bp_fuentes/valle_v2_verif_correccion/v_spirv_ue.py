# v_spirv_ue.py - compila los envoltorios de v_compila.py con el dxcompiler.dll de UE 5.8 (ShaderConductor),
# llamado por COM (IDxcCompiler3) desde ctypes, con -spirv (el camino Vulkan de la Quest), y valida con spirv-val.
# El dxc.exe del SDK no trae el generador SPIR-V; el dll de UE si.
import ctypes, os, re, subprocess, sys, uuid
from ctypes import wintypes
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TMP = AQUI / "compila"
DLL = r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\ShaderConductor\Win64\dxcompiler.dll"
NDK = os.path.join(os.environ["LOCALAPPDATA"], r"Android\Sdk\ndk\27.2.12479018\shader-tools\windows-x86_64")
os.add_dll_directory(os.path.dirname(DLL))
dxc = ctypes.WinDLL(DLL)


class GUID(ctypes.Structure):
    _fields_ = [("d", ctypes.c_ubyte * 16)]

    @staticmethod
    def of(s):
        g = GUID()
        ctypes.memmove(g.d, uuid.UUID(s).bytes_le, 16)
        return g


class DxcBuffer(ctypes.Structure):
    _fields_ = [("Ptr", ctypes.c_void_p), ("Size", ctypes.c_size_t), ("Encoding", ctypes.c_uint)]


CLSID_DxcCompiler = GUID.of("73e22d93-e6ce-47f3-b5bf-f0664f39c1b0")
IID_IDxcCompiler3 = GUID.of("228B4687-5A6A-4730-900C-9702B2203F54")
IID_IDxcResult = GUID.of("58346CDA-DDE7-4497-9461-6F87AF5E0659")


def vcall(obj, idx, restype, *argtypes):
    vt = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vt[idx])


comp = ctypes.c_void_p()
hr = dxc.DxcCreateInstance(ctypes.byref(CLSID_DxcCompiler), ctypes.byref(IID_IDxcCompiler3), ctypes.byref(comp))
assert hr == 0, hex(hr & 0xFFFFFFFF)


def blob_bytes(b):
    ptr = vcall(b, 3, ctypes.c_void_p)(b)
    n = vcall(b, 4, ctypes.c_size_t)(b)
    return ctypes.string_at(ptr, n) if ptr and n else b""


def compile_(src_text, args):
    data = src_text.encode("utf-8")
    buf = DxcBuffer(ctypes.cast(ctypes.c_char_p(data), ctypes.c_void_p), len(data), 65001)
    arr = (ctypes.c_wchar_p * len(args))(*args)
    res = ctypes.c_void_p()
    f = vcall(comp, 3, ctypes.HRESULT if False else ctypes.c_long, ctypes.POINTER(DxcBuffer), ctypes.POINTER(ctypes.c_wchar_p),
              ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))
    hr = f(comp, ctypes.byref(buf), arr, len(args), None, ctypes.byref(IID_IDxcResult), ctypes.byref(res))
    assert hr == 0, hex(hr & 0xFFFFFFFF)
    st = ctypes.c_long()
    vcall(res, 3, ctypes.c_long, ctypes.POINTER(ctypes.c_long))(res, ctypes.byref(st))
    eb = ctypes.c_void_p()
    vcall(res, 5, ctypes.c_long, ctypes.POINTER(ctypes.c_void_p))(res, ctypes.byref(eb))
    err = blob_bytes(eb).decode("utf-8", "replace") if eb else ""
    ob = ctypes.c_void_p()
    vcall(res, 4, ctypes.c_long, ctypes.POINTER(ctypes.c_void_p))(res, ctypes.byref(ob))
    obj = blob_bytes(ob) if ob else b""
    return st.value, err, obj


fallas = 0
for name, kind in (("ValleyHeightVS", "vs"), ("ValleyGradVS", "vs"), ("ValleyPS", "ps")):
    src = (TMP / ("ue_%s.hlsl" % name)).read_text(encoding="ascii")
    for hv in ("2018", "2021"):
        args = ["-T", kind + "_6_0", "-E", "main", "-HV", hv, "-WX", "-O3", "-spirv", "-fspv-target-env=vulkan1.1"]
        st, err, obj = compile_(src, args)
        ok = st == 0 and len(obj) > 0
        spv = TMP / ("%s_ue_%s.spv" % (name, hv))
        msg = err.strip()[-600:]
        if ok:
            spv.write_bytes(obj)
            p = subprocess.run([os.path.join(NDK, "spirv-val.exe"), "--target-env", "vulkan1.1", str(spv)], capture_output=True, text=True)
            ok = p.returncode == 0
            msg = (p.stdout + p.stderr).strip()[-600:]
            if ok:
                d = subprocess.run([os.path.join(NDK, "spirv-dis.exe"), str(spv)], capture_output=True, text=True).stdout
                (TMP / ("%s_ue_%s.spvasm" % (name, hv))).write_text(d, encoding="utf-8")
                msg = "OpTypeArray=%d OpLoopMerge=%d RelaxedPrecision=%d bytes=%d" % (
                    len(re.findall(r"OpTypeArray", d)), len(re.findall(r"OpLoopMerge", d)),
                    len(re.findall(r"RelaxedPrecision", d)), len(obj))
        print(("OK    " if ok else "FALLA ") + "UE5.8 dxcompiler -spirv vulkan1.1 %s_6_0 HV%s -WX + spirv-val  %s  %s" % (kind, hv, name, msg))
        fallas += not ok
print("RESULTADO SPIR-V UE: " + ("TODO OK" if not fallas else "%d FALLAS" % fallas))
