import os
import requests

def send_telegram(msg: str):
    token = os.environ['TELEGRAM_TOKEN']
    chat  = os.environ['CHAT_ID']
    url   = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={'chat_id': chat, 'text': msg})

def fetch_events():
    # → tu scraping o llamada a API
    return []

def filter_events(events):
    # → tus filtros de cuotas/ligas
    return []

def build_parlay(picks):
    # → arma 2 parlays (strings)
    return ["Parlay 1", "Parlay 2"]

def main():
    events  = fetch_events()
    picks   = filter_events(events)
    parlays = build_parlay(picks)
    for p in parlays:
        send_telegram(p)

if __name__ == '__main__':
    main()
