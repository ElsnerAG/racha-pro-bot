from datetime import timedelta

# 1. Ligas de fútbol a monitorizar
SOCCER_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_usa_mls",
    # añade más claves de tu JSON según necesites
]

# 2. Torneos de tenis a monitorizar
TENNIS_TOURNAMENTS = [
    "tennis_atp_italian_open",
    "tennis_wta_italian_open",
    # añade más claves si quieres cubrir otros torneos
]

# 3. Mercados y rangos de cuota ideales
MARKETS = {
    "soccer": [
        {"key": "h2h",     "min_odd": 1.30, "max_odd": 1.45},  # Ganador 1X2
        {"key": "spreads", "min_odd": 1.30, "max_odd": 1.45},  # Handicap asiático
        {"key": "totals",  "min_odd": 1.30, "max_odd": 1.45},  # Over/Under goles
    ],
    # Para tenis sólo usamos h2h (equipo ganador). Si tu API soporta spreads/totals, añádelos aquí.
    "tennis_atp_italian_open": [
        {"key": "h2h",     "min_odd": 1.30, "max_odd": 1.45},
    ],
    "tennis_wta_italian_open": [
        {"key": "h2h",     "min_odd": 1.30, "max_odd": 1.45},
    ],
}

# 4. Analizar partidos dentro de las próximas 24 h
DAYS_AHEAD = 1

# 5. Cuota total deseada para cada parlay
TARGET_PARLAY    = (1.90, 2.10)
MAX_COMBINED_ODD = 2.10

# 6. Score mínimo para considerar un pick
MIN_SCORE = 50

# 7. Ponderaciones para el score
WEIGHTS = {
    "win_rate":  0.4,
    "xg_diff":   0.2,
    "h2h_rate":  0.2,
    "form_rate": 0.2,
}
