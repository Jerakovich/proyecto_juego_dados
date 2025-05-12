import subprocess
import time

def registrar_log(tipo, juego_id, operacion, equipo="", jugador="", valor=""):
    timestamp = str(int(time.time()))
    args = [timestamp, tipo, juego_id, operacion]
    if equipo:
        args.append(equipo)
    if jugador:
        args.append(jugador)
    if valor:
        args.append(str(valor))

    # Llama al cliente Java con los argumentos
    subprocess.run(["java", "-cp", "rmi_logging", "LogClient"] + args)
