#!/usr/bin/env python3
# Genera 3 matcaps 256x256 como PNG puro (sin PIL/numpy).
# Un matcap se muestrea por la normal en espacio de vista -> el centro de la imagen
# es la cara mirando a camara, los bordes son el rasante. Construimos: color base,
# highlight desplazado hacia arriba, y luz de borde (rim).
import struct, zlib, math, os

SIZE = 256
OUT = os.path.dirname(os.path.abspath(__file__))

def clamp01(x): return 0.0 if x < 0 else (1.0 if x > 1 else x)

def gauss(u, v, cx, cy, s):
    d2 = (u-cx)**2 + (v-cy)**2
    return math.exp(-d2/(2*s*s))

def lerp(a,b,t): return a+(b-a)*t
def mix3(c1,c2,t): return tuple(lerp(c1[i],c2[i],t) for i in range(3))

def build(base, hi_col, hi_pos, hi_size, hi_str, rim_col, rim_str, rim_pow, edge_col, curve):
    """Devuelve una funcion pixel(u,v)->(r,g,b) 0..1. u,v en [-1,1]."""
    def px(u, v):
        r = math.sqrt(u*u+v*v)
        if r > 1.0:
            # fuera del disco: color de borde plano (nunca se muestrea de todos modos)
            return edge_col
        # sombreado esferico base: se oscurece hacia el rasante
        shade = clamp01(1.0 - curve*(r**1.6))
        col = tuple(base[i]*shade for i in range(3))
        # highlight especular desplazado arriba
        h = gauss(u, v, hi_pos[0], hi_pos[1], hi_size) * hi_str
        col = tuple(clamp01(col[i] + hi_col[i]*h) for i in range(3))
        # luz de borde (rim): crece cerca de r=1
        rim = (clamp01((r-0.6)/0.4))**rim_pow * rim_str
        col = tuple(clamp01(col[i] + rim_col[i]*rim) for i in range(3))
        return tuple(clamp01(c) for c in col)
    return px

# 01 - PERLA: suave, nacar frio-calido, highlight amplio arriba, rim tenue
pearl = build(
    base=(0.62,0.64,0.72), hi_col=(0.40,0.40,0.45), hi_pos=(0.0,0.45), hi_size=0.55,
    hi_str=0.9, rim_col=(0.30,0.32,0.42), rim_str=0.5, rim_pow=2.2,
    edge_col=(0.10,0.11,0.16), curve=0.55)

# 02 - VIDRIO FRIO: base azul oscura, highlight chico y nitido, rim ciano fuerte
glass = build(
    base=(0.04,0.10,0.20), hi_col=(0.55,0.80,1.0), hi_pos=(-0.22,0.32), hi_size=0.16,
    hi_str=1.0, rim_col=(0.25,0.60,0.95), rim_str=0.95, rim_pow=3.0,
    edge_col=(0.01,0.02,0.05), curve=0.85)

# 03 - SEDA CALIDA: ambar, highlight amplio suave, sheen satinado, rim calido
silk = build(
    base=(0.34,0.20,0.09), hi_col=(0.55,0.45,0.28), hi_pos=(0.0,0.28), hi_size=0.6,
    hi_str=0.85, rim_col=(0.45,0.28,0.12), rim_str=0.6, rim_pow=2.4,
    edge_col=(0.06,0.035,0.015), curve=0.6)

def write_png(path, pxfunc):
    raw = bytearray()
    for j in range(SIZE):
        raw.append(0)  # filter type 0
        v = (j/(SIZE-1))*2.0 - 1.0
        v = -v  # y hacia arriba
        for i in range(SIZE):
            u = (i/(SIZE-1))*2.0 - 1.0
            r,g,b = pxfunc(u, v)
            raw.append(int(round(clamp01(r)*255)))
            raw.append(int(round(clamp01(g)*255)))
            raw.append(int(round(clamp01(b)*255)))
    def chunk(typ, data):
        c = struct.pack('>I', len(data)) + typ + data
        c += struct.pack('>I', zlib.crc32(typ+data) & 0xffffffff)
        return c
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', SIZE, SIZE, 8, 2, 0, 0, 0)  # 8bit RGB
    idat = zlib.compress(bytes(raw), 9)
    with open(path,'wb') as f:
        f.write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))
    print("wrote", path)

write_png(os.path.join(OUT,'T_Matcap_01.png'), pearl)
write_png(os.path.join(OUT,'T_Matcap_02.png'), glass)
write_png(os.path.join(OUT,'T_Matcap_03.png'), silk)
print("done")
