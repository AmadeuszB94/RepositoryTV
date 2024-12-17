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
CAPITAL_API_URL = "https://demo-api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY")
CAPITAL_PASSWORD = os.getenv("CAPITAL_PASSWORD")
PING_URL = os.getenv("PING_URL", "https://repositorytv.onrender.com/")

# Sprawdzenie poprawności zmiennych środowiskowych
logger.info(f"CAPITAL_API_KEY: {CAPITAL_API_KEY}")
logger.info(f"CAPITAL_PASSWORD: {CAPITAL_PASSWORD}")


# ==========================
# Funkcja autoryzacji w Capital.com
# ==========================
async def authenticate():
    url = f"{CAPITAL_API_URL}/session"
    payload = {"identifier": CAPITAL_API_KEY, "password": CAPITAL_PASSWORD}
    headers = {"Content-Type": "application/json"}

    logger.info(f"Próba autoryzacji z URL: {url}")
    logger.info(f"Payload: {payload}")
    logger.info(f"Headers: {headers}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"Odpowiedź API: {response.status_code} - {response.text}")
            if response.status_code == 200:
                session_data = response.json()
                logger.info(f"Token sesji: {session_data.get('token')}")
                return session_data.get("token")
            else:
                logger.error(f"Błąd autoryzacji: {response.json()}")
                return None
        except Exception as e:
            logger.error(f"Wystąpił błąd podczas autoryzacji: {e}")
            return None



# ==========================
# Funkcja do wysyłania zleceń
# ==========================
async def send_to_capital(endpoint: str, payload: dict, token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"{CAPITAL_API_URL}/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"API Response ({response.status_code}): {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania żądania: {e}")
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

    if not action or not symbol:
        return {"error": "Brak wymaganych parametrów: action lub symbol"}

    logger.info(f"Otrzymano: {action}, Symbol: {symbol}, Rozmiar: {size}, TP: {tp}, SL: {sl}")

    token = await authenticate()
    if not token:
        return {"error": "Nie udało się zalogować do Capital.com"}

    payload = {"epic": symbol, "size": size, "orderType": "MARKET", "currencyCode": "USD"}
    if tp:
        payload["limitLevel"] = tp
    if sl:
        payload["stopLevel"] = sl

    if action in ["BUY", "SELL"]:
        payload["direction"] = action
        response = await send_to_capital("positions", payload, token)
        return {"status": f"{action} zlecenie wysłane", "response": response}
    else:
        return {"error": "Niepoprawna akcja"}


# ==========================
# Endpoint testowy
# ==========================
@app.get("/")
@app.head("/")  # Dodanie obsługi HEAD
async def root(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"message": "Serwer działa prawidłowo - TradingView & Capital.com"}


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
