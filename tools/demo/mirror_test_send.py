"""mirror_test_send.py - un QUEST FALSO: manda por OSC lo mismo que BP_MirrorLink_SC en modo emisor, siguiendo un guion.

  python tools/demo/mirror_test_send.py                        # guion "menu": solo clics (START -> ENTERING), sin estado
  python tools/demo/mirror_test_send.py --guion sync_menu      # solo ESTADO, ningun clic: el robot tiene que elegir Draw por la sincronizacion
  python tools/demo/mirror_test_send.py --guion sesion_draw --segundos 200    # menu -> Draw -> panel (3 paginas) -> dibuja circulos
  python tools/demo/mirror_test_send.py --guion sesion_breath --segundos 210  # menu -> Breath -> panel -> el mando respira contra el cuerpo
  python tools/demo/mirror_test_send.py --guion flujo_breath --segundos 90    # ya en Breath: las fases del director nuevo (BP_DemoFlow_SC)
  python tools/demo/mirror_test_send.py --guion flujo_draw --segundos 90      # ya en Draw: fases + un trazo de practica con el gatillo
  python tools/demo/mirror_test_send.py --guion flujo_draw_izq --segundos 90  # lo mismo con la mano IZQUIERDA (mano 0, gatillo izquierdo)
  python tools/demo/mirror_test_send.py --guion cierre_draw --segundos 150    # Draw entero: practica, dibujo, el Quest termina, resultados y vuelve al MENU (a los 128 s)
  opciones: --ip 192.168.0.20 --port 9000 --retardo 4 (corre el guion N s si el receptor tarda en arrancar)

Mensajes:
  /sc/pose  30 floats: cabeza, grip L, grip R, aim L, aim R  ->  x y z pitch yaw roll (mundo)
  /sc/in    15 floats: los canales de BP_MirrorLink_SC.Keys (1 = gatillo R, 14 = clic del gatillo R)
  /sc/st    9 floats: fase del menu, eleccion, fase del director (antes: estado del panel), mano (antes: pagina), fase del ensayo, RT, PT,
            calma y BPM del Muse del Quest   (-1 = no hay)
  /sc/lvl   string: nivel actual del visor (cada 0,25 s, como el emisor real)
Las posiciones salen de los niveles: PlayerStart + 120 cm = ojos; botones, cuadros y paneles donde estan colocados.
"""
import argparse, math, socket, struct, time

def _pad(b):
    return b + b"\0" * (4 - len(b) % 4)

def osc(address, args):
    tags = "," + "".join("s" if isinstance(a, str) else "f" for a in args)
    out = _pad(address.encode()) + _pad(tags.encode())
    for a in args:
        out += _pad(a.encode()) if isinstance(a, str) else struct.pack(">f", float(a))
    return out

def aim(src, dst):
    dx, dy, dz = (d - s for s, d in zip(src, dst))
    return math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx))

# --- lugares (mundo) ---------------------------------------------------------------------------------
MENU_EYE = (-3600.0, 0.0, 196.97)
START_BTN, CARD_A, CARD_B = (-3450.0, 0.0, 140.0), (-3450.0, 18.0, 180.0), (-3450.0, -18.0, 180.0)
BREATH_EYE, BREATH_PANEL = (0.0, 0.0, 120.0), (170.0, 0.0, 118.0)
DRAW_EYE, DRAW_PANEL = (-315.0, 0.0, 226.0), (-145.0, 0.0, 224.0)

def pulso(t, *ts):
    return 1.0 if any(x <= t < x + 0.3 for x in ts) else 0.0

class Frame:
    def __init__(self, eye):
        self.eye = eye
        self.hr = (eye[0] + 10, eye[1] + 15, eye[2] - 40)
        self.hl = (eye[0] + 10, eye[1] - 15, eye[2] - 40)
        self.rot_r = (0.0, 0.0)
        self.trig = 0.0
        self.trig_l = 0.0
        self.level = "L_Demo_Menu"
        self.st = None

    def apuntar(self, target):
        self.rot_r = aim(self.hr, target)

    def pose(self):
        p, y = self.rot_r
        return [*self.eye, 0, 0, 0, *self.hl, 0, 0, 0, *self.hr, p, y, 0, *self.hl, 0, 0, 0, *self.hr, p, y, 0]

    def inp(self):
        return [self.trig_l, self.trig, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, self.trig_l, self.trig]

# --- el menu como lo vive el Quest ---------------------------------------------------------------------
def menu_estado(t, pick, eleccion):
    # fases de BP_DemoMenu_SC: 2 START visible (desde ~6 s), clic a los 9 -> 3 (2,2 s) -> 4; clic en el cuadro -> 6 (1,5 s) -> 7 (3 s) -> 8
    if t < 9: return 2, -1
    if t < 11.2: return 3, -1
    if t < pick: return 4, -1
    if t < pick + 1.5: return 6, eleccion
    if t < pick + 4.5: return 7, eleccion
    return 8, eleccion

def guion_menu(t, f, clics=True, estado=False, eleccion=1, pick=16.0):
    f.level = "L_Demo_Menu"
    f.apuntar(START_BTN if t < 12 else (CARD_A if eleccion == 1 else CARD_B))
    f.trig = pulso(t, 9.0, pick) if clics else 0.0
    if estado:
        ph, ch = menu_estado(t, pick, eleccion)
        f.st = [ph, ch, -1, -1, -1, -1, -1]

def etapa(t, f, eye, panel, clics_en, fin_panel):
    # el ensayo del Quest: fase 0 (velo + titulo) hasta 5,5 s, 1 hasta 6,0, 2 (panel) hasta fin_panel + 1, 3 la mecanica
    f.eye = eye
    f.hr = (eye[0] + 10, eye[1] + 15, eye[2] - 40)
    f.hl = (eye[0] + 10, eye[1] - 15, eye[2] - 40)
    f.apuntar(panel)
    f.trig = pulso(t, *clics_en)
    st_i, pag = 0, 0
    if t >= fin_panel - 9:                       # el panel aparece ShowDelay despues de la fase 2
        st_i = 1
    for k, c in enumerate(clics_en):
        if t >= c:
            pag = min(k + 1, 2)
            st_i = 2 if t < c + 0.5 else 1
    if t >= clics_en[-1] + 0.5: st_i, pag = 3, 2
    if t >= clics_en[-1] + 1.5: st_i = 4
    if t < 5.5: rph, pt = 0, t
    elif t < 6.0: rph, pt = 1, t - 5.5
    elif t < clics_en[-1] + 1.5: rph, pt = 2, t - 6.0
    else: rph, pt = 3, t - (clics_en[-1] + 1.5)
    f.st = [-1, -1, st_i, pag, rph, t, pt]
    return rph


# --- el director de las experiencias (BP_DemoFlow_SC, guion 2026-10-19): /sc/st slot 2 = fase, slot 3 = mano (1 derecha) --------
FASES_BREATH = [(6.0, 0), (9.0, 1), (10.8, 2), (14.0, 3), (20.0, 4), (23.0, 5), (23.6, 6), (24.8, 7), (26.8, 8)]
FASES_DRAW = [(6.0, 0), (9.0, 1), (10.5, 2), (20.0, 3), (21.0, 4)]
# Heart (2026-10-20): panel 0-1, toma, paginas 2-4, el latido (5) hasta los 60 s, voz final (6), cierre comun 15-19, menu a los 130
# 2026-10-20 noche: Heart quedo con fases 0-7 (0 titulo, 1 tomar, 2 espera, 3 pagina 2 hasta 3 pulsos, 4 pausa, 5 sube la esfera, 6 etapa,
# 7 cierre) y el panel a los 9,8 s
FASES_HEART = [(10.0, 0), (13.0, 1), (14.8, 2), (24.0, 3), (25.0, 4), (27.9, 5), (60.0, 6), (63.0, 7), (65.0, 15), (67.0, 16), (102.0, 17),
               (105.0, 18), (130.0, 19)]


def flujo_heart(t, f):
    # el Quest falso de Heart: toma con la derecha y desde la pagina 1 deja la mano QUIETA en el pecho (el umbral del robot tiene que abrir
    # con la pose recibida: BP_MirrorLink_SC.RobotHeart pone bIgnoreTracking en el manager del latido)
    f.level = "L_Demo_Heart"
    eye = BREATH_EYE
    f.eye = eye
    f.apuntar((eye[0] + 150, eye[1], eye[2]))
    ph = 19
    for hasta, fase in FASES_HEART:
        if t < hasta:
            ph = fase
            break
    f.hr = (eye[0] + 10, eye[1] + 15, eye[2] - 40)
    f.hl = (eye[0] + 10, eye[1] - 15, eye[2] - 40)
    if 2 <= ph <= 7:
        f.hr = (eye[0] + 8, eye[1] - 4, eye[2] - 30)          # el sensor en el pecho, a la izquierda
    f.trig = f.trig_l = 0.0
    if t >= 130.0:
        f.level = "L_Demo_Menu"
        f.eye = MENU_EYE
        f.st = [0, -1, -1, -1, -1, -1, -1, -1, -1]
        return
    # slot 4: indice de calma % del Quest (-999 = sin indice); slot 5: 2.0 = protocolo con indice (APK desde el 20-10 noche)
    f.st = [-1, -1, ph, 1, 12.0 + 3.0 * math.sin(t / 9.0), 2.0, -1, 0.55 + 0.25 * math.sin(t / 7.0), 64 + 4 * math.sin(t / 11.0)]

def fase_flujo(t, draw):
    for hasta, fase in (FASES_DRAW if draw else FASES_BREATH):
        if t < hasta:
            return fase
    return 5 if draw else 9

def circulo(f, eye, k, izq):
    # un circulo de 20 cm a 60 cm delante de los ojos con la mano que dibuja
    a = 2 * math.pi * (k / 3.0)
    p = (eye[0] + 60, eye[1] + (-20 if izq else 20) + 20 * math.cos(a), eye[2] - 25 + 20 * math.sin(a))
    if izq:
        f.hl = p
        f.trig_l = 1.0
    else:
        f.hr = p
        f.trig = 1.0

def flujo(t, f, draw, izq=False, cierre=False):
    f.level = "L_Demo_Draw" if draw else "L_Demo_Breath"
    eye = DRAW_EYE if draw else BREATH_EYE
    f.eye = eye
    f.hr = (eye[0] + 10, eye[1] + 15, eye[2] - 40)
    f.hl = (eye[0] + 10, eye[1] - 15, eye[2] - 40)
    f.apuntar((eye[0] + 150, eye[1], eye[2]))
    ph = fase_flujo(t, draw)
    f.trig = 0.0
    f.trig_l = 0.0
    if draw and ph == 3 and t > 12.0:
        circulo(f, eye, t - 12.0, izq)
    if cierre:
        # el Quest dibuja 2 s de cada 3 entre los 25 y los 45 s, termina a los 50 (fase 6), resultados 15-19 y a los 128 vuelve al menu
        # (el robot llega antes a su fase 19: tiene que ESPERAR al visor, 'DEMOFLOW: robot espera al visor', y no abrir el menu solo)
        if 25.0 <= t < 45.0 and (t % 3.0) < 2.0:
            circulo(f, eye, t - 25.0, izq)
        if t >= 50.0:
            ph = 6
        for desde, fase in ((62.0, 15), (64.0, 16), (66.0, 17), (101.0, 18), (104.0, 19)):
            if t >= desde:
                ph = fase
        if t >= 128.0:
            f.level = "L_Demo_Menu"
            f.eye = MENU_EYE
            f.hr = (MENU_EYE[0] + 10, MENU_EYE[1] + 15, MENU_EYE[2] - 40)
            f.hl = (MENU_EYE[0] + 10, MENU_EYE[1] - 15, MENU_EYE[2] - 40)
            f.apuntar(START_BTN)
            f.trig = f.trig_l = 0.0
            f.st = [0, -1, -1, -1, -1, -1, -1, -1, -1]
            return
    # slot 4: indice de calma % (-999 = sin indice) y slot 5 = 2.0 (protocolo con indice); slots 7-8: actividad neuronal 0..1 y BPM
    f.st = [-1, -1, ph, 0 if izq else 1, 15.0 + 4.0 * math.sin(t / 9.0), 2.0, -1, 0.55 + 0.25 * math.sin(t / 7.0), 70 + 5 * math.sin(t / 11.0)]

a_yaw_respira = -90.0   # yaw del grip derecho que pone su RightVector hacia adelante (camara mirando +X)

def guion(nombre, t, f):
    if nombre == "menu":
        guion_menu(t, f)
    elif nombre == "sync_menu":
        guion_menu(t, f, clics=False, estado=True, eleccion=2)
        # el visor real abre la experiencia ~38 s despues de elegir (viaje 18 s + voces + HUD + negro)
        if t >= 16 + 38.0: f.level = "L_Demo_Draw"
    elif nombre == "flujo_heart":
        flujo_heart(t, f)
    elif nombre in ("flujo_breath", "flujo_draw", "flujo_draw_izq", "cierre_draw"):
        flujo(t, f, nombre != "flujo_breath", izq=nombre == "flujo_draw_izq", cierre=nombre == "cierre_draw")
    elif nombre in ("sesion_draw", "sesion_breath"):
        draw = nombre == "sesion_draw"
        cambio = 16 + 4.5
        if t < cambio:
            guion_menu(t, f, estado=True, eleccion=2 if draw else 1)
            return
        f.level = "L_Demo_Draw" if draw else "L_Demo_Breath"
        te = t - cambio
        clics = (13.0, 15.0, 17.0)
        rph = etapa(te, f, DRAW_EYE if draw else BREATH_EYE, DRAW_PANEL if draw else BREATH_PANEL, clics, clics[-1] + 0.5)
        if rph == 3 and draw:
            # dibuja: circulos de 20 cm a 85 cm delante de los ojos, 2 s con gatillo y 1 s sin
            k = te - (clics[-1] + 3.0)
            if k > 0:
                a = 2 * math.pi * (k / 3.0)
                e = f.eye
                f.hr = (e[0] + 85, e[1] + 20 * math.cos(a), e[2] - 25 + 20 * math.sin(a))
                f.trig = 1.0 if (k % 3.0) < 2.0 else 0.0
        elif rph == 3:
            # respira (zona de BP_BreathRig_SC: horizontal cabeza->grip <= 23 cm, 33-63 cm mas abajo, cara plana al cuerpo
            # = RightVector del grip hacia donde mira la cabeza, FacingDot >= 0,34): el vientre empuja el mando 1,5 cm
            # adelante y atras con la guia 6-0-6-0 (la senal es la distancia HORIZONTAL cabeza->grip)
            e = f.eye
            s = math.sin(2 * math.pi * te / 12.0)
            f.hr = (e[0] + 9 + 1.5 * s, e[1] + 4, e[2] - 48)
            f.rot_r = (0.0, a_yaw_respira)
            f.trig = 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--segundos", type=float, default=30)
    ap.add_argument("--retardo", type=float, default=0, help="corre todo el guion N segundos (si el receptor tarda en arrancar)")
    ap.add_argument("--yaw-respira", type=float, default=-90.0)
    ap.add_argument("--pausa", default="", help="INI:FIN segundos sin mandar nada (prueba la vigia de enlace del robot)")
    ap.add_argument("--guion", default="menu", choices=["menu", "sync_menu", "sesion_draw", "sesion_breath", "flujo_breath", "flujo_draw", "flujo_draw_izq", "cierre_draw", "flujo_heart"])
    a = ap.parse_args()
    global a_yaw_respira
    a_yaw_respira = a.yaw_respira
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    f = Frame(MENU_EYE)
    t0 = time.time()
    n = 0
    while time.time() - t0 < a.segundos + a.retardo:
        t = time.time() - t0 - a.retardo
        guion(a.guion, t, f)
        if a.pausa:
            p0, p1 = map(float, a.pausa.split(":"))
            if p0 <= t < p1:
                n += 1
                time.sleep(1 / 60)
                continue
        sock.sendto(osc("/sc/pose", f.pose()), (a.ip, a.port))
        sock.sendto(osc("/sc/in", f.inp()), (a.ip, a.port))
        if f.st is not None:
            sock.sendto(osc("/sc/st", f.st), (a.ip, a.port))
        if n % 15 == 0:
            sock.sendto(osc("/sc/lvl", [f.level]), (a.ip, a.port))
        n += 1
        time.sleep(1 / 60)
    print("enviados %d cuadros a %s:%d (guion %s)" % (n, a.ip, a.port, a.guion))

if __name__ == "__main__":
    main()
