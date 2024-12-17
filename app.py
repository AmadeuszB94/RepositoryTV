import httpx
from fastapi import FastAPI, Request
import asyncio

app = FastAPI()

# ==========================
# Konfiguracja API Capital.com
# ==========================
CAPITAL_API_URL = "https://api-capital.backend-capital.com"
CAPITAL_DEMO_URL = "https://demo-api-capital.backend-capital.com"
CAPITAL_API_KEY = "0ZxPppptSYX7q3F5"  # <-- Wstaw tutaj swój klucz API
IS_DEMO = True  # Ustawienie dla konta Demo (True) lub Real (False)

# ==========================
# Wybór URL na podstawie konta
# ==========================
BASE_URL = CAPITAL_DEMO_URL if IS_DEMO else CAPITAL_API_URL

# ==========================
# Funkcja do uzyskania sesji z Capital.com
# ==========================
async def start_session():
    payload = {"identifier": "YOUR_LOGIN", "password": "YOUR_PASSWORD"}
    headers = {"X-CAP-API-KEY": CAPITAL_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/session", json=payload, headers=headers)
        if response.status_code == 200:
            cst = response.headers.get("CST")
            security_token = response.headers.get("X-SECURITY-TOKEN")
            return cst, security_token
        else:
            print(f"Session start failed: {response.text}")
            return None, None

# ==========================
# Funkcja do wysyłania żądań do Capital.com
# ==========================
async def send_to_capital(endpoint: str, payload: dict, cst: str, security_token: str):
    headers = {
        "Authorization": f"Bearer {CAPITAL_API_KEY}",
        "Content-Type": "application/json",
        "CST": cst,
        "X-SECURITY-TOKEN": security_token
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/{endpoint}", json=payload, headers=headers)
        return response.json()

# ==========================
# Endpoint do odbierania sygnałów z TradingView
# ==========================
@app.post("/webhook")
async def webhook(request: Request):
    """
    Odbiera sygnały z TradingView i wykonuje odpowiednie akcje na Capital.com
    """
    data = await request.json()
    action = data.get("action")  # BUY, SELL, CLOSE
    symbol = data.get("symbol", "US100")
    size = data.get("size", 1)
    tp = data.get("tp")
    sl = data.get("sl")
    strategy = data.get("strategy", "default")
    interval = data.get("interval", "1m")

    print(f"Action: {action}, Symbol: {symbol}, Size: {size}, TP: {tp}, SL: {sl}, Strategy: {strategy}, Interval: {interval}")

    # Startowanie sesji
    cst, security_token = await start_session()
    if not cst or not security_token:
        return {"error": "Failed to start session"}

    # Obsługa akcji
    if action == "BUY":
        payload = {
            "epic": symbol,
            "direction": "BUY",
            "size": size,
            "orderType": "MARKET",
            "limitLevel": tp,
            "stopLevel": sl
        }
        response = await send_to_capital("positions", payload, cst, security_token)
        return {"status": "BUY order sent", "response": response}

    elif action == "SELL":
        payload = {
            "epic": symbol,
            "direction": "SELL",
            "size": size,
            "orderType": "MARKET",
            "limitLevel": tp,
            "stopLevel": sl
        }
        response = await send_to_capital("positions", payload, cst, security_token)
        return {"status": "SELL order sent", "response": response}

    elif action == "CLOSE":
        payload = {"epic": symbol}
        response = await send_to_capital("positions/close", payload, cst, security_token)
        return {"status": "Position closed", "response": response}

    return {"error": "Invalid action"}

# ==========================
# Mechanizm podtrzymania aktywności serwera
# ==========================
async def keep_alive():
    """
    Wysyła regularny ping do serwera, aby utrzymać go aktywnym.
    """
    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://tv-capital-webhook.onrender.com/")
                print(f"Keep-Alive Ping: {response.status_code}")
            except Exception as e:
                print(f"Keep-Alive Error: {e}")
        await asyncio.sleep(48)  # Ping co 48 sekund

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

# ==========================
# Prosty endpoint testowy
# ==========================
@app.get("/")
async def root():
    return {"message": "TradingView & Capital.com Integration Active"}
