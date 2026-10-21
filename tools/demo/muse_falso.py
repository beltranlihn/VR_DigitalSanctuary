"""muse_falso.py - manda lo mismo que Muse Integration 0.3 (contrato acordado el 2026-10-20 noche) para probar sin diadema.
  /muse/alpha f 0-1 (actividad neuronal: el grafico del HUD) · /muse/heart_rate f bpm · /muse/sensor_active i
  /muse/calm_index f % de -100 a +100 vs la calibracion · /muse/calm_quality f 0-1
Sirve tambien para la senal simulada del BioHub como respaldo: mientras llega esto el simulado se apaga ("BIO: Muse real ...");
2 s despues de cortar vuelve ("BIO: sin Muse, vuelve el simulado").
  python tools/demo/muse_falso.py --ip 127.0.0.1 --desde 20 --hasta 35
  python tools/demo/muse_falso.py --ip <IP del Quest> --hasta 300          # al visor, como la app real (UDP 10000)
  python tools/demo/muse_falso.py --viejo ...                               # solo /muse/calm + heart + sensor (contrato anterior)
"""
import argparse, math, os, socket, struct, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mirror_test_send import osc  # codificador OSC de floats y strings del Quest falso


def osc_int(addr, v):
    def pad(b):
        return b + b'\0' * (4 - len(b) % 4)
    return pad(addr.encode()) + pad(b',i') + struct.pack('>i', int(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=10000)
    ap.add_argument("--desde", type=float, default=0.0, help="segundo en que empieza a mandar")
    ap.add_argument("--hasta", type=float, default=30.0, help="segundo en que deja de mandar")
    ap.add_argument("--hz", type=float, default=20.0)
    ap.add_argument("--viejo", action="store_true", help="contrato anterior: /muse/calm en vez de alpha + calm_index")
    a = ap.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t0 = time.time()
    n = 0
    while True:
        t = time.time() - t0
        if t >= a.hasta:
            break
        if t >= a.desde:
            u = t - a.desde
            dst = (a.ip, a.port)
            if a.viejo:
                sock.sendto(osc("/muse/calm", [0.3 + 0.2 * math.sin(u * 0.7)]), dst)
            else:
                sock.sendto(osc("/muse/alpha", [0.45 + 0.2 * math.sin(u * 0.5) + 0.05 * math.sin(u * 2.3)]), dst)
                # la persona se calma: de 0 % a ~+20 % en 2 min, con algo de ruido; calidad alta
                ci = 20.0 * (1.0 - math.exp(-u / 60.0)) + 3.0 * math.sin(u * 0.21)
                sock.sendto(osc("/muse/calm_index", [ci]), dst)
                sock.sendto(osc("/muse/calm_quality", [0.85 + 0.1 * math.sin(u * 0.05)]), dst)
            sock.sendto(osc("/muse/heart_rate", [74.0 - 4.0 * (1.0 - math.exp(-u / 90.0)) + 1.5 * math.sin(u * 0.3)]), dst)
            sock.sendto(osc_int("/muse/sensor_active", 1), dst)
            n += 1
        time.sleep(1.0 / a.hz)
    print("muse falso: %d envios a %s:%d (%s)" % (n, a.ip, a.port, "contrato viejo" if a.viejo else "contrato 0.3"))


if __name__ == "__main__":
    main()
