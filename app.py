import httpx
from fastapi import FastAPI, Request
import asyncio
import json

app = FastAPI()

# ==========================
# Konfiguracja API Capital.com
# ==========================
CAPITAL_API_URL = "https://api-capital.com"
CAPITAL_API_KEY = "0ZxPppptSYX7q3F5"  # Wstaw swój klucz API tutaj

# ==========================
# Funkcja do wysyłania żądań do Capital.com
# ==========================
async def send_to_capital(endpoint: str, payload: dict):
    headers = {
        "Authorization": f"Bearer {CAPITAL_API_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get("https://tv-capital-webhook.onrender.com/")
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
    action = data.get("action")  # "BUY", "SELL", "CLOSE"
    symbol = data.get("symbol", "US100")
    size = data.get("size", 1)
    tp = data.get("tp", None)
    sl = data.get("sl", None)

    print(f"Received action: {action}, Symbol: {symbol}, Size: {size}, TP: {tp}, SL: {sl}")

    if action == "BUY":
        payload = {
            "epic": symbol,
            "direction": "BUY",
            "size": size,
            "orderType": "MARKET",
            "currencyCode": "USD",
            "limitLevel": tp,
            "stopLevel": sl
        }
        response = await send_to_capital("positions/otc", payload)
        return {"status": "BUY order sent", "response": response}

    elif action == "SELL":
        payload = {
            "epic": symbol,
            "direction": "SELL",
            "size": size,
            "orderType": "MARKET",
            "currencyCode": "USD",
            "limitLevel": tp,
            "stopLevel": sl
        }
        response = await send_to_capital("positions/otc", payload)
        return {"status": "SELL order sent", "response": response}

    elif action == "CLOSE":
        payload = {
            "epic": symbol,
            "orderType": "MARKET"
        }
        response = await send_to_capital("positions/otc/close", payload)
        return {"status": "Position closed", "response": response}

    else:
        return {"error": "Invalid action"}

# ==========================
# Prosty endpoint testowy
# ==========================
@app.get("/")
async def root():
    return {"message": "TradingView & Capital.com Integration Active"}

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
                response = await client.get("http://localhost:8000/")
                print(f"Keep-Alive Ping: {response.status_code}")
            except Exception as e:
                print(f"Keep-Alive Error: {e}")
        await asyncio.sleep(48)  # Ping co 48 sekund

# Uruchomienie taska w tle
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())
