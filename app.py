import os
import httpx
import asyncio
import logging
from fastapi import FastAPI, Request, Response

# Ustawienie logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ==========================
# Konfiguracja Capital.com API
# ==========================
CAPITAL_API_URL = "https://api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY", "0ZxPppptSYX7q3F5")
PING_URL = os.getenv("PING_URL", "https://repositorytv.onrender.com/")  # Dynamiczny URL

# ==========================
# Funkcja autoryzacji w Capital.com
# ==========================
async def get_auth_headers():
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
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"API Response ({response.status_code}): {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return {"error": str(e)}

# ==========================
# Endpoint odbierający sygnały z TradingView
# ==========================
@app.post("/webhook")
@app.head("/webhook")  # Dodanie obsługi HEAD
async def webhook(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)

    data = await request.json()
    action = data.get("action", "").upper()
    symbol = data.get("symbol")
    size = data.get("size", 1)
    tp = data.get("tp")
    sl = data.get("sl")
    deal_id = data.get("dealId")

    if not action or not symbol:
        return {"error": "Brak wymaganych parametrów: action lub symbol"}

    logger.info(f"Otrzymano: {action}, Symbol: {symbol}, Rozmiar: {size}, TP: {tp}, SL: {sl}, DealID: {deal_id}")

    payload = {"epic": symbol, "size": size, "orderType": "MARKET", "currencyCode": "USD"}
    if tp: payload["limitLevel"] = tp
    if sl: payload["stopLevel"] = sl

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
    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(PING_URL)
                logger.info(f"Keep-Alive: {response.status_code}")
            except Exception as e:
                logger.error(f"Błąd Keep-Alive: {e}")
        await asyncio.sleep(45)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

# ==========================
# Endpoint testowy
# ==========================
@app.get("/")
@app.head("/")  # Dodanie obsługi HEAD
async def root(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"message": "Serwer dziala prawidlowo - TradingView & Capital.com"}

# ==========================
# Handler błędu 405
# ==========================
@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return Response(content="Metoda HTTP nie jest obsługiwana dla tego endpointu", status_code=405)
