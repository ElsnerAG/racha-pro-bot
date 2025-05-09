from datetime import timedelta

# 1. Define aquí las ligas de fútbol que quieres monitorizar
SOCCER_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_usa_mls",
    # añade más claves de tu JSON si quieres cubrir otras ligas
]

# 2. Define aquí los torneos de tenis que quieres monitorizar
TENNIS_TOURNAMENTS = [
    "tennis_atp_italian_open",
    "tennis_wta_italian_open",
    # añade más claves de tu JSON si quieres cubrir otros torneos
]

# 3. Mercados con rangos de cuota parciales ideales por deporte/mercado
MARKETS = {
    "soccer": [
        {"key": "h2h",        "min_odd": 1.30, "max_odd": 1.45},  # Ganador 1X2
        {"key": "spreads",    "min_odd": 1.30, "max_odd": 1.45},  # Handicap asiático ±0.5
        {"key": "totals",     "min_odd": 1.30, "max_odd": 1.45},  # Over/Under goles
    ],
    "tennis_atp_italian_open": [
        {"key": "h2h",       "min_odd": 1.30, "max_odd": 1.45},  # Ganador partido
        {"key": "set_line",  "min_odd": 1.35, "max_odd": 1.50},  # Handicap de sets
    ],
    "tennis_wta_italian_open": [
        {"key": "h2h",       "min_odd": 1.30, "max_odd": 1.45},
        {"key": "set_line",  "min_odd": 1.35, "max_odd": 1.50},
    ],
}

# 4. Ventana de partidos a analizar (24 h desde la ejecución)
DAYS_AHEAD = 1

# 5. Rango de cuota total combinado (≈2.0)
TARGET_PARLAY    = (1.90, 2.10)
MAX_COMBINED_ODD = 2.10

# 6. Umbral mínimo de “confianza” para un pick (0–100)
MIN_SCORE = 50

# 7. Ponderaciones para calcular el “score” de cada pick
WEIGHTS = {
    "win_rate":  0.4,  # % victorias recientes
    "xg_diff":   0.2,  # diferencial de goles esperados
    "h2h_rate":  0.2,  # racha head-to-head
    "form_rate": 0.2,  # forma reciente
}
