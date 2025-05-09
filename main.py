import os
import requests
from datetime import datetime, timedelta
from config import MARKETS, DAYS_AHEAD, WEIGHTS, TARGET_PARLAY, MAX_COMBINED_ODD

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
    """Trae cuotas y mercados de tu API (TheOddsAPI)."""
    key = os.environ["ODDS_API_KEY"]
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": key,
        "regions": "eu,us",
        "markets": ",".join([m["key"] for m in MARKETS[sport_key]]),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    resp = requests.get(url, params=params).json()
    events = []
    for e in resp:
        for bm in e["bookmakers"]:
            for mkt in bm["markets"]:
                if mkt["key"] in {m["key"] for m in MARKETS[sport_key]}:
                    for outcome in mkt["outcomes"]:
                        events.append({
                            "sport":      sport_key,
                            "home_team":  e["home_team"],
                            "away_team":  e["away_team"],
                            "start_time": datetime.fromisoformat(e["commence_time"].replace("Z","+00:00")),
                            "market":     mkt["key"],
                            "side":       outcome["name"],
                            "odds":       outcome["price"]
                        })
    return events

def fetch_stats_football(home, away, start):
    """(Pendiente) Obtiene win_rate, xg_diff, h2h_rate y form_rate de tu fuente de stats."""
    # ➔ Aquí harías scraping/API FootyStats
    return {"win_rate_home":0.65,"xg_diff":0.5,"h2h_rate":0.7,"form_rate":0.6}

def fetch_stats_tennis(p1, p2, start):
    """(Pendiente) Obtiene win_rate_1, h2h_rate, form_rate para tenis."""
    # ➔ Scraping/API de ITF/ATP/WTA
    return {"win_rate_1":0.72,"win_rate_2":0.28,"h2h_rate":0.6,"form_rate":0.7}

def score_event(ev):
    """Calcula un score 0–100 según WEIGHTS."""
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
        fav = st["win_rate_1"] if ev["side"]==ev["home_team"] else st["win_rate_2"]
        base = (
            fav                * WEIGHTS["win_rate"] +
            st["h2h_rate"]     * WEIGHTS["h2h_rate"] +
            st["form_rate"]    * WEIGHTS["form_rate"]
        )
    return round(base * 100, 1)

def filter_and_score(events):
    """Filtra eventos de mañana por cuota + score mínimo y ordena."""
    tomorrow = (datetime.utcnow() + timedelta(days=DAYS_AHEAD)).date()
    valid = []
    for ev in events:
        if ev["start_time"].date() != tomorrow:
            continue
        for cfg in MARKETS[ev["sport"]]:
            if ev["market"]==cfg["key"] and cfg["min_odd"]<=ev["odds"]<=cfg["max_odd"]:
                sc = score_event(ev)
                if sc >= MIN_SCORE:
                    ev["score"] = sc
                    valid.append(ev)
    return sorted(valid, key=lambda x: x["score"], reverse=True)

def build_parlays(picks):
    """Toma los top 4, arma hasta 2 combinadas cercanas a cuota ≈2.0."""
    combos = []
    top = picks[:4]
    if len(top)<2:
        return ["🚫 No hay picks suficientes para mañana."]
    # Combo1: 1+2
    for i in (0,2):
        if i+1 < len(top):
            a,b = top[i], top[i+1]
            odd = round(a["odds"]*b["odds"],3)
            if TARGET_PARLAY[0] <= odd <= TARGET_PARLAY[1]:
                combos.append(
                  f"🏆 *Combo{i//2+1} ({a['sport']}+{b['sport']}):*\n"
                  f"• {a['home_team']} vs {a['away_team']} [{a['market']} @ {a['odds']}]\n"
                  f"• {b['home_team']} vs {b['away_team']} [{b['market']} @ {b['odds']}]\n"
                  f"*Total:* {odd} _(scores {a['score']:.0f}+{b['score']:.0f})_"
                )
    if not combos:
        combos = ["🚫 No se encontraron combinadas óptimas."]
    return combos

def main():
    # 1) Fetch fútbol y tenis
    ev = fetch_api_events("soccer") + \
         fetch_api_events("tennis_atp") + \
         fetch_api_events("tennis_wta")
    # 2) Filtrar y puntuar
    scored = filter_and_score(ev)
    # 3) Crear parlays
    combos = build_parlays(scored)
    # 4) Enviar
    send_telegram(
      f"*📅 Picks para mañana {(datetime.utcnow()+timedelta(days=1)).date()}:*\n\n"
      + "\n\n".join(combos)
    )

if __name__=="__main__":
    main()
