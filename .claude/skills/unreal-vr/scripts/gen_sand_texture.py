# -*- coding: utf-8 -*-
"""gen_sand_texture.py - textura de ARENA fina para M_ChladniFloor_SC (reemplaza las motas calculadas).

Beltran (2026-09-28): "la textura es muy matematica, debe ser mas como arena, no como motas" (referencia: foto de
arena de playa de grano fino). Una arena real es ruido a VARIAS escalas: el grano (1 texel), grupos de granos, y
manchas suaves; mas unos pocos granos oscuros y claros sueltos. Horneada con mipmaps: de lejos el motor promedia solo,
sin parpadeo y sin cuentas por pixel.

Canales (lineal, sin sRGB):  R = arena (media 0,5)   G = granos oscuros sueltos (0..1)   B = granos claros sueltos (0..1)
PERIODICA (el desenfoque es por FFT, que envuelve), asi que tesela sin costura. En el material: uv = p / GrainSize (cm).

Uso:  python gen_sand_texture.py   -> VR_Test/Saved/ClaudeScripts/T_SandGrain_SC.png (1024, RGB 8 bits)
"""
import os
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
SALIDA = os.path.join(REPO, "VR_Test", "Saved", "ClaudeScripts", "T_SandGrain_SC.png")
N = 1024
rng = np.random.default_rng(11)
f = np.fft.fftfreq(N)
FX, FY = np.meshgrid(f, f)
F2 = FX * FX + FY * FY


def blur(a, sigma):
    """desenfoque gaussiano PERIODICO (en frecuencia)"""
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * F2)))


def norm(a):
    return (a - a.mean()) / (a.std() + 1e-9)


def granos(cantidad, rmin, rmax):
    """granos sueltos: discos suaves de radio al azar (periodicos)"""
    m = np.zeros((N, N))
    ys, xs = rng.integers(0, N, cantidad), rng.integers(0, N, cantidad)
    rs = rng.uniform(rmin, rmax, cantidad)
    yy, xx = np.mgrid[-4:5, -4:5]
    for y, x, r in zip(ys, xs, rs):
        d = np.sqrt(xx * xx + yy * yy)
        g = np.clip(1.0 - (d - r) / 0.8, 0.0, 1.0) * rng.uniform(0.5, 1.0)
        m[np.ix_((y + np.arange(-4, 5)) % N, (x + np.arange(-4, 5)) % N)] = np.maximum(m[np.ix_((y + np.arange(-4, 5)) % N, (x + np.arange(-4, 5)) % N)], g)
    return m


def main():
    fino = norm(blur(rng.standard_normal((N, N)), 0.55))      # el grano: casi un texel
    grupos = norm(blur(rng.standard_normal((N, N)), 1.8))     # grupos de granos
    medio = norm(blur(rng.standard_normal((N, N)), 7.0))      # irregularidad
    ancho = norm(blur(rng.standard_normal((N, N)), 45.0))     # manchas muy suaves
    arena = 0.55 * fino + 0.3 * grupos + 0.18 * medio + 0.12 * ancho
    R = np.clip(0.5 + 0.13 * norm(arena), 0.0, 1.0)
    G = granos(2600, 0.4, 1.6)                                 # granos oscuros sueltos
    B = granos(1800, 0.3, 1.1)                                 # granos claros (brillo de cuarzo)
    img = np.stack([R, G, B], -1)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    Image.fromarray(np.round(img * 255).astype(np.uint8), "RGB").save(SALIDA)
    print("escrito %s  R media %.3f desvio %.3f | G cubre %.1f%% | B cubre %.1f%%" % (SALIDA, R.mean(), R.std(), (G > 0.3).mean() * 100, (B > 0.3).mean() * 100))


if __name__ == "__main__":
    main()
