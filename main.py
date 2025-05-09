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

def fetch_sports_by_group(group_name: str):
    """Devuelve la lista de sport_key de la API cuya group == group_name."""
    key = os.environ["ODDS_API_KEY"]
    url = "https://api.the-odds-api.com/v4/sports"
    resp = requests.get(url, params={"apiKey": key}).json()
    if not isinstance(resp, list):
        print(f"⚠️ Error fetching sports list: {resp}")
        return []
    return [s["key"] for s in resp if s.get("group","").lower() == group_name.lower()]

def fetch_events_for_sport(sport_key: str, markets_cfg: list):
    """Trae eventos de un sport_key específico usando markets_cfg."""
    key = os.environ["ODDS_API_KEY"]
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": key,
        "regions": "eu,us",
        "markets": ",".join([m["key"] for m in markets_cfg]),
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
                if mkt.get("key") in {m["key"] for m in markets_cfg}:
                    for outcome in mkt.get("outcomes", []):
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

def fetch_api_events(group_key: str):
    """
    Si group_key == "soccer", trae todas las ligas de fútbol,
    si es tenis, trae solo ATP o WTA.
    """
    events = []
    if group_key == "soccer":
        leagues = fetch_sports_by_group("Soccer")
        for lk in leagues:
            events += fetch_events_for_sport(lk, MARKETS["soccer"])
    else:
        # Para tenis_atp y tennis_wta
        events += fetch_events_for_sport(group_key, MARKETS[group_key])
    return events

def fetch_stats_football(home, away, start):
    """Stub: stats de fútbol (win_rate, xg_diff, h2h_rate, form_rate)."""
    return {"win_rate_home":0.65,"xg_diff":0.5,"h2h_rate":0.7,"form_rate":0.6}

def fetch_stats_tennis(p1, p2, start):
    """Stub: stats de tenis (win_rate_1, win_rate_2, h2h_rate, form_rate)."""
    return {"win_rate_1":0.72,"win_rate_2":0.28,"h2h_rate":0.6,"form_rate":0.7}

def score_event(ev: dict):
    """Calcula un score 0–100 basado en WEIGHTS, detectando deporte por key."""
    if ev["sport"].startswith("soccer"):
        st = fetch_stats_football(ev["home_team"], ev["away_team"], ev["start_time"])
        base = (
            st["win_rate_home"] * WEIGHTS["win_rate"] +
            st["xg_diff"]       * WEIGHTS["xg_diff"] +
            st["h2h_rate"]      * WEIGHTS["h2h_rate"] +
            st["form_rate"]     * WEIGHTS["form_rate"]
        )
    elif ev["sport"].startswith("tennis"):
        st = fetch_stats_tennis(ev["home_team"], ev["away_team"], ev["start_time"])
        fav = st["win_rate_1"] if ev["side"] == ev["home_team"] else st["win_rate_2"]
        base = (
            fav                * WEIGHTS["win_rate"] +
            st["h2h_rate"]     * WEIGHTS["h2h_rate"] +
            st["form_rate"]    * WEIGHTS["form_rate"]
        )
    else:
        return 0
    return round(base * 100, 1)

def filter_and_score(events: list):
    """
    Filtra eventos en las próximas 24 h (hasta NOW + DAYS_AHEAD),
    por cuota y score, y los ordena de mayor a menor score.
    """
    now = datetime.utcnow()
    window_end = now + timedelta(days=DAYS_AHEAD)
    valid = []
    for ev in events:
        if not (now <= ev["start_time"] < window_end):
            continue
        # Determina cfg base
        root = "soccer" if ev["sport"].startswith("soccer") else ev["sport"]
        if root not in MARKETS:
            continue
        for cfg in MARKETS[root]:
            if ev["market"] == cfg["key"] and cfg["min_odd"] <= ev["odds"] <= cfg["max_odd"]:
                sc = score_event(ev)
                if sc >= MIN_SCORE:
                    ev["score"] = sc
                    valid.append(ev)
    return sorted(valid, key=lambda x: x["score"], reverse=True)

def build_parlays(picks: list):
    """
    Toma los 4 mejores picks y arma hasta 2 parlays con cuota ≈2.0.
    """
    combos = []
    top = picks[:4]
    if len(top) < 2:
        return ["🚫 No hay picks suficientes en la ventana."]
    for i in (0, 2):
        if i + 1 < len(top):
            a, b = top[i], top[i+1]
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
    # 1) Traer todos los eventos de fútbol y tenis
    events = fetch_api_events("soccer") \
           + fetch_api_events("tennis_atp") \
           + fetch_api_events("tennis_wta")

    # 2) Filtrar y puntuar
    scored = filter_and_score(events)

    # 3) Construir parlays
    combos = build_parlays(scored)

    # 4) Enviar a Telegram
    now = datetime.utcnow()
    window = f"{now.isoformat()} → {(now + timedelta(days=DAYS_AHEAD)).isoformat()}"
    msg = f"*📅 Picks próximas 24 h ({window} UTC):*\n\n" + "\n\n".join(combos)
    send_telegram(msg)

if __name__ == "__main__":
    main()
