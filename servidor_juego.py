import socket
import threading
import random
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv  
import os
import subprocess   

from utils.log_helper import registrar_log


# Configuración del servidor
load_dotenv()  # Cargar variables de entorno desde el archivo .env


HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
# Variables del juego
equipos = {
    "Equipo1": [],
    "Equipo2": []
}
clientes = []
conexiones_por_nombre = {}
solicitudes_pendientes = {}  # nombre -> {"equipo": ..., "votos": {"miembro": "si"/"no"}}
posiciones_equipos = {}      # Posiciones de los equipos en el tablero
equipos_inicio = {}          # Registro de equipos que han votado por iniciar
MAX_POSICIONES = 100         # Posiciones máximas en el tablero (configurable)
RANGO_DADO = (1, 6)          # Rango del dado (configurable)
juego_iniciado = False       # Estado del juego
turno_actual = None          # Equipo que tiene el turno actual
orden_turnos = []            # Orden de turnos de los equipos
# Variable para almacenar el estado del juego
estado_juego = {}


def registrar_log(tipo, juego_id, operacion, equipo="", jugador="", valor=""):
    """Función para registrar logs en el sistema de logging"""
    timestamp = str(int(time.time()))
    args = [timestamp, tipo, juego_id, operacion]
    if equipo:
        args.append(equipo)
    if jugador:
        args.append(jugador)
    if valor:
        args.append(str(valor))

    # Llama al cliente Java con los argumentos
    try:
        subprocess.run(["java", "-cp", "rmi_logging", "LogClient"] + args)
    except Exception as e:
        logging.error(f"Error al registrar log: {e}")
        print(f"Error al registrar log: {e}")
def manejar_cliente(conn, addr):
    conn.send("Tu nombre: \n".encode())
    nombre = conn.recv(1024).decode().strip()
    conexiones_por_nombre[nombre] = conn

    conn.send("Nombre del equipo:\n".encode())
    equipo = conn.recv(1024).decode().strip()

    # Verificar si el juego ya está iniciado y si el equipo existe
    if juego_iniciado and equipo not in equipos:
        conn.send("El juego ya está iniciado. Solo puedes unirte a equipos existentes.\n".encode())
        # Enviar lista de equipos disponibles
        equipos_disponibles = ", ".join([eq for eq in equipos if equipos[eq]])
        conn.send(f"Equipos disponibles: {equipos_disponibles}\n".encode())
        # Solicitar nuevamente el nombre del equipo
        conn.send("Nombre del equipo:\n".encode())
        equipo = conn.recv(1024).decode().strip()
        
        # Verificar nuevamente si el equipo existe
        if equipo not in equipos:
            conn.send("Equipo no válido. Desconectando...\n".encode())
            conn.close()
            return

    if equipo not in equipos:
        equipos[equipo] = []
        posiciones_equipos[equipo] = 0
        equipos_inicio[equipo] = set()  # Inicializa el conjunto de miembros que votaron por iniciar

    if not equipos[equipo]:  # Primer jugador, se une directo
        equipos[equipo].append(nombre)
        clientes.append(conn)
        registrar_log("INFO", "1", "UNION_JUGADOR", equipo, nombre)

        print(f"{nombre} se ha unido directamente a {equipo}.")
        conn.send(f"Te has conectado correctamente como {nombre} en {equipo}.\n".encode())
        
        if not juego_iniciado:
            conn.send("Puedes escribir 'start' para votar por iniciar el juego.\n".encode())
        conn.send("Puedes escribir mensajes, 'solicitar_union:EquipoX' o 'voto:Jugador:si/no'\n".encode())
    else:
        # Solicita unirse por votación
        solicitudes_pendientes[nombre] = {"equipo": equipo, "votos": {}}
        conn.send(f"Solicitud enviada para unirte a {equipo}. Esperando aprobacion...\n".encode())
        for jugador in equipos[equipo]:
            if jugador in conexiones_por_nombre:
                conexiones_por_nombre[jugador].send(
                    f"{nombre} quiere unirse a {equipo}. Escribe 'voto:{nombre}:si' o 'voto:{nombre}:no'\n".encode()
                )

        # Espera aprobación
        while nombre in solicitudes_pendientes:
            time.sleep(0.5)  # Pequeña pausa para evitar uso intensivo de CPU

        if not juego_iniciado:
            conn.send("Puedes escribir 'start' para votar por iniciar el juego.\n".encode())
        conn.send("Puedes escribir mensajes, 'solicitar_union:EquipoX' o 'voto:Jugador:si/no'\n".encode())

    while True:
        try:
            mensaje = conn.recv(1024).decode().strip()
            if not mensaje:
                break

            # Votación para iniciar juego
            if mensaje.lower() == "start" and not juego_iniciado:
                manejar_voto_inicio(nombre, equipo)
                continue

            # Tirar dado cuando es el turno del equipo
            if juego_iniciado and mensaje.lower() == "tirar" and turno_actual == equipo:
                manejar_tirada_dado(nombre, equipo)
                continue

            if mensaje.startswith("solicitar_union:"):
                destino = mensaje.split(":")[1]
                
                # Verificar si el juego ya está iniciado y si el equipo existe
                if juego_iniciado and destino not in equipos:
                    conn.send("El juego ya está iniciado. Solo puedes unirte a equipos existentes.\n".encode())
                    # Enviar lista de equipos disponibles
                    equipos_disponibles = ", ".join([eq for eq in equipos if equipos[eq]])
                    conn.send(f"Equipos disponibles: {equipos_disponibles}\n".encode())
                    continue
                
                if destino not in equipos:
                    equipos[destino] = []
                    posiciones_equipos[destino] = 0
                    equipos_inicio[destino] = set()

                if nombre in equipos[destino] or nombre in solicitudes_pendientes:
                    conn.send("Ya estas en ese equipo o ya solicitaste unirte.\n".encode())
                    continue

                solicitudes_pendientes[nombre] = {"equipo": destino, "votos": {}}
                conn.send(f"Solicitud enviada para unirte a {destino}. Esperando aprobacion...\n".encode())

                for jugador in equipos[destino]:
                    if jugador in conexiones_por_nombre:
                        conexiones_por_nombre[jugador].send(
                            f"{nombre} quiere unirse a {destino}. Escribe 'voto:{nombre}:si' o 'voto:{nombre}:no'\n".encode()
                        )

            elif mensaje.startswith("voto:"):
                partes = mensaje.split(":")
                if len(partes) != 3:
                    conn.send("Formato incorrecto. Usa voto:Jugador:si o voto:Jugador:no\n".encode())
                    continue
                objetivo, decision = partes[1], partes[2]
                if objetivo in solicitudes_pendientes:
                    votos = solicitudes_pendientes[objetivo]["votos"]
                    votos[nombre] = decision
                    conn.send(f"Voto registrado: {decision} para {objetivo}\n".encode())

                    equipo_obj = solicitudes_pendientes[objetivo]["equipo"]
                    total_miembros = len(equipos[equipo_obj])
                    if len(votos) == total_miembros:
                        if all(v == "si" for v in votos.values()):
                            equipos[equipo_obj].append(objetivo)
                            registrar_log("INFO", "1", "UNION_APROBADA", equipo_obj, objetivo)

                            if objetivo in conexiones_por_nombre:
                                conexiones_por_nombre[objetivo].send(f"Fuiste aceptado en {equipo_obj}.\n".encode())
                                if not juego_iniciado:
                                    conexiones_por_nombre[objetivo].send("Puedes escribir 'start' para votar por iniciar el juego.\n".encode())
                            for miembro in equipos[equipo_obj]:
                                if miembro != objetivo and miembro in conexiones_por_nombre:
                                    conexiones_por_nombre[miembro].send(
                                        f"{objetivo} se ha unido al juego en {equipo_obj}.\n".encode()
                                    )
                            clientes.append(conexiones_por_nombre[objetivo])
                        else:
                            if objetivo in conexiones_por_nombre:
                                conexiones_por_nombre[objetivo].send("Tu solicitud fue rechazada.\n".encode())
                                registrar_log("INFO", "1", "UNION_RECHAZADA", equipo_obj, objetivo)

                        del solicitudes_pendientes[objetivo]
                else:
                    conn.send("No hay solicitud pendiente para ese jugador.\n".encode())

            else:
                # Mensajes generales
                for cliente in clientes:
                    if cliente != conn:
                        cliente.send(f"{nombre} ({equipo}): {mensaje}\n".encode())

        except Exception as e:
            print(f"Error: {e}")
            break

    # Limpieza si se desconecta
    print(f"🛑 {nombre} se ha desconectado.")
    registrar_log("INFO", "1", "DESCONEXION_JUGADOR", equipo, nombre)   
    if conn in clientes:
        clientes.remove(conn)
    for eq in equipos.values():
        if nombre in eq:
            eq.remove(nombre)
    if nombre in conexiones_por_nombre:
        del conexiones_por_nombre[nombre]
    if nombre in solicitudes_pendientes:
        del solicitudes_pendientes[nombre]
    
    # Eliminar voto de inicio si existe
    for eq in equipos_inicio:
        if nombre in equipos_inicio[eq]:
            equipos_inicio[eq].remove(nombre)
    
    conn.close()

def manejar_voto_inicio(nombre, equipo):
    """Maneja el voto de un jugador para iniciar el juego"""
    global juego_iniciado, turno_actual, orden_turnos
    
    # Registrar el voto del jugador
    equipos_inicio[equipo].add(nombre)
    
    # Notificar a todos sobre el voto
    mensaje = f"{nombre} del {equipo} ha votado por iniciar el juego."
    for cliente in clientes:
        cliente.send(mensaje.encode())
    
    # Verificar si hay suficientes equipos y si todos tienen al menos un voto
    equipos_con_jugadores = [eq for eq in equipos if equipos[eq]]
    equipos_listos = [eq for eq in equipos_con_jugadores if equipos_inicio[eq]]
    
    # Debe haber al menos 2 equipos con jugadores y todos los equipos con jugadores deben tener al menos un voto
    if len(equipos_listos) >= 2 and set(equipos_listos) == set(equipos_con_jugadores):
        iniciar_juego()

def iniciar_juego():
    """Inicia el juego cuando todos los equipos están listos"""
    global juego_iniciado, turno_actual, orden_turnos, estado_juego
    
    # Verificar que hay al menos un jugador en cada equipo
    equipos_validos = [eq for eq in equipos if equipos[eq]]
    if len(equipos_validos) < 2:
        return  # No hay suficientes equipos para comenzar
    
    # Inicializar las posiciones de cada equipo
    for eq in equipos_validos:
        posiciones_equipos[eq] = 0
    
    # Determinar el orden aleatorio de los turnos
    orden_turnos = equipos_validos.copy()
    random.shuffle(orden_turnos)
    
    # Establecer el turno inicial
    turno_actual = orden_turnos[0]
    
    # Inicializar el estado del juego
    estado_juego['tiradas'] = {}  # Para almacenar las tiradas por equipo
    estado_juego['ronda'] = 1     # Contador de rondas
    
    # Marcar el juego como iniciado
    juego_iniciado = True
    
    # Notificar a todos los jugadores que el juego ha comenzado

    mensaje = f"¡✅ El juego ha comenzado! Orden de turnos: {', '.join(orden_turnos)}\n"
    mensaje += f"Turno actual: {turno_actual}. Los jugadores de {turno_actual} deben escribir 'tirar' para lanzar el dado."
    registrar_log("INFO", "1", "INICIO_JUEGO", turno_actual, "", "")
    
    for cliente in clientes:
        cliente.send(mensaje.encode())

def manejar_tirada_dado(nombre, equipo):
    """Maneja la tirada de dado de un jugador durante su turno"""
    global turno_actual
    
    if equipo != turno_actual:
        conexiones_por_nombre[nombre].send(f"❌ No es el turno de tu equipo. Turno actual: {turno_actual}\n".encode())
        return
    
    # Inicializar tiradas del turno si es necesario
    if not hasattr(manejar_tirada_dado, 'tiradas_actuales'):
        manejar_tirada_dado.tiradas_actuales = {}
    
    if turno_actual not in manejar_tirada_dado.tiradas_actuales:
        manejar_tirada_dado.tiradas_actuales[turno_actual] = {}
    
    # Verificar si este jugador ya tiró en este turno
    if nombre in manejar_tirada_dado.tiradas_actuales[turno_actual]:
        conexiones_por_nombre[nombre].send(f"🎲 Ya has lanzado el dado en este turno.\n".encode())
        return
    
    # Lanzar el dado
    resultado = random.randint(RANGO_DADO[0], RANGO_DADO[1])
    manejar_tirada_dado.tiradas_actuales[turno_actual][nombre] = resultado
    
    # Notificar la tirada
    mensaje = f"🎲 {nombre} del {equipo} ha lanzado el dado y obtuvo {resultado}.\n"
    
    # Enviar el mensaje a todos
    for cliente in clientes:
        cliente.send(mensaje.encode())
    
    # Verificar si todos los jugadores del equipo han tirado
    jugadores_equipo = equipos[turno_actual]
    jugadores_que_tiraron = manejar_tirada_dado.tiradas_actuales[turno_actual].keys()
    
    if set(jugadores_equipo).issubset(set(jugadores_que_tiraron)):
        # Todos los jugadores han tirado, calcular el avance
        suma_tiradas = sum(manejar_tirada_dado.tiradas_actuales[turno_actual].values())
        
        # Actualizar la posición del equipo
        posiciones_equipos[equipo] += suma_tiradas
        
        mensaje = f"🎲 Todos los jugadores de {equipo} han lanzado el dado.\n"
        mensaje += f"Suma total: {suma_tiradas}\n"
        mensaje += f"🧩 El {equipo} avanza a la posición {posiciones_equipos[equipo]} de {MAX_POSICIONES}.\n"
        
        # Verificar si hay un ganador
        if posiciones_equipos[equipo] >= MAX_POSICIONES:
            mensaje += f"🏆 ¡{equipo} ha ganado el juego al alcanzar o superar {MAX_POSICIONES} posiciones!"
            registrar_log("INFO", "1", "JUEGO_GANADO", equipo, "", "")
            for cliente in clientes:
                cliente.send(mensaje.encode())
            
            # Reiniciar el juego
            reiniciar_juego()
            return
        
        # Pasar al siguiente turno
        indice_actual = orden_turnos.index(turno_actual)
        manejar_tirada_dado.tiradas_actuales.pop(turno_actual, None)  # Limpiar tiradas del turno actual
        turno_actual = orden_turnos[(indice_actual + 1) % len(orden_turnos)]
        
        mensaje += f"🔄 Turno de {turno_actual}. Los jugadores de {turno_actual} deben escribir 'tirar' para lanzar el dado."
        registrar_log("INFO", "1", "TIRADA_COMPLETA", equipo, nombre, resultado)
        
        # Enviar el mensaje a todos
        for cliente in clientes:
            cliente.send(mensaje.encode())
    else:
        # Informar cuántos jugadores faltan por tirar
        jugadores_faltantes = set(jugadores_equipo) - set(jugadores_que_tiraron)
        mensaje = f"Esperando a que {len(jugadores_faltantes)} jugadores más de {equipo} lancen el dado: {', '.join(jugadores_faltantes)}"
        
        # Enviar el mensaje a todos
        for cliente in clientes:
            cliente.send(mensaje.encode())

def reiniciar_juego():
    """Reinicia el estado del juego después de que un equipo ha ganado"""
    global juego_iniciado, turno_actual, orden_turnos
    
    # Reiniciar variables del juego
    juego_iniciado = False
    turno_actual = None
    orden_turnos = []
    
    # Reiniciar posiciones
    for eq in posiciones_equipos:
        posiciones_equipos[eq] = 0
    
    # Reiniciar votos de inicio
    for eq in equipos_inicio:
        equipos_inicio[eq] = set()
    
    # Limpiar tiradas si existen
    if hasattr(manejar_tirada_dado, 'tiradas_actuales'):
        manejar_tirada_dado.tiradas_actuales = {}
    
    # Notificar a todos que pueden reiniciar
    registrar_log("INFO", "1", "JUEGO_TERMINADO", "", "", "")
    mensaje = "El juego ha terminado. Pueden votar 'start' para iniciar un nuevo juego."\
      
    for cliente in clientes:
        cliente.send(mensaje.encode())

# Configuración del servidor
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"Servidor iniciado en {HOST}:{PORT}")
    registrar_log("INFO", "1", "INICIO_SERVIDOR", "", "", "")
    print(f"Configuración del juego: {MAX_POSICIONES} posiciones, dado {RANGO_DADO[0]}-{RANGO_DADO[1]}")
    registrar_log("INFO", "1", "CONFIG_JUEGO", "", "", f"{MAX_POSICIONES} posiciones, dado {RANGO_DADO[0]}-{RANGO_DADO[1]}")
    
    
    try:
        while True:
            conn, addr = servidor.accept()
            print(f"Nueva conexión desde {addr}")
            hilo = threading.Thread(target=manejar_cliente, args=(conn, addr))
            hilo.daemon = True
            hilo.start()
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario")
    finally:
        servidor.close()
        print("🔒 Servidor cerrado")

if __name__ == "__main__":
    iniciar_servidor()