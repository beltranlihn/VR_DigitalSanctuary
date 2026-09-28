# -*- coding: utf-8 -*-
"""make_vida_sounds.py - sintetiza los soplos de viento de la CAPA DE VIDA (Entering, 2026-09-28).

Cuatro one-shots MONO, 48 kHz, 16 bit (las fuentes espacializadas en Quest tienen que ser mono; audio-quest.md):
  SND_VidaGustA/B/C.wav   la rafaga LATERAL (GustLife = 28 s): se acerca desde un lado, pasa por el usuario y se va
                          al otro. El BP la hace viajar (la fuente va con el frente) y la estira con el pitch si
                          GustLife cambia (0,75-1,33). OJO: el pitch tambien cambia el TIMBRE (GustLife 36 -> pitch 0,78,
                          4 semitonos mas grave): si GustLife cambia mas de ~15 %, REGENERAR con la duracion nueva.
  SND_VidaSoplo.wav       el SOPLO (BreathLife = 18 s): nace con la exhalacion, pasa por el usuario en ~2,5 s y se
                          aleja hacia el horizonte (un solo aire). Rev. 2: SUENA AL MISMO TIEMPO que SND_PacerExhale
                          (un tono de 4 s, RMS -20,5 dBFS, 93 % de su energia en 150-500 Hz): el soplo va ARRIBA de esa
                          banda (el siseo del aire, 450-6000 Hz, casi nada debajo de 400 Hz) y ~8 dB mas fuerte que en la
                          rev. 1, para que no lo tape el pacer (ni se pierda en los parlantes de la Quest, que atenuan
                          debajo de ~200 Hz). Su pico cae a ~2,5 s, despues del ataque del tono del pacer.
La ENVOLVENTE sale del MISMO reloj que el polvo y la franja (vida_model): cerca = la actividad de la rafaga 2 m
delante del usuario (el frente pasando), lejos = la envolvente de la rafaga a lo largo del camino (la franja en el llano).
Cerca suena mas brillante (el pasto al lado: filtro abierto + un susurro fino), lejos mas oscuro (solo el cuerpo grave).
Soplos lentos adentro (dos moduladores de 0,4 y 1,3 Hz) para que no sea un ruido plano. Sin clics: arranca y termina en
silencio (la envolvente vale 0 en las puntas + fundidos coseno de 0,3 s) y sin DC (pasaaltos 30 Hz).
Nivel: la rafaga con pico -16 dBFS; el soplo NORMALIZADO por su RMS en los primeros 4 s (la ventana del tono de exhalar del
pacer) a -27 dBFS, con el pico tope en -9 dBFS. Los del pacer andan en -15/-17 dBFS de pico con RMS -20/-25. El volumen
final es la perilla GustVolume.

Uso:  python make_vida_sounds.py [carpeta]      (default VR_Test/Saved/ClaudeScripts/vida/audio)
      Ademas escribe sonidos_rafaga.png (envolventes y espectrogramas) y un informe (picos, RMS, clics, brillo).
"""
import math
import os
import struct
import sys
import wave

import numpy as np
from scipy import signal

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import vida_model as vm  # noqa: E402

SR = 48000


def envolventes(kind, life, rng):
    """(cerca, lejos) por muestra, del modelo: una rafaga con las perillas por defecto."""
    bp = vm.VidaBP()
    if kind == 0:
        bp.start_lateral(1.0)
    else:
        bp.start_breath()
    bp.q.update(GustLife=life, BreathLife=life)
    bp.Life = life
    bp.Sdot = (bp.S1 - bp.S0) / life
    n = int(life * SR)
    t = np.arange(n) / SR
    s = bp.S0 + bp.Sdot * t
    F = bp.actor.axes()[0]
    probe = (bp.actor.loc + F * vm.PROBE_FWD)[:2]
    cerca = np.empty(n)
    lejos = np.empty(n)
    paso = 480                       # se evalua cada 10 ms y se interpola (las funciones son suaves)
    idx = np.arange(0, n, paso)
    c = []
    l = []
    for i in idx:
        bp.S = s[i]
        g = bp.gust()
        c.append(vm.gust_act(probe, g))
        l.append(vm.gust_env(s[i], bp.E0, bp.E1, bp.Ramp))
    cerca[:] = np.interp(np.arange(n), idx, c)
    lejos[:] = np.interp(np.arange(n), idx, l)
    if kind == 1:
        # el soplo SE ALEJA (la fuente no tiene atenuacion por distancia: la trae el archivo): baja con la distancia del
        # frente (a 15 m la mitad, a 60 m ~0,3) en vez de quedar parejo 12 s
        lejos *= np.power(1500.0 / (1500.0 + np.maximum(s, 0.0)), 0.8)
    return t, cerca, lejos


def ruido_lento(n, hz, rng):
    """ruido suave de banda baja (media 0, desvio ~1)."""
    x = rng.standard_normal(n // 100 + 8)
    b, a = signal.butter(2, hz / (SR / 100 / 2))
    y = signal.filtfilt(b, a, x)
    y = y / (np.std(y) + 1e-12)
    return np.interp(np.arange(n) / 100.0, np.arange(len(y)), y)


# bandas por tipo: (cuerpo, oscuro [lowpass o banda], brillo, susurro). El soplo, arriba de la banda del pacer.
BANDAS = {0: ([120, 450], 750, [380, 2400], [1800, 5200]),     # la lateral: el cuerpo desde 120 Hz (parlantes Quest)
          1: ([450, 1400], [380, 950], [900, 3500], [2600, 6200])}
SOPLO_RMS4_DBFS = -27.0     # RMS en 0-4 s (la ventana del tono de exhalar del pacer)
SOPLO_PICO_TOPE = -9.0


def soplo(kind, life, seed, pico_dbfs):
    rng = np.random.default_rng(seed)
    t, cerca, lejos = envolventes(kind, life, rng)
    n = t.size
    blanco = rng.standard_normal(n)
    b_cuerpo, b_oscuro, b_brillo, b_susurro = BANDAS[kind]
    sos_grave = signal.butter(2, b_cuerpo, btype="bandpass", fs=SR, output="sos")
    sos_oscuro = signal.butter(2, b_oscuro, btype=("lowpass" if np.isscalar(b_oscuro) else "bandpass"), fs=SR, output="sos")
    sos_brillo = signal.butter(2, b_brillo, btype="bandpass", fs=SR, output="sos")
    sos_susurro = signal.butter(2, b_susurro, btype="bandpass", fs=SR, output="sos")
    grave = signal.sosfiltfilt(sos_grave, blanco)
    oscuro = signal.sosfiltfilt(sos_oscuro, rng.standard_normal(n))
    brillo = signal.sosfiltfilt(sos_brillo, rng.standard_normal(n))
    susurro = signal.sosfiltfilt(sos_susurro, rng.standard_normal(n))
    for x in (grave, oscuro, brillo, susurro):
        x /= np.std(x) + 1e-12
    # soplos adentro de la rafaga (no es un ruido plano) y un temblor rapido para el susurro del pasto
    puf = 1.0 + 0.22 * ruido_lento(n, 0.4, rng) + 0.10 * ruido_lento(n, 1.3, rng)
    puf = np.clip(puf, 0.45, 1.6)
    temblor = np.clip(1.0 + 0.5 * ruido_lento(n, 9.0, rng), 0.0, 2.2)
    c = np.power(np.clip(cerca, 0.0, 1.0), 0.8)
    l = np.clip(lejos, 0.0, 1.0)
    brillo_mix = np.clip(c, 0.0, 1.0)
    cuerpo = (0.55 * grave + 0.45 * ((1.0 - brillo_mix) * oscuro + brillo_mix * brillo))
    k_sus = 0.09 if kind == 0 else 0.22          # el soplo es sobre todo siseo (el aire que sale)
    y = (0.30 * l + 0.70 * c) * puf * cuerpo + k_sus * c * c * temblor * susurro
    # pasaaltos 30 Hz (sin DC) y fundidos coseno de 0,3 s en las puntas
    y = signal.sosfiltfilt(signal.butter(2, 30, btype="highpass", fs=SR, output="sos"), y)
    f = int(0.3 * SR)
    ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(f) / f)
    y[:f] *= ramp
    y[-f:] *= ramp[::-1]
    if kind == 1:
        rms4 = np.sqrt(np.mean(y[:4 * SR] ** 2)) + 1e-12
        g = 10 ** (SOPLO_RMS4_DBFS / 20.0) / rms4
        g = min(g, 10 ** (SOPLO_PICO_TOPE / 20.0) / (np.abs(y).max() + 1e-12))
        y *= g
    else:
        y *= 10 ** (pico_dbfs / 20.0) / (np.abs(y).max() + 1e-12)
    return y, t, cerca, lejos


def escribir(ruta, y):
    q = np.clip(np.round(y * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(q.tobytes())
    return q


def informe(nombre, q, cerca):
    y = q.astype(np.float64) / 32768.0
    pk = 20 * math.log10(np.abs(y).max() + 1e-12)
    rms = 20 * math.log10(np.sqrt(np.mean(y * y)) + 1e-12)
    # RMS en ventanas de 50 ms: el tramo fuerte
    w = int(0.05 * SR)
    r = np.sqrt(np.convolve(y * y, np.ones(w) / w, mode="same"))
    rms_max = 20 * math.log10(r.max() + 1e-12)
    salto = np.abs(np.diff(y)).max()
    tipico = np.percentile(np.abs(np.diff(y)), 99.9)
    punta = max(abs(y[0]), abs(y[-1]))
    # brillo: centroide espectral cuando la rafaga esta cerca vs lejos
    f, tt, Z = signal.stft(y, fs=SR, nperseg=4096)
    mag = np.abs(Z)
    cen = (f[:, None] * mag).sum(0) / (mag.sum(0) + 1e-12)
    ce = np.interp(tt, np.arange(cerca.size) / SR, cerca)
    e = mag.sum(0)
    # brillo = centroide ponderado por energia: cerca = el frente en el usuario, lejos = el resto con senal (antes el
    # "lejos" exigia un tramo fuerte con el frente lejos y en la variante B no habia ninguno: salia NaN)
    m_c = (ce > 0.6) & (e > 0.05 * e.max())
    m_l = (ce < 0.15) & (e > 0.02 * e.max())
    c_cerca = float((cen[m_c] * e[m_c]).sum() / e[m_c].sum()) if m_c.any() else float("nan")
    c_lejos = float((cen[m_l] * e[m_l]).sum() / e[m_l].sum()) if m_l.any() else float("nan")
    # contra el pacer: la energia por bandas y el RMS en los primeros 4 s (la ventana del tono de exhalar)
    fw, Pw = signal.welch(y, SR, nperseg=8192)
    banda = lambda a, b: 100.0 * Pw[(fw >= a) & (fw < b)].sum() / Pw.sum()
    rms4 = 20 * math.log10(np.sqrt(np.mean(y[:4 * SR] ** 2)) + 1e-12)
    y4 = signal.sosfiltfilt(signal.butter(4, [500, 4000], btype="bandpass", fs=SR, output="sos"), y[:4 * SR])
    rms4_alta = 20 * math.log10(np.sqrt(np.mean(y4 ** 2)) + 1e-12)
    corr = float(np.corrcoef(np.interp(np.arange(r.size), np.arange(r.size), r)[::480], cerca[::480])[0, 1])
    dc = float(np.mean(y))
    return dict(nombre=nombre, dur=y.size / SR, pico=pk, rms=rms, rms50_max=rms_max, salto_max=float(salto),
                salto_p999=float(tipico), punta=float(punta), centroide_cerca=c_cerca, centroide_lejos=c_lejos,
                corr_env_cerca=corr, dc=dc, b_bajo=banda(0, 200), b_pacer=banda(150, 500), b_alto=banda(500, 4000),
                rms4=rms4, rms4_alta=rms4_alta)


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
        os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "vida", "audio"))
    os.makedirs(carpeta, exist_ok=True)
    assert abs(vm.BP["SndLen"] - vm.BP["GustLife"]) < 1e-9 and abs(vm.BP["BreathSndLen"] - vm.BP["BreathLife"]) < 1e-9, \
        "SndLen/BreathSndLen tienen que ser la duracion de los WAV (= GustLife/BreathLife por defecto)"
    piezas = [("SND_VidaGustA", 0, vm.BP["GustLife"], 101, -16.0), ("SND_VidaGustB", 0, vm.BP["GustLife"], 202, -16.0),
              ("SND_VidaGustC", 0, vm.BP["GustLife"], 303, -16.0), ("SND_VidaSoplo", 1, vm.BP["BreathLife"], 404, None)]
    res = []
    curvas = {}
    for nombre, kind, life, seed, pk in piezas:
        y, t, cerca, lejos = soplo(kind, life, seed, pk)
        q = escribir(os.path.join(carpeta, nombre + ".wav"), y)
        res.append(informe(nombre, q, cerca))
        curvas[nombre] = (t, cerca, lejos, q.astype(np.float64) / 32768.0)
    lineas = []
    for r in res:
        lineas.append("%-14s %5.1f s  pico %6.1f dBFS  RMS %6.1f dBFS (maximo en 50 ms %6.1f)  salto max entre muestras %.4f "
                      "(p99,9 %.4f)  puntas %.1e  DC %.1e  brillo cerca %4.0f Hz / lejos %4.0f Hz  corr(envolvente, frente) %.2f"
                      "\n               energia < 200 Hz %4.1f %% | 150-500 Hz (la banda del pacer) %4.1f %% | 500-4000 Hz %4.1f %%"
                      " | RMS 0-4 s %6.1f dBFS (en 500-4000 Hz %6.1f dBFS)"
                      % (r["nombre"], r["dur"], r["pico"], r["rms"], r["rms50_max"], r["salto_max"], r["salto_p999"],
                         r["punta"], r["dc"], r["centroide_cerca"], r["centroide_lejos"], r["corr_env_cerca"],
                         r["b_bajo"], r["b_pacer"], r["b_alto"], max(r["rms4"], -99.0), max(r["rms4_alta"], -99.0)))
    lineas.append("referencia SND_PacerExhale: tono de 4 s, RMS -20,5 dBFS, 93 % en 150-500 Hz, ~0 % en 1-6 kHz "
                  "(suena junto con el comienzo del soplo)")
    texto = "\n".join(lineas)
    print(texto)
    open(os.path.join(carpeta, "informe_sonidos.txt"), "w", encoding="utf-8").write(texto + "\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(len(curvas), 2, figsize=(13, 2.4 * len(curvas)))
        for i, (nombre, (t, cerca, lejos, y)) in enumerate(curvas.items()):
            a = ax[i, 0]
            w = int(0.05 * SR)
            r = np.sqrt(np.convolve(y * y, np.ones(w) / w, mode="same"))
            a.plot(t, r / r.max(), color="#6b6fd6", lw=1, label="RMS (50 ms)")
            a.plot(t, cerca, color="#d98a6b", lw=1.2, label="frente en el usuario")
            a.plot(t, lejos, color="#8fb08f", lw=1, ls="--", label="rafaga en el llano")
            a.set_title(nombre, fontsize=9)
            a.set_xlim(0, t[-1])
            a.set_ylim(0, 1.05)
            a.tick_params(labelsize=7)
            if i == 0:
                a.legend(fontsize=7, loc="upper right")
            f, tt, Z = signal.stft(y, fs=SR, nperseg=2048)
            ax[i, 1].pcolormesh(tt, f, 20 * np.log10(np.abs(Z) + 1e-7), shading="auto", vmin=-110, vmax=-40, cmap="magma")
            ax[i, 1].set_ylim(0, 8000)
            ax[i, 1].tick_params(labelsize=7)
            ax[i, 1].set_title("espectrograma (0-8 kHz)", fontsize=9)
        ax[-1, 0].set_xlabel("s", fontsize=8)
        ax[-1, 1].set_xlabel("s", fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(carpeta, "sonidos_rafaga.png"), dpi=110)
    except Exception as e:  # noqa: BLE001
        print("sin grafico:", e)
    print("escrito en " + carpeta)


if __name__ == "__main__":
    main()
