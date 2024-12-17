import os
import httpx
import asyncio
from fastapi import FastAPI, Request

app = FastAPI()

# ==========================
# Konfiguracja Capital.com API
# ==========================
CAPITAL_API_URL = "https://api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY", "YOUR_CAPITAL_API_KEY")

# ==========================
# Funkcja autoryzacji w Capital.com
# ==========================
async def get_auth_headers():
    """
    Pobiera nagłówki autoryzacyjne do Capital.com API.
    """
    return {
        "X-CAP-API-KEY": CAPITAL_API_KEY,
        "Content-Type": "application/json"
    }

# ==========================
# Funkcja do wysyłania zleceń
# ==========================
async def send_to_capital(endpoint: str, payload: dict):
    headers = await get_auth_headers()
    async with httpx.AsyncClient() as client:
        url = f"{CAPITAL_API_URL}/{endpoint}"
        response = await client.post(url, json=payload, headers=headers)
        return response.json()

# ==========================
# Endpoint odbierający sygnały z TradingView
# ==========================
@app.post("/webhook")
async def webhook(request: Request):
    """
    Odbiera sygnały z TradingView i wykonuje akcje na Capital.com.
    """
    data = await request.json()
    action = data.get("action")  # BUY, SELL, CLOSE
    symbol = data.get("symbol", "US100")
    size = data.get("size", 1)
    tp = data.get("tp")
    sl = data.get("sl")

    print(f"Otrzymano: {action}, Symbol: {symbol}, Rozmiar: {size}, TP: {tp}, SL: {sl}")

    payload = {
        "epic": symbol,
        "direction": action.upper(),
        "size": size,
        "orderType": "MARKET",
        "currencyCode": "USD",
        "limitLevel": tp,
        "stopLevel": sl
    }

    if action.upper() in ["BUY", "SELL"]:
        response = await send_to_capital("positions", payload)
        return {"status": f"{action.upper()} zlecenie wysłane", "response": response}
    elif action.upper() == "CLOSE":
        response = await send_to_capital(f"positions/close", payload)
        return {"status": "Zamknięto pozycję", "response": response}
    else:
        return {"error": "Niepoprawna akcja"}

# ==========================
# Mechanizm podtrzymania serwera
# ==========================
async def keep_alive():
    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/")
                print(f"Keep-Alive: {response.status_code}")
            except Exception as e:
                print(f"Błąd Keep-Alive: {e}")
        await asyncio.sleep(48)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

# ==========================
# Endpoint testowy
# ==========================
@app.get("/")
async def root():
    return {"message": "Serwer działa prawidłowo - TradingView & Capital.com"}
