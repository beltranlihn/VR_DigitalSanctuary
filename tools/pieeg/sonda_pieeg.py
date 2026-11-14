"""Sonda Bluetooth del PiEEG XR: ¿la caja está emitiendo? ¿qué canales tienen contacto?

Uso (con el Python del entorno $HOME\\pieeg-venv, que tiene bleak):
    python tools/pieeg/sonda_pieeg.py                 # escanea 8 s y lista lo que ve
    python tools/pieeg/sonda_pieeg.py leer            # se conecta 10 s y diagnostica cada canal
    python tools/pieeg/sonda_pieeg.py leer --segundos 60 --csv   # y además graba un CSV

Una sola conexión Bluetooth a la vez: cerrar PiEEG Cloud o BodyPress antes de "leer".
Protocolo (docs.pieeg.com, Specification): notify 0000fe42-8e22-4541-9d4c-21edae82ed19,
24 bytes por muestra = 8 canales x 3 bytes big-endian en complemento a 2, 250 muestras/s.
"""
import argparse
import asyncio
import csv
import statistics
import sys
import time
from pathlib import Path

from bleak import BleakClient, BleakScanner

UUID_DATOS = "0000fe42-8e22-4541-9d4c-21edae82ed19"
NOMBRES = ("PIEEG", "EAREEG", "IRONBCI")
CANALES = 8
BYTES_MUESTRA = CANALES * 3
FS = 250
LUGAR = ["sien izq. abajo", "sien izq. arriba", "frente izq.", "frente izq.",
         "frente der.", "frente der.", "sien der. arriba", "sien der. abajo"]
CARPETA_CSV = Path.home() / "pieeg-datos"


def a_microvoltios(b0, b1, b2):
    raw = (b0 << 16) | (b1 << 8) | b2
    if raw & 0x800000:
        raw -= 1 << 24
    return raw, raw * 4.5 / 16777215 * 1e6


def es_pieeg(nombre):
    return bool(nombre) and any(n in nombre.upper() for n in NOMBRES)


async def escanear(segundos):
    print(f"Escaneando Bluetooth LE {segundos} s...")
    vistos = await BleakScanner.discover(timeout=segundos, return_adv=True)
    filas = sorted(vistos.values(), key=lambda da: -(da[1].rssi or -999))
    encontrados = []
    for disp, adv in filas:
        nombre = adv.local_name or disp.name or ""
        marca = "  <== PiEEG" if es_pieeg(nombre) else ""
        if nombre:
            print(f"  {adv.rssi:>4} dBm  {disp.address}  {nombre}{marca}")
        if marca:
            encontrados.append(disp)
    sin_nombre = sum(1 for d, a in filas if not (a.local_name or d.name))
    print(f"  (+{sin_nombre} dispositivos sin nombre)")
    if encontrados:
        print(f"\nOK: la caja está emitiendo ({encontrados[0].name}, {encontrados[0].address}).")
    else:
        print("\nNo apareció ningún PiEEG. Revisar: LED de la caja encendido, cable de energía,"
              " a menos de 5 m, y que BodyPress o PiEEG Cloud no la tengan conectada.")
    return encontrados


def resto_movil(xs, ventana=FS):
    """Le resta a cada muestra el promedio móvil de 1 s (saca el offset y la deriva lenta)."""
    acum, salida = [0.0], []
    for x in xs:
        acum.append(acum[-1] + x)
    for i, x in enumerate(xs):
        a, b = max(0, i - ventana // 2), min(len(xs), i + ventana // 2 + 1)
        salida.append(x - (acum[b] - acum[a]) / (b - a))
    return salida


def veredicto(dc, desv, saturado):
    if saturado:
        return "SATURADO (¿referencia sin contacto?)"
    if desv < 0.5:
        return "PLANO: sin contacto"
    if desv > 300:
        return "muy ruidoso (movimiento, contacto flojo o red eléctrica)"
    return "señal"


async def leer(args):
    direccion = args.direccion
    if not direccion:
        encontrados = await escanear(6)
        if not encontrados:
            return 1
        direccion = encontrados[0].address

    muestras, crudos, largos, sobrantes = [], [], {}, 0
    tiempos = []

    def al_llegar(_car, data: bytearray):
        nonlocal sobrantes
        ahora = time.time()
        largos[len(data)] = largos.get(len(data), 0) + 1
        n = len(data) // BYTES_MUESTRA
        sobrantes += len(data) - n * BYTES_MUESTRA
        for s in range(n):
            bloque = data[s * BYTES_MUESTRA:(s + 1) * BYTES_MUESTRA]
            pares = [a_microvoltios(*bloque[3 * i:3 * i + 3]) for i in range(CANALES)]
            crudos.append([p[0] for p in pares])
            muestras.append([p[1] for p in pares])
            tiempos.append(ahora)

    print(f"\nConectando a {direccion}...")
    async with BleakClient(direccion, timeout=20) as cliente:
        print("Conectado. Servicios y características:")
        notificables = []
        for serv in cliente.services:
            print(f"  servicio {serv.uuid}")
            for car in serv.characteristics:
                print(f"    {car.uuid}  {','.join(car.properties)}")
                if "notify" in car.properties:
                    notificables.append(car)
        if not notificables:
            print("No hay ninguna característica 'notify': el protocolo no es el documentado.")
            return 1
        car = next((c for c in notificables if c.uuid.lower() == UUID_DATOS), notificables[0])
        if car.uuid.lower() != UUID_DATOS:
            print(f"Ojo: no está la característica documentada; uso {car.uuid}.")
        await cliente.start_notify(car, al_llegar)
        print(f"Leyendo {args.segundos} s... (quieto, cara relajada)")
        await asyncio.sleep(args.segundos)
        await cliente.stop_notify(car)

    if not muestras:
        print("Conectó pero no llegaron datos. Probable: firmware (docs: Firmware & Service).")
        return 1

    duracion = max(tiempos[-1] - tiempos[0], 1e-6)
    print(f"\n{len(muestras)} muestras en {duracion:.1f} s = {len(muestras) / duracion:.0f} muestras/s"
          f" (esperado {FS}). Largos de notificación: {largos}."
          + (f" Bytes sobrantes: {sobrantes} (¡el paquete no es múltiplo de 24!)" if sobrantes else ""))
    print(f"\n{'canal':<6}{'lugar':<18}{'offset µV':>11}{'variación µV':>14}  diagnóstico")
    for c in range(CANALES):
        serie = [m[c] for m in muestras]
        dc = statistics.fmean(serie)
        desv = statistics.pstdev(resto_movil(serie))
        saturado = sum(1 for r in crudos if abs(r[c]) >= 0x7FFF00) > len(crudos) * 0.1
        print(f"Ch{c + 1:<4}{LUGAR[c]:<18}{dc:>11.0f}{desv:>14.1f}  {veredicto(dc, desv, saturado)}")
    print("\n'variación' = desviación de la señal sin el offset ni la deriva lenta."
          " Con buen contacto y quieto: decenas de µV. Parpadear la hace saltar en la frente.")

    if args.csv:
        CARPETA_CSV.mkdir(parents=True, exist_ok=True)
        ruta = CARPETA_CSV / time.strftime("pieegxr_%Y%m%d_%H%M%S.csv")
        with open(ruta, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp"] + [f"ch{i + 1}" for i in range(CANALES)])
            for t, m in zip(tiempos, muestras):
                w.writerow([f"{t:.6f}"] + [f"{v:.3f}" for v in m])
        print(f"\nCSV: {ruta}  (timestamp = llegada de la notificación, µV crudos sin filtrar)")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", nargs="?", default="escanear", choices=["escanear", "leer"])
    p.add_argument("--segundos", type=float, help="escanear: 8 por defecto; leer: 10 por defecto")
    p.add_argument("--direccion", help="dirección Bluetooth, para saltarse el escaneo")
    p.add_argument("--csv", action="store_true", help=f"grabar un CSV en {CARPETA_CSV}")
    args = p.parse_args()
    if args.modo == "escanear":
        return 0 if asyncio.run(escanear(args.segundos or 8)) else 1
    args.segundos = args.segundos or 10
    return asyncio.run(leer(args))


if __name__ == "__main__":
    sys.exit(main())
