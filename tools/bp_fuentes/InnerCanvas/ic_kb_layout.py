# ic_kb_layout.py - el teclado de Inner Canvas: posiciones de las teclas (cm, en el espacio del actor) y su celda del atlas.
# Actor: X se aleja de la persona, Y a su derecha, Z arriba. Cada tecla es un Plane girado como los titulos (Roll 90, Yaw 90):
# su eje X local queda horizontal (ancho) y su eje Y local vertical (alto).
# Indices: 0-25 = A..Z, 26 = N con tilde (solo en espanol), 27 = BORRAR, 28 = ESPACIO, 29 = OK.
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NTILDE = 'Ñ'
CHARS_UP = list(LETTERS) + [NTILDE]
CHARS_LO = [c.lower() for c in LETTERS] + ['ñ']
ROWS = ['QWERTYUIOP', 'ASDFGHJKL' + NTILDE, 'ZXCVBNM']
P = 9.0       # paso entre teclas (cm)
K = 8.0       # lado de una tecla (cm)
Z0 = 9.0      # fila de arriba
ATLAS = 2048
CELL = 256    # px por celda del atlas (8 x 8 celdas)


def key_index(ch):
    return 26 if ch == NTILDE else LETTERS.index(ch)


def layout():
    """lista de 30 (y, z, w, h) en cm, por indice"""
    pos = [None] * 30
    for r, row in enumerate(ROWS):
        z = Z0 - r * P
        for c, ch in enumerate(row):
            pos[key_index(ch)] = (-40.5 + c * P, z, K, K)
    pos[27] = (31.5, Z0 - 2 * P, 2 * K + 1.0, K)            # BORRAR, al final de la fila de Z
    pos[28] = (-13.5, Z0 - 3 * P, 7 * P - 1.0, K)          # ESPACIO
    pos[29] = (31.5, Z0 - 3 * P, 2 * K + 1.0, K)            # OK
    return pos


FIELD = (0.0, Z0 + 13.0, 81.0, 12.0)                         # campo del nombre (y, z, w, h)
BOARD = (0.0, -4.0, 92.0, 52.0)                             # tablero invisible que recibe el laser


def atlas_cells():
    """celda del atlas (col, fila, ancho en celdas) por indice y por idioma: (en, es)"""
    cells = {}
    for i in range(27):
        cells[i] = ((i % 8, i // 8, 1), (i % 8, i // 8, 1))
    cells[27] = ((0, 5, 2), (2, 5, 2))   # DELETE / BORRAR
    cells[28] = ((0, 4, 4), (4, 4, 4))   # SPACE / ESPACIO
    cells[29] = ((4, 5, 2), (4, 5, 2))   # OK
    return cells


def rects():
    """(en, es): listas de 30 (u0, v0, us, vs) para el parametro Rect del material de la tecla"""
    en, es = [], []
    for i in range(30):
        a, b = atlas_cells()[i]
        for cell, out in ((a, en), (b, es)):
            c, r, w = cell
            out.append((c * CELL / ATLAS, r * CELL / ATLAS, w * CELL / ATLAS, CELL / ATLAS))
    return en, es
