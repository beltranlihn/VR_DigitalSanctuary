// ensayo.js - GENERADO desde Unreal (ensayo_export.py -> gen_ensayo_js.py). No editar a mano: se pisa en cada exportacion.
// Los ensayos de etapa (BP_StageRunner_SC + TargetPoints sc<K>_* en cada nivel de test) son la fuente: la Obra y la web los leen.
// Posiciones en cm relativas al PlayerStart del nivel (fwd adelante, side derecha +, up sobre los ojos). La web aplica el
// DESPLAZAMIENTO respecto de la base (lo movido en Unreal se mueve igual aca), no la posicion absoluta.
const ENSAYO = {
 "base": {
  "alma_in": {
   "fwd": 220,
   "side": 0,
   "up": 5,
   "scale": 1
  },
  "alma_side": {
   "fwd": 140,
   "side": -300,
   "up": 20,
   "scale": 1
  },
  "charge": {
   "fwd": 253,
   "side": 0,
   "up": 37,
   "scale": 2.115
  },
  "title": {
   "fwd": 300,
   "side": 0,
   "up": 0,
   "scale": 1
  }
 },
 "voLen": [
  8.54,
  9.33,
  5.15,
  7.43,
  13.05
 ],
 "stages": [
  {
   "k": 0,
   "level": "Test_Entering",
   "points": {
    "alma_in": {
     "fwd": 220.0,
     "side": 0.0,
     "up": 5.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "alma_side": {
     "fwd": 140.0,
     "side": -300.0,
     "up": 20.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "charge": {
     "fwd": 253.0,
     "side": 0.0,
     "up": 37.0,
     "yaw": 0.0,
     "scale": 2.115
    },
    "title": {
     "fwd": 300.0,
     "side": 0.0,
     "up": 0.0,
     "yaw": 0.0,
     "scale": 1.0
    }
   },
   "AlmaTime": 10.5,
   "InstrTime": 6,
   "OutroTime": 2.5,
   "ChargeTime": 4,
   "TimeoutS": 240,
   "top": [
    0.55,
    0.64,
    0.82
   ],
   "hor": [
    0.66,
    0.73,
    0.88
   ]
  },
  {
   "k": 1,
   "level": "Test_Heart",
   "points": {
    "alma_in": {
     "fwd": 220.0,
     "side": 0.0,
     "up": 5.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "alma_side": {
     "fwd": 140.0,
     "side": -300.0,
     "up": 20.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "charge": {
     "fwd": 253.0,
     "side": 0.0,
     "up": 37.0,
     "yaw": 0.0,
     "scale": 2.115
    },
    "title": {
     "fwd": 300.0,
     "side": 0.0,
     "up": 0.0,
     "yaw": 0.0,
     "scale": 1.0
    }
   },
   "AlmaTime": 11.3,
   "InstrTime": 6,
   "OutroTime": 2.5,
   "ChargeTime": 4,
   "TimeoutS": 150,
   "top": [
    0.4,
    0.3,
    0.31
   ],
   "hor": [
    0.95,
    0.85,
    0.83
   ]
  },
  {
   "k": 2,
   "level": "Test_Fluid",
   "points": {
    "alma_in": {
     "fwd": 220.0,
     "side": 0.0,
     "up": 5.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "alma_side": {
     "fwd": 140.0,
     "side": -300.0,
     "up": 20.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "charge": {
     "fwd": 253.0,
     "side": 0.0,
     "up": 37.0,
     "yaw": 0.0,
     "scale": 2.115
    },
    "title": {
     "fwd": 300.0,
     "side": 0.0,
     "up": 0.0,
     "yaw": 0.0,
     "scale": 1.0
    }
   },
   "AlmaTime": 7.2,
   "InstrTime": 6,
   "OutroTime": 2.5,
   "ChargeTime": 4,
   "TimeoutS": 120,
   "top": [
    0.0369,
    0.0273,
    0.0482
   ],
   "hor": [
    0.0176,
    0.013,
    0.0232
   ]
  },
  {
   "k": 3,
   "level": "Test_Sequencer",
   "points": {
    "alma_in": {
     "fwd": 220.0,
     "side": 0.0,
     "up": 5.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "alma_side": {
     "fwd": 140.0,
     "side": -300.0,
     "up": 20.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "charge": {
     "fwd": 253.0,
     "side": 0.0,
     "up": 37.0,
     "yaw": 0.0,
     "scale": 2.115
    },
    "title": {
     "fwd": 300.0,
     "side": 0.0,
     "up": 0.0,
     "yaw": 0.0,
     "scale": 1.0
    }
   },
   "AlmaTime": 9.4,
   "InstrTime": 6,
   "OutroTime": 2.5,
   "ChargeTime": 4,
   "TimeoutS": 240,
   "top": [
    0.863,
    0.745,
    0.631
   ],
   "hor": [
    0.973,
    0.815,
    0.565
   ]
  },
  {
   "k": 4,
   "level": "L_TBTest_SC",
   "points": {
    "alma_in": {
     "fwd": 220.0,
     "side": 0.0,
     "up": 5.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "alma_side": {
     "fwd": 140.0,
     "side": -300.0,
     "up": 20.0,
     "yaw": 0.0,
     "scale": 1.0
    },
    "charge": {
     "fwd": 253.0,
     "side": 0.0,
     "up": 37.0,
     "yaw": 0.0,
     "scale": 2.115
    },
    "title": {
     "fwd": 300.0,
     "side": 0.0,
     "up": 0.0,
     "yaw": 0.0,
     "scale": 1.0
    }
   },
   "AlmaTime": 15,
   "InstrTime": 6,
   "OutroTime": 2.5,
   "ChargeTime": 6,
   "TimeoutS": 240,
   "top": [
    0.0027,
    0.0033,
    0.008
   ],
   "hor": [
    0.0137,
    0.0194,
    0.0395
   ]
  }
 ]
};
ENSAYO.stages.forEach(s => { const st = STAGES[s.k]; if (!st) return; st.top = s.top; st.hor = s.hor; CHARGE_T[s.k] = s.ChargeTime; });
function ensDelta(k, nm) {
  const s = ENSAYO.stages[k], b = ENSAYO.base[nm], p = s && s.points[nm];
  if (!p || !b) return { f: 0, s: 0, u: 0, sc: 1 };
  return { f: (p.fwd - b.fwd) / 100, s: (p.side - b.side) / 100, u: (p.up - b.up) / 100, sc: p.scale / b.scale };
}
function ensPause(k) { const s = ENSAYO.stages[k]; return s ? Math.max(0, +(s.AlmaTime - ENSAYO.voLen[k]).toFixed(2)) : 2; }
