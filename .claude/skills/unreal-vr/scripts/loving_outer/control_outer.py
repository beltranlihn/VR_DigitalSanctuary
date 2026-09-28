# -*- coding: utf-8 -*-
"""Controles del instrumento verify_outer.py sobre el port INTEGRADO.
  neg  : envoltura deliberadamente angosta (CSIG 0,7 y lente x0,3) -> TIENE que aparecer hueco < margen.
  oldw : Win.x viejo (ancla fija en Rc, sin la ameba) con la ameba V4 -> mide cuanto aporta la correccion.
Uso: python control_outer.py neg|neg2|neg3|oldw N SEED"""
import sys
import numpy as np
import lvport as L
import verify_outer as V
mode = sys.argv[1]
if mode == "neg":
    L.CSIG = 0.7; L.KAPPA = 0.3
elif mode == "neg2":                      # lobulos MUY angostos: tiene que asomar la hebra/la bolsa
    L.CSIG = 0.3; L.KAPPA = 0.05
elif mode == "neg3":                      # cota de la bolsa a la mitad: tiene que asomar la bolsa
    orig3 = L.OuterEnv
    def OuterEnv_half(sh, gC, LV1, LV3, LV4, LV5, OuterK):
        Env, Win = orig3(sh, gC, LV1, LV3, LV4, LV5, OuterK)
        Env = Env.copy(); Env[0] *= 0.5
        return Env, Win
    L.OuterEnv = OuterEnv_half
elif mode == "oldw":
    orig = L.OuterEnv
    def OuterEnv_old(sh, gC, LV1, LV3, LV4, LV5, OuterK):
        Env, Win = orig(sh, gC, LV1, LV3, LV4, LV5, OuterK)
        Win = Win.copy(); Win[0] = sh['Rc'] + gC + 0.8 * sh['MoundH'] + sh['kC'] + sh['lam'] + 1.0
        return Env, Win
    L.OuterEnv = OuterEnv_old
V.N_CFG = int(sys.argv[2]); V.SEED = int(sys.argv[3])
V.main()
