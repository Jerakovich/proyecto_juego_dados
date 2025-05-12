import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
LOG_PATH = os.getenv("LOG_PATH")
VENTANA_MIN = int(os.getenv("VENTANA_TIEMPO", 5))

# Crear carpeta de salida si no existe
OUTPUT_DIR = "graficos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Leer archivo como CSV
columnas = ['timestamp', 'id', 'nivel', 'juego', 'evento', 'equipo', 'jugador', 'extra']
df = pd.read_csv(LOG_PATH, names=columnas, parse_dates=['timestamp'], engine='python')

# Filtrar tipos de eventos
df_jugadores = df[df['evento'] == 'UNION_JUGADOR'].copy()
df_jugadas = df[df['evento'] == 'TIRADA_COMPLETA'].copy()
if 'extra' in df_jugadas.columns:
    df_jugadas = df_jugadas[df_jugadas['extra'].notna()]
    df_jugadas['puntos'] = df_jugadas['extra'].astype(int)
else:
    raise ValueError("La columna 'extra' no existe en df_jugadas")

df_equipos = df_jugadores[['timestamp', 'equipo']].drop_duplicates()

# --- 1. Jugadores por equipo ---
plt.figure()
df_jugadores.groupby("equipo")["jugador"].nunique().plot(kind='bar')
plt.title("Jugadores por equipo")
plt.ylabel("Cantidad")
plt.savefig(os.path.join(OUTPUT_DIR, "grafico_1_jugadores_por_equipo.png"))

# --- 2. Jugadas por jugador ---
plt.figure()
df_jugadas.groupby("jugador")["evento"].count().sort_values().plot(kind='barh')
plt.title("Jugadas por jugador")
plt.xlabel("Cantidad")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "grafico_2_jugadas_por_jugador.png"))

# --- 3. Puntuación por equipo en el tiempo ---
ventana = timedelta(minutes=VENTANA_MIN)
df_jugadas['timestamp'] = pd.to_datetime(df_jugadas['timestamp'])
df_jugadas['puntos'] = df_jugadas['extra'].astype(int)

min_time = df_jugadas['timestamp'].min()
max_time = df_jugadas['timestamp'].max()
bins = pd.date_range(min_time, max_time + ventana, freq=f"{VENTANA_MIN}min")
df_jugadas['timestamp_bin'] = pd.cut(df_jugadas['timestamp'], bins=bins)

plt.figure()
for equipo in df_jugadas['equipo'].unique():
    df_e = df_jugadas[df_jugadas['equipo'] == equipo]
    df_sum = df_e.groupby("timestamp_bin", observed=False)["puntos"].sum().cumsum()
    df_sum.plot(label=equipo)

plt.title(f"Puntaje acumulado por equipo cada {VENTANA_MIN} min")
plt.ylabel("Puntaje acumulado")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "grafico_3_puntaje_por_equipo_tiempo.png"))

# --- 4. Equipos creados por ventana ---
df_equipos['timestamp_bin'] = pd.cut(df_equipos['timestamp'], bins=bins)
plt.figure()
df_equipos.groupby("timestamp_bin")["equipo"].count().plot(kind='bar')
plt.title(f"Equipos creados cada {VENTANA_MIN} min")
plt.ylabel("Cantidad")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "grafico_4_equipos_por_ventana.png"))

# --- 5. Jugadores creados por ventana ---
df_jugadores['timestamp_bin'] = pd.cut(df_jugadores['timestamp'], bins=bins)
plt.figure()
df_jugadores.groupby("timestamp_bin")["jugador"].count().plot(kind='bar')
plt.title(f"Jugadores creados cada {VENTANA_MIN} min")
plt.ylabel("Cantidad")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "grafico_5_jugadores_por_ventana.png"))

print("✅ Gráficos generados con éxito.")
