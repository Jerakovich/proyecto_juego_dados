Juego de Tablero por Equipos
Este proyecto implementa un juego de mesa basado en un esquema cliente-servidor donde diferentes equipos compiten para avanzar por un tablero de un número configurable de posiciones.
Descripción del Juego

Los equipos compiten por ser el primero en llegar a la meta en un tablero de posiciones.
Cada integrante del equipo lanza un dado en su turno.
La suma de los valores obtenidos por todos los integrantes determina cuánto avanza el equipo.
Los turnos se rotan entre los equipos.
El primer equipo en alcanzar o superar la posición máxima (por defecto 100) gana.
Los jugadores deben ser aceptados por consenso en un equipo existente.

Requisitos Técnicos

Python 3.6 o superior
Módulos estándar de Python (socket, threading, random, time)

Estructura del Proyecto
├── servidor.py     # Archivo principal del servidor
└── cliente.py      # Cliente para conectarse al juego
Configuración
El juego tiene varias configuraciones que pueden ajustarse en el archivo servidor.py:
VariableDescripciónValor por defectoHOSTDirección IP del servidor127.0.0.1PORTPuerto del servidor5000MAX_POSICIONESNúmero de posiciones en el tablero100RANGO_DADORango mínimo y máximo del dado(1, 6)
Instalación y Ejecución

Clona el repositorio o descarga los archivos.

# Ejecucion (procurar orden)

- Ejecutar: 
    javac *.java / javac (Get-ChildItem -Filter *.java).FullName

- Ejecuta el rmi : 
dentro del directorio: rmi_logging 
    java LogServer

- Ejecuta el servidor:
    python servidor_juego.py

- Ejecuta el cliente en una o varias ventanas de consola:
    python cliente_juego.py

- Una vez hayan logs dentro de "rmi_logging/logs_centralizados" se puede ejecutar el grafico :
    export VENTANA_TIEMPO=5
    python3 grafico.py


# Comandos del Juego
ComandoDescripciónstartVota para iniciar el juegotirarLanza el dado cuando es tu turnosolicitar_union:EquipoSolicita unirse a un equipo específicovoto:Jugador:si o voto:Jugador:noVota para aceptar o rechazar a un jugador que quiere unirse a tu equiposalirDesconecta al cliente del servidor
Características Especiales

Sistema de votación: Los jugadores deben ser aceptados por unanimidad para unirse a un equipo.
Juego asíncrono: El juego inicia cuando todos los equipos con jugadores votan por iniciar.
Gestión de turnos: El servidor asigna los turnos aleatoriamente y controla su rotación.
Restricciones en juego iniciado: No se pueden crear equipos nuevos una vez iniciado el juego.

# Flujo del Juego

Los jugadores se conectan al servidor e ingresan su nombre y equipo.
Si un jugador intenta unirse a un equipo existente, los miembros actuales deben aprobar su entrada.
Cuando al menos un jugador de cada equipo vota por iniciar, el juego comienza.
El servidor asigna aleatoriamente el orden de los turnos y notifica a todos.
En cada turno, todos los jugadores del equipo actual deben lanzar su dado.
El equipo avanza según la suma de sus tiradas y se pasa al siguiente equipo.
El primer equipo en alcanzar o superar la meta gana, y el juego se reinicia.

Notas Adicionales

El servidor permite unirse a nuevos jugadores en cualquier momento del juego, pero sólo a equipos existentes cuando el juego está en curso.
El sistema está diseñado para ser resistente a desconexiones y manejar errores básicos.
El servidor gestiona múltiples conexiones usando hilos (threading) para cada cliente.
