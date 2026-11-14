"""Analiza un CSV del PiEEG XR (timestamp, ch1..ch8 en µV crudos) y dibuja un PNG al lado.

Uso (con el Python del sistema, que tiene numpy, scipy y matplotlib):
    python tools/pieeg/analizar_pieeg.py                      # el CSV más nuevo de ~/pieeg-datos
    python tools/pieeg/analizar_pieeg.py ruta/al/archivo.csv

Por canal: señal filtrada 1-40 Hz (desviación y pico a pico), zumbido de la red (50 y 60 Hz)
contra la señal útil, y las bandas EEG relativas. El PNG muestra las 8 ondas y sus espectros.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, welch

FS = 250.0
LUGAR = ["sien izq. abajo", "sien izq. arriba", "frente izq.", "frente izq.",
         "frente der.", "frente der.", "sien der. arriba", "sien der. abajo"]
BANDAS = {"delta": (1, 4), "theta": (4, 8), "alfa": (8, 13), "beta": (13, 30)}


def cargar(ruta):
    datos = np.genfromtxt(ruta, delimiter=",", names=True)
    canales = [n for n in datos.dtype.names if n.startswith("ch")]
    return datos["timestamp"], np.vstack([datos[c] for c in canales])


def potencia(f, p, a, b):
    m = (f >= a) & (f < b)
    integrar = getattr(np, "trapezoid", None) or np.trapz   # numpy < 2.0 solo tiene trapz
    return integrar(p[m], f[m]) if m.any() else 0.0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
    else:
        ruta = max((Path.home() / "pieeg-datos").glob("*.csv"), key=lambda p: p.stat().st_mtime)
    t, x = cargar(ruta)
    print(f"{ruta.name}: {x.shape[1]} muestras, {t[-1] - t[0]:.1f} s")

    b, a = butter(4, [1, 40], btype="band", fs=FS)
    filt = filtfilt(b, a, x - x.mean(axis=1, keepdims=True), axis=1)
    bn, an = iirnotch(50, 30, fs=FS)
    borde = int(FS)   # el filtro deja un transitorio en el primer y el último segundo: se descarta
    limpio = filtfilt(bn, an, filt, axis=1)[:, borde:-borde]
    x = x[:, borde:-borde]
    f, psd = welch(x - x.mean(axis=1, keepdims=True), fs=FS, nperseg=512, axis=1)

    print(f"\n{'canal':<6}{'lugar':<18}{'desv 1-40':>10}{'pp 1-40':>9}{'red 50Hz':>10}{'red 60Hz':>10}"
          f"{'red/útil':>9}   delta theta  alfa  beta")
    for c in range(x.shape[0]):
        util = potencia(f, psd[c], 1, 40)
        r50, r60 = potencia(f, psd[c], 48, 52), potencia(f, psd[c], 58, 62)
        bandas = np.array([potencia(f, psd[c], *v) for v in BANDAS.values()])
        rel = bandas / bandas.sum() if bandas.sum() else bandas
        pp = np.percentile(limpio[c], 99.5) - np.percentile(limpio[c], 0.5)
        print(f"Ch{c + 1:<4}{LUGAR[c]:<18}{limpio[c].std():>10.1f}{pp:>9.0f}{np.sqrt(r50):>10.1f}"
              f"{np.sqrt(r60):>10.1f}{max(r50, r60) / util if util else 0:>9.2f}   "
              + "  ".join(f"{v:>4.0%}" for v in rel))
    print("\ndesv y pp en µV, sin red (notch 50 Hz). red = amplitud RMS del zumbido."
          " red/útil > 1: la red eléctrica le gana a la señal.")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8), gridspec_kw={"width_ratios": [3, 1]})
    tt = np.arange(x.shape[1]) / FS
    paso = max(150.0, np.percentile(np.abs(limpio), 99) * 2.2)
    for c in range(x.shape[0]):
        ax1.plot(tt, limpio[c] - c * paso, lw=0.6)
        ax1.text(tt[0] - 0.3, -c * paso, f"Ch{c + 1}", ha="right", va="center", fontsize=9)
        ax2.semilogy(f, psd[c], lw=0.8, label=f"Ch{c + 1}")
    ax1.set_title(f"{ruta.name}: 1-40 Hz + notch 50 Hz (separación {paso:.0f} µV)")
    ax1.set_xlabel("s")
    ax1.set_yticks([])
    ax2.set_title("espectro crudo (µV²/Hz)")
    ax2.set_xlabel("Hz")
    ax2.set_xlim(0, 70)
    for fr in (50, 60):
        ax2.axvline(fr, color="gray", ls=":", lw=0.8)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    png = ruta.with_suffix(".png")
    fig.savefig(png, dpi=110)
    print(f"PNG: {png}")


if __name__ == "__main__":
    main()
