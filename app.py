import os
import httpx
import asyncio
from fastapi import FastAPI, Request

app = FastAPI()

# ==========================
# Konfiguracja Capital.com API
# ==========================
CAPITAL_API_URL = "https://api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = "0ZxPppptSYX7q3F5"  # Twój klucz API
PING_URL = "https://repositorytv.onrender.com/"  # Zewnętrzny URL serwera

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
    """
    Wysyła żądania POST do API Capital.com.
    """
    headers = await get_auth_headers()
    async with httpx.AsyncClient() as client:
        url = f"{CAPITAL_API_URL}/{endpoint}"
        response = await client.post(url, json=payload, headers=headers)
        print(f"Response: {response.json()}")
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
    action = data.get("action", "").upper()  # BUY, SELL, CLOSE
    symbol = data.get("symbol")
    size = data.get("size", 1)
    tp = data.get("tp")
    sl = data.get("sl")
    deal_id = data.get("dealId")  # wymagane przy CLOSE

    # Walidacja parametrów
    if not action or not symbol:
        return {"error": "Brak wymaganych parametrów: action lub symbol"}

    print(f"Otrzymano: {action}, Symbol: {symbol}, Rozmiar: {size}, TP: {tp}, SL: {sl}, DealID: {deal_id}")

    # Przygotowanie payload
    payload = {
        "epic": symbol,
        "size": size,
        "orderType": "MARKET",
        "currencyCode": "USD",
    }
    if tp:
        payload["limitLevel"] = tp
    if sl:
        payload["stopLevel"] = sl

    # Wysyłanie zleceń
    if action in ["BUY", "SELL"]:
        payload["direction"] = action
        response = await send_to_capital("positions", payload)
        return {"status": f"{action} zlecenie wysłane", "response": response}

    elif action == "CLOSE":
        if not deal_id:
            return {"error": "Brak dealId dla zamknięcia pozycji"}
        response = await send_to_capital(f"positions/{deal_id}", payload)
        return {"status": "Zamknięto pozycję", "response": response}

    else:
        return {"error": "Niepoprawna akcja"}

# ==========================
# Mechanizm podtrzymania serwera
# ==========================
async def keep_alive():
    """
    Wysyła ping do serwera, aby podtrzymać aktywność.
    """
    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(PING_URL)
                print(f"Keep-Alive: {response.status_code}")
            except Exception as e:
                print(f"Błąd Keep-Alive: {e}")
        await asyncio.sleep(40)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

# ==========================
# Endpoint testowy
# ==========================
@app.get("/")
async def root():
    return {"message": "Serwer działa prawidłowo - TradingView & Capital.com"}
