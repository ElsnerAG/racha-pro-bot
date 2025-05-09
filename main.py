import os
import requests
from datetime import datetime, timedelta
from config import (
    MARKETS,
    DAYS_AHEAD,
    WEIGHTS,
    TARGET_PARLAY,
    MAX_COMBINED_ODD,
    MIN_SCORE
)

def send_telegram(text: str):
    """Envía un mensaje formateado a tu bot de Telegram."""
    token = os.environ["TELEGRAM_TOKEN"]
    chat  = os.environ["CHAT_ID"]
    url   = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat,
        "text": text,
        "parse_mode": "Markdown"
    })

def fetch_api_events(sport_key: str):
    """
    Trae cuotas y mercados de tu API (TheOddsAPI u otra).
    Si la respuesta no es una lista, devuelve [] para evitar errores.
    """
    key = os.environ["ODDS_API_KEY"]
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": key,
        "regions": "eu,us",
        "markets": ",".join([m["key"] for m in MARKETS.get(sport_key, [])]),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    resp = requests.get(url, params=params).json()
    if not isinstance(resp, list):
        print(f"⚠️ Odds API error for {sport_key}: {resp}")
        return []

    events = []
    for e in resp:
        for bm in e.get("bookmakers", []):
            for mkt in bm.get("markets", []):
                if mkt.get("key") in {m["key"] for m in MARKETS.get(sport_key, [])}:
                    for outcome in mkt.get("outcomes", []):
                        # Parsear hora de inicio
                        try:
                            start = datetime.fromisoformat(
                                e["commence_time"].replace("Z", "+00:00")
                            )
                        except Exception as ex:
                            print(f"❌ Error parsing time {e.get('commence_time')}: {ex}")
                            continue

                        events.append({
                            "sport":      sport_key,
                            "home_team":  e.get("home_team"),
                            "away_team":  e.get("away_team"),
                            "start_time": start,
                            "market":     mkt.get("key"),
                            "side":       outcome.get("name"),
                            "odds":       outcome.get("price")
                        })
    return events

def fetch_stats_football(home, away, start):
    """
    Stub para estadísticas de fútbol (win_rate, xg_diff, h2h_rate, form_rate).
    Aquí implementas tu scraping o API de FootyStats, Sofascore, etc.
    """
    return {
        "win_rate_home": 0.65,
        "xg_diff":       0.5,
        "h2h_rate":      0.7,
        "form_rate":     0.6
    }

def fetch_stats_tennis(p1, p2, start):
    """
    Stub para estadísticas de tenis (win_rate_1, win_rate_2, h2h_rate, form_rate).
    Aquí implementas tu scraping o API de ATP/WTA, ITF, etc.
    """
    return {
        "win_rate_1": 0.72,
        "win_rate_2": 0.28,
        "h2h_rate":   0.6,
        "form_rate":  0.7
    }

def score_event(ev):
    """Asigna un score 0–100 al pick según las ponderaciones de WEIGHTS."""
    if ev["sport"] == "soccer":
        st = fetch_stats_football(ev["home_team"], ev["away_team"], ev["start_time"])
        base = (
            st["win_rate_home"] * WEIGHTS["win_rate"] +
            st["xg_diff"]       * WEIGHTS["xg_diff"] +
            st["h2h_rate"]      * WEIGHTS["h2h_rate"] +
            st["form_rate"]     * WEIGHTS["form_rate"]
        )
    else:
        st = fetch_stats_tennis(ev["home_team"], ev["away_team"], ev["start_time"])
        fav = st["win_rate_1"] if ev["side"] == ev["home_team"] else st["win_rate_2"]
        base = (
            fav               * WEIGHTS["win_rate"] +
            st["h2h_rate"]    * WEIGHTS["h2h_rate"] +
            st["form_rate"]   * WEIGHTS["form_rate"]
        )

    return round(base * 100, 1)

def filter_and_score(events):
    """
    Filtra eventos dentro de las próximas 24 h (ventana de DAYS_AHEAD),
    con cuota en rango y score >= MIN_SCORE. Luego ordena por score.
    """
    now = datetime.utcnow()
    window_end = now + timedelta(days=DAYS_AHEAD)
    valid = []
    for ev in events:
        if not (now <= ev["start_time"] < window_end):
            continue
        for cfg in MARKETS.get(ev["sport"], []):
            if ev["market"] == cfg["key"] and cfg["min_odd"] <= ev["odds"] <= cfg["max_odd"]:
                sc = score_event(ev)
                if sc >= MIN_SCORE:
                    ev["score"] = sc
                    valid.append(ev)
    return sorted(valid, key=lambda x: x["score"], reverse=True)

def build_parlays(picks):
    """
    Toma los 4 mejores picks y arma hasta 2 combinadas con cuota total ≈2.0.
    """
    combos = []
    top = picks[:4]
    if len(top) < 2:
        return ["🚫 No hay picks suficientes para la próxima ventana."]
    for i in (0, 2):
        if i + 1 < len(top):
            a, b = top[i], top[i + 1]
            combo_odd = round(a["odds"] * b["odds"], 3)
            if TARGET_PARLAY[0] <= combo_odd <= TARGET_PARLAY[1]:
                combos.append(
                    f"🏆 *Combo{i//2+1} ({a['sport']}+{b['sport']}):*\n"
                    f"• {a['home_team']} vs {a['away_team']} [{a['market']} @ {a['odds']}]\n"
                    f"• {b['home_team']} vs {b['away_team']} [{b['market']} @ {b['odds']}]\n"
                    f"*Total:* {combo_odd} _(scores {a['score']:.0f}+{b['score']:.0f})_"
                )
    if not combos:
        combos = ["🚫 No se encontraron combinadas óptimas."]
    return combos

def main():
    # 1) Fetch de fútbol y tenis
    all_events = []
    for sport in ("soccer", "tennis_atp", "tennis_wta"):
        all_events += fetch_api_events(sport)

    # 2) Filtrado y scoring
    scored = filter_and_score(all_events)

    # 3) Construcción de parlays
    combos = build_parlays(scored)

    # 4) Envío al bot
    now = datetime.utcnow()
    date_window = f"{now.isoformat()} → {(now + timedelta(days=DAYS_AHEAD)).isoformat()}"
    message = (
        f"*📅 Picks próximos 24 h ({date_window} UTC):*\n\n"
        + "\n\n".join(combos)
    )
    send_telegram(message)

if __name__ == "__main__":
    main()
