# -*- coding: utf-8 -*-
"""Diagrama de la geometria del aliento visible (lado y planta), con los limites de confort. Usa air_model.py."""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import air_model as am  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
q = am.AIR
sd = am.Seeds(q)
EYE = np.array([0.0, 0.0, 120.0])


def estado(yaw_head=0.0, yaw_lag=0.0, pitch=-2.0):
    st = am.BPState(EYE, yaw_head, pitch, q)
    st.yawLag, st.pitchLag = yaw_lag, pitch
    st.Ein = st.Eout = 1.0
    st.Fout = 1.5
    st.rateIn = st.rateOut = 0.12                      # tasa tipica a mitad de una respiracion de 4 s
    return st


def caminos(st, idx, yaw_head=0.0, pitch=-2.0, n=90):
    """P(s) y alfa(s) de las motas idx a lo largo de su camino completo."""
    ss = np.linspace(0.001, 0.999, n)
    P = np.zeros((len(idx), n, 3))
    A = np.zeros((len(idx), n))
    for j, s in enumerate(ss):
        for kk, i in enumerate(idx):
            T = (s - sd.e[i]) % 1.0
            if i < sd.nin:
                st.Tin = T
            else:
                st.Tout = T
            m = am.motes(st, sd, EYE, yaw_head, pitch, q)
            P[kk, j] = m["P"][i]
            A[kk, j] = m["alpha"][i]
    return P, A


def dibujar(ax, P, A, col, plano):
    a, b = (0, 2) if plano == "lado" else (0, 1)
    for k in range(P.shape[0]):
        x, y = P[k, :, a], P[k, :, b]
        if plano == "planta":
            y = y                                     # UE +Y = derecha -> arriba del grafico = derecha del usuario
        ax.plot(x, y, color=col, lw=0.5, alpha=0.18)
        for j in range(P.shape[1] - 1):
            al = float(A[k, j])
            if al > 0.02:
                ax.plot(x[j:j + 2], y[j:j + 2], color=col, lw=1.6, alpha=min(1.0, al * 1.8))


rng = np.random.default_rng(2)
idx_in = rng.choice(sd.nin, 34, replace=False)
idx_out = sd.nin + rng.choice(sd.nout, 34, replace=False)
st = estado()
Pi, Ai = caminos(st, idx_in)
Po, Ao = caminos(st, idx_out)
st_g = estado(yaw_head=30.0, yaw_lag=12.0)            # a mitad de un giro rapido: el aire va 18 grados atras
Pig, Aig = caminos(st_g, idx_in, yaw_head=30.0)

fig, axs = plt.subplots(1, 3, figsize=(21, 7.4), dpi=110)
C_IN, C_OUT = "#6f8cff", "#e0786a"
mouth = am.mouth(EYE, 0.0, -2.0, q)

# ---- lado ----
ax = axs[0]
dibujar(ax, Pi, Ai, C_IN, "lado")
dibujar(ax, Po, Ao, C_OUT, "lado")
for r, ls in ((q["NearMin"], "-"), (q["NearFull"], "--")):
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(EYE[0] + r * np.cos(th), EYE[2] + r * np.sin(th), color="#555", ls=ls, lw=1)
for ang, txt, c in ((-2.0, "mirada (-2°)", "#222"), (q["ElevMax"] - 2.0, "tope de elevación (-4° de la mirada)", "#b33"),
                    (q["ElevMax"] - q["ElevSoft"] - 2.0, "plena visibilidad (-10°)", "#d88"),
                    (-50.0, "borde inferior del campo (~-50°)", "#999")):
    L = 140.0
    ax.plot([0, L * math.cos(math.radians(ang))], [120, 120 + L * math.sin(math.radians(ang))], color=c, lw=1, ls=":")
    ax.text(L * math.cos(math.radians(ang)) * 0.62, 120 + L * math.sin(math.radians(ang)) * 0.62 + 1.2, txt, color=c,
            fontsize=8)
ax.plot(*EYE[[0, 2]], "ko")
ax.text(EYE[0] - 3, EYE[2] + 3, "ojos", fontsize=9)
ax.plot(mouth[0], mouth[2], "s", color="#333")
ax.text(mouth[0] - 11, mouth[2] - 5, "boca", fontsize=9)
ax.text(0, 157, "círculos: sin motas a < 22 cm; plenas desde 36 cm", fontsize=8, color="#555")
ax.annotate("metaball a 3,8 m →", xy=(140, 125), fontsize=9, ha="right", color="#555")
ax.set_xlim(-20, 145)
ax.set_ylim(40, 162)
ax.set_aspect("equal")
ax.set_title("De lado (cm). Azul: inhalar, llega a la boca · Rojo: exhalar, sale de la boca\n"
             "trazo grueso = tramo visible (alfa > 0,02); fino = tramo oculto", fontsize=10)
ax.grid(alpha=0.2)

# ---- planta ----
ax = axs[1]
dibujar(ax, Pi, Ai, C_IN, "planta")
dibujar(ax, Po, Ao, C_OUT, "planta")
ax.plot(0, 0, "ko")
for aa in (-52, 52):
    ax.plot([0, 150 * math.cos(math.radians(aa))], [0, 150 * math.sin(math.radians(aa))], color="#999", ls=":", lw=1)
ax.text(60, 70, "campo visual (±52°)", fontsize=8, color="#999")
ax.set_xlim(-20, 145)
ax.set_ylim(-80, 80)
ax.set_aspect("equal")
ax.set_title("En planta (cm), cabeza quieta. Arriba = derecha del usuario", fontsize=10)
ax.grid(alpha=0.2)

# ---- planta durante un giro ----
ax = axs[2]
dibujar(ax, Pig, Aig, C_IN, "planta")
mg = am.mouth(EYE, 30.0, -2.0, q)
ax.plot(0, 0, "ko")
ax.plot(mg[0], mg[1], "s", color="#333")
for yawv, c, txt in ((30.0, "#222", "cabeza (30°)"), (12.0, "#b33", "marco del aire (12°, con retardo)")):
    ax.annotate("", xy=(120 * math.cos(math.radians(yawv)), 120 * math.sin(math.radians(yawv))), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=c, lw=1.5))
    ax.text(122 * math.cos(math.radians(yawv)), 122 * math.sin(math.radians(yawv)), txt, color=c, fontsize=9)
ax.set_xlim(-20, 145)
ax.set_ylim(-80, 80)
ax.set_aspect("equal")
ax.set_title("Giro de cabeza en plena inhalación: el origen de las motas se queda\n"
             "atrás (mundo), el destino es la boca ACTUAL (siempre entran)", fontsize=10)
ax.grid(alpha=0.2)

plt.tight_layout()
out = os.path.join(AQUI, "geometria_aliento.png")
plt.savefig(out)
print("->", out)
