import socket
import threading
import sys
import json
import os
from dotenv import load_dotenv


# Configuración del cliente

load_dotenv()
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

def recibir_mensajes(sock):
    """Función para recibir mensajes del servidor"""
    while True:
        try:
            mensaje = sock.recv(1024).decode('utf-8')
            if mensaje:
                print(f"\n{mensaje}")
                print("> ", end="", flush=True)  # Mostrar el prompt después de recibir un mensaje
            else:
                print("\nConexión cerrada por el servidor.")
                sock.close()
                sys.exit(0)
        except Exception as e:
            print(f"\nError al recibir mensajes: {e}")
            sock.close()
            sys.exit(1)

def main():
    """Función principal del cliente"""
    # Crear socket y conectar al servidor
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente.connect((HOST, PORT))
        print(f"Conectado al servidor en {HOST}:{PORT}")
    except Exception as e:
        print(f"No se pudo conectar al servidor: {e}")
        sys.exit(1)

    # Iniciar hilo para recibir mensajes
    hilo = threading.Thread(target=recibir_mensajes, args=(cliente,))
    hilo.daemon = True
    hilo.start()

    # Bucle principal para enviar mensajes
    try:
        while True:
            entrada = input("> ")
            if entrada.lower() == "salir":
                print("Desconectando...")
                break
            if entrada:
                cliente.send(entrada.encode('utf-8'))
    except KeyboardInterrupt:
        print("\nDesconexión por interrupción del usuario.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cliente.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()