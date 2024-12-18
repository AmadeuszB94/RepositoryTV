import os
import httpx
import asyncio
import logging
from fastapi import FastAPI, Request, Response

# ==========================
# Ustawienie logowania
# ==========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ==========================
# Konfiguracja Capital.com API
# ==========================
CAPITAL_API_URL = "https://demo-api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = os.getenv("CAPITAL_API_KEY", "M6GSDg0ESMM9Ab3B")
CAPITAL_PASSWORD = os.getenv("CAPITAL_PASSWORD", "1DawacKaske2@#!")
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
    headers = {
        "Content-Type": "application/json",
        "X-CAP-API-KEY": CAPITAL_API_KEY  # Klucz API w nagłówku
    }

    logger.info(f"Próba autoryzacji z URL: {url}")
    logger.info(f"Payload: {payload}")
    logger.info(f"Headers: {headers}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"Odpowiedź API: {response.status_code} - {response.text}")

            if response.status_code == 200:
                session_data = response.json()
                token = session_data.get("token")
                if token:
                    logger.info(f"Token sesji uzyskany: {token}")
                    return token
                else:
                    logger.error("Brak tokena w odpowiedzi API.")
            else:
                logger.error(f"Błąd autoryzacji: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Błąd podczas autoryzacji: {e}")
    return None


# ==========================
# Funkcja do wysyłania zleceń
# ==========================
async def send_to_capital(token: str, endpoint: str, payload: dict):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        url = f"{CAPITAL_API_URL}/{endpoint}"
        try:
            response = await client.post(url, json=payload, headers=headers)
            logger.info(f"API Response ({response.status_code}): {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"Błąd wysyłania zlecenia: {e}")
            return {"error": str(e)}

# ==========================
# Endpoint odbierający sygnały z TradingView
# ==========================
@app.post("/webhook")
async def webhook(request: Request):
    logger.info("Otrzymano żądanie webhooka.")
    
    token = await authenticate()
    if not token:
        logger.error("Nie udało się uzyskać tokena sesji. Autoryzacja nie powiodła się.")
        return {"error": "Nie udało się zalogować do Capital.com"}
    
    logger.info(f"Token sesji uzyskany: {token}")

    data = await request.json()
    logger.info(f"Otrzymane dane: {data}")
    
    action = data.get("action", "").upper()
    symbol = data.get("symbol")
    size = data.get("size", 1)
    tp = data.get("tp")
    sl = data.get("sl")

    if not action or not symbol:
        return {"error": "Brak wymaganych parametrów: action lub symbol"}

    payload = {
        "epic": symbol,
        "size": size,
        "orderType": "MARKET",
        "currencyCode": "USD",
        "direction": action
    }
    if tp:
        payload["limitLevel"] = tp
    if sl:
        payload["stopLevel"] = sl

    # Wysyłanie zlecenia
    response = await send_to_capital(token, "positions", payload)
    return {"status": f"{action} zlecenie wysłane", "response": response}

# ==========================
# Obsługa metody HEAD dla /webhook
# ==========================
@app.head("/webhook")
async def webhook_head():
    return Response(status_code=200)

# ==========================
# Endpoint testowy
# ==========================
@app.get("/")
async def root():
    return {"message": "Serwer działa prawidłowo - TradingView & Capital.com"}

# ==========================
# Obsługa metody HEAD dla /
# ==========================
@app.head("/")
async def root_head():
    return Response(status_code=200)

import asyncio
import httpx

# Funkcja pingująca serwer
async def keep_alive():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(PING_URL)
                logger.info(f"Ping na {PING_URL}: {response.status_code}")
        except Exception as e:
            logger.error(f"Błąd podczas pingowania serwera: {e}")
        
        # Odczekaj 45 sekund
        await asyncio.sleep(45)

# Uruchomienie pętli pingującej
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

