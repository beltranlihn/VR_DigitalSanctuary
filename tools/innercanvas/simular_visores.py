# simular_visores.py - Inner Canvas: simula a los visores Pico mandandole al PC (L_InnerCanvas_Wall) su estado y sus trazos, por
# OSC/UDP, con el mismo formato que BP_ICLink_IC (ver VR_Test/Saved/ClaudeScripts/InnerCanvas/ic_link_dsl.py). Sirve para probar la
# pantalla de los 8 dibujos sin cascos.
#
#   python tools/innercanvas/simular_visores.py                       8 visores, 40 s dibujando, despues presentacion
#   python tools/innercanvas/simular_visores.py --visores 1,3 --dibujo 20
#   python tools/innercanvas/simular_visores.py --nueva 2             el visor 2 empieza una sesion nueva (su cuadro se limpia)
#   python tools/innercanvas/simular_visores.py --ip 192.168.1.10     a otro PC
#
# Mensajes (todos empiezan con slot y sesion; numeros como float32, nombres como string):
#   /ic/new slot ses + nombre       /ic/nm slot ses + nombre       /ic/st slot ses fase tiempo tinta idioma
#   /ic/sb slot ses trazo preset size01 sizeLo sizeHi r g b grad gaR gaG gaB gbR gbG gbB ubase atlasV0 atlasV1 seed
#   /ic/k  slot ses trazo nudo px py pz fx fy fz ux uy uz presion      /ic/se slot ses trazo nudos
#   /ic/pr slot ses px py pz escala                                     /ic/cl slot ses
import argparse, math, random, socket, struct, time

NOMBRES = ['Lucia', 'Martin', 'Muñoz', 'Sofia', 'ÑANDU', 'Ana Maria', 'Joaquin', 'Paz']   # el teclado solo tiene A-Z, Ñ y ñ
# Paleta definida de Inner Canvas (copiada de la instancia de BP_TBDirector_NC en L_InnerCanvas, 2026-11-12): primario -> secundario
PALETA_A = [(0.768, 0.807, 0.753), (0.392, 0.644, 0.521), (0.270, 0.552, 0.658), (0.017, 0.058, 0.050)]
PALETA_B = [(0.366, 0.539, 0.503), (0.089, 0.332, 0.301), (0.107, 0.191, 0.445), (0.125, 0.262, 0.191)]


def pad(b):
    return b + b'\0' * (4 - len(b) % 4)


def osc(addr, floats=(), strings=()):
    tags = ',' + 'f' * len(floats) + 's' * len(strings)
    out = pad(addr.encode()) + pad(tags.encode())
    for f in floats:
        out += struct.pack('>f', float(f))
    for s in strings:
        out += pad(s.encode('latin-1'))     # como el OSC de Unreal: un byte por caracter (la Ñ viaja como 0xD1)
    return out


class Visor:
    def __init__(self, slot, ses, sock, dest, dibujo):
        self.slot, self.ses, self.sock, self.dest, self.dibujo = slot, ses, sock, dest, dibujo
        self.nombre = NOMBRES[(slot - 1) % len(NOMBRES)]
        self.rng = random.Random(slot * 977 + ses)
        self.trazo = -1
        self.t0 = time.time()

    def send(self, addr, floats=(), strings=()):
        self.sock.sendto(osc(addr, (self.slot, self.ses) + tuple(floats), strings), self.dest)

    def empezar(self):
        self.send('/ic/new', strings=[self.nombre])

    def estado(self, fase, tiempo, tinta):
        self.send('/ic/st', (fase, tiempo, tinta, 1.0 if self.slot % 2 == 0 else 0.0))

    def trazo_nuevo(self):
        self.trazo += 1
        r = self.rng
        # la paleta de 4 colores del visor (BP_TBDirector_NC de L_InnerCanvas: ColorMode 1, SlotColorA -> SlotColorB, degradado)
        k = r.randint(0, 3)
        a, b = PALETA_A[k], PALETA_B[k]
        self.send('/ic/sb', [self.trazo, r.randint(0, 2), 0.6, 0.5, 1.5] + list(a) + [1.0] + list(a) + list(b) + [r.random(), 0.0, 0.0, r.randint(0, 9999)])
        self.fase_curva = r.random() * 6.28
        self.alto = 70 + r.random() * 110
        self.radio = 30 + r.random() * 70
        self.nudo = 0

    def nudo_nuevo(self, u):
        # una espiral suave alrededor del centro del espacio (posiciones en cm, relativas al centro en el piso)
        a = self.fase_curva + u * 4.0
        p = (math.cos(a) * self.radio, math.sin(a) * self.radio, self.alto + 25 * math.sin(u * 3.0))
        f = (-math.sin(a), math.cos(a), 0.15)
        self.send('/ic/k', [self.trazo, self.nudo, p[0], p[1], p[2], f[0], f[1], f[2], 0.0, 0.0, 1.0, 0.8])
        self.nudo += 1

    def trazo_fin(self):
        self.send('/ic/se', [self.trazo, self.nudo])

    def presentar(self):
        self.send('/ic/pr', [0.0, 0.0, 130.0, 1.6])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ip', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9300)
    ap.add_argument('--visores', default='1,2,3,4,5,6,7,8')
    ap.add_argument('--dibujo', type=float, default=40.0, help='segundos dibujando antes de la presentacion')
    ap.add_argument('--hold', type=float, default=15.0, help='segundos de presentacion')
    ap.add_argument('--sesion', type=int, default=0, help='numero de sesion (0 = segun la hora, siempre mayor)')
    ap.add_argument('--nueva', type=int, default=0, help='solo: el visor N empieza una sesion nueva y dibuja')
    a = ap.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest = (a.ip, a.port)
    ses = a.sesion or int(time.time()) % 100000
    slots = [a.nueva] if a.nueva else [int(x) for x in a.visores.split(',') if x.strip()]
    vs = [Visor(s, ses, sock, dest, a.dibujo) for s in slots]
    print('simulando visores %s -> %s:%d (sesion %d)' % (slots, a.ip, a.port, ses))
    for v in vs:
        v.empezar()
    t0 = time.time()
    hz, last_st, last_nm = 30.0, 0.0, 0.0
    dur_trazo = 1.6
    while True:
        t = time.time() - t0
        if t - last_nm > 2.0:
            for v in vs:
                v.send('/ic/nm', strings=[v.nombre])
            last_nm = t
        dibujando = t < a.dibujo
        if t - last_st > 0.2:
            for v in vs:
                v.estado(12 if dibujando else 14, max(0.0, 180.0 - t * 180.0 / a.dibujo) if dibujando else 0.0,
                         max(0.0, 1.0 - t / a.dibujo) if dibujando else 0.0)
            last_st = t
        if dibujando:
            for v in vs:
                k = int(t / dur_trazo)
                if k != v.trazo:
                    if v.trazo >= 0:
                        v.trazo_fin()
                    while v.trazo < k:
                        v.trazo_nuevo()
                v.nudo_nuevo((t % dur_trazo) / dur_trazo * 2.0)
        elif not getattr(vs[0], 'presentado', False):
            for v in vs:
                v.trazo_fin()
                v.presentar()
                v.presentado = True
            print('presentacion: los dibujos quedan girando')
        if t > a.dibujo + a.hold:
            break
        time.sleep(1.0 / hz)
    print('listo')


if __name__ == '__main__':
    main()
