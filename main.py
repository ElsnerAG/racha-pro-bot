import os
import requests
from datetime import datetime, timedelta, timezone
from config import (
    SOCCER_LEAGUES,
    TENNIS_TOURNAMENTS,
    MARKETS,
    DAYS_AHEAD,
    WEIGHTS,
    TARGET_PARLAY,
    MAX_COMBINED_ODD,
    MIN_SCORE
)

def send_telegram(text: str):
    token = os.environ["TELEGRAM_TOKEN"]
    chat  = os.environ["CHAT_ID"]
    url   = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat,
        "text": text,
        "parse_mode": "Markdown"
    })

def fetch_events_for_sport(sport_key: str, markets_cfg: list):
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
        print(f"⚠️ API error for {sport_key}: {resp}")
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
                        except:
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

# --- Stubs de estadísticas, reemplázalos con tu scraping/API real ---
def fetch_stats_football(home, away, start):
    return {"win_rate_home":0.65,"xg_diff":0.5,"h2h_rate":0.7,"form_rate":0.6}

def fetch_stats_tennis(p1, p2, start):
    return {"win_rate_1":0.72,"win_rate_2":0.28,"h2h_rate":0.6,"form_rate":0.7}

def score_event(ev: dict):
    if ev["sport"] in SOCCER_LEAGUES:
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
            fav                * WEIGHTS["win_rate"] +
            st["h2h_rate"]     * WEIGHTS["h2h_rate"] +
            st["form_rate"]    * WEIGHTS["form_rate"]
        )
    return round(base * 100, 1)

def filter_and_score(events: list):
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=DAYS_AHEAD)
    valid = []
    for ev in events:
        if not (now <= ev["start_time"] < window_end):
            continue
        root = "soccer" if ev["sport"] in SOCCER_LEAGUES else ev["sport"]
        for cfg in MARKETS.get(root, []):
            if ev["market"] == cfg["key"] and cfg["min_odd"] <= ev["odds"] <= cfg["max_odd"]:
                sc = score_event(ev)
                if sc >= MIN_SCORE:
                    ev["score"] = sc
                    valid.append(ev)
    return sorted(valid, key=lambda x: x["score"], reverse=True)

def build_parlays(picks: list):
    combos = []
    top = picks[:4]
    if len(top) < 2:
        return ["🚫 No hay picks suficientes en la ventana."]
    for i in (0, 2):
        if i+1 < len(top):
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
    # 1) Fetch eventos
    events = []
    for lg in SOCCER_LEAGUES:
        events += fetch_events_for_sport(lg, MARKETS["soccer"])
    for tn in TENNIS_TOURNAMENTS:
        events += fetch_events_for_sport(tn, MARKETS[tn])

    # 2) Filtrar y puntuar
    scored = filter_and_score(events)

    # 3) Crear parlays
    combos = build_parlays(scored)

    # 4) Enviar a Telegram
    now = datetime.now(timezone.utc)
    win = f"{now.isoformat()} → {(now + timedelta(days=DAYS_AHEAD)).isoformat()}"
    text = f"*📅 Picks próximas 24 h ({win} UTC):*\n\n" + "\n\n".join(combos)
    send_telegram(text)

if __name__ == "__main__":
    main()
