# config.py

from datetime import timedelta

# 1) Mercados y cuotas parciales por deporte
MARKETS = {
    "soccer": [
        {"key": "h2h",        "min_odd": 1.30, "max_odd": 1.45},  # Ganador 1X2
        {"key": "asian_line", "min_odd": 1.30, "max_odd": 1.45},  # AH ±0.5
        {"key": "over_under", "min_odd": 1.30, "max_odd": 1.45},  # Over/Under goles
    ],
    "tennis_atp": [
        {"key": "h2h",       "min_odd": 1.30, "max_odd": 1.45},   # Ganador partido
        {"key": "set_line",  "min_odd": 1.35, "max_odd": 1.50},   # Hándicap de sets
    ],
    "tennis_wta": [
        {"key": "h2h",       "min_odd": 1.30, "max_odd": 1.45},
        {"key": "set_line",  "min_odd": 1.35, "max_odd": 1.50},
    ],
}

# 2) Horario de ejecución:  
#    22:00 MDT (tu hora) = 04:00 UTC → cron '0 4 * * *'
CRON_NIGHTLY = "0 4 * * *"

# 3) Partido “de mañana” (1 día adelante)
DAYS_AHEAD = 1

# 4) Cuota combinada aceptable (≈2.0)
TARGET_PARLAY    = (1.90, 2.10)
MAX_COMBINED_ODD = 2.10

# 5) Scores mínimos y ponderaciones
MIN_SCORE = 50   # descarta picks muy débiles
WEIGHTS = {
    "win_rate":  0.4,  # importancia de % victorias
    "xg_diff":   0.2,  # diferencial de goles esperados
    "h2h_rate":  0.2,  # racha H2H
    "form_rate": 0.2,  # forma reciente
}
