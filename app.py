from flask import Flask, request, jsonify
import requests
import threading
import time
import logging  # Dodaj import logowania

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)  # Ustaw poziom logowania na INFO
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Konfiguracja Capital.com API
CAPITAL_API_URL = "https://demo-api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = "0ZxPppptSYX7q3F5"  # Zastąp poprawnym kluczem API
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {CAPITAL_API_KEY}"
}

# Funkcja do wysyłania zleceń
def send_order(action, ticker, quantity):
    logger.info(f"Sending order: action={action}, ticker={ticker}, quantity={quantity}")
    direction = "BUY" if action.upper() == "BUY" else "SELL"
    order_data = {
        "marketId": ticker,
        "direction": direction,
        "orderType": "MARKET",
        "size": quantity,
        "timeInForce": "FILL_OR_KILL",
        "guaranteedStop": False
    }

    try:
        response = requests.post(f"{CAPITAL_API_URL}/positions", headers=HEADERS, json=order_data)
        if response.ok:
            logger.info(f"Order successful: {response.json()}")
            return {"status": "success", "data": response.json()}
        else:
            logger.error(f"Order failed: {response.text}")
            return {"status": "error", "message": response.text}
    except Exception as e:
        logger.error(f"Exception while sending order: {e}")
        return {"status": "error", "message": str(e)}

# Endpoint webhooka do TradingView
@app.route('/api/v1/orders', methods=['POST'])
def handle_order():
    data = request.json
    logger.info(f"Request received: {data}")
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    if not action or not ticker or not quantity:
        logger.error("Invalid payload received")
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    # Wysłanie zlecenia
    result = send_order(action, ticker, quantity)
    return jsonify(result)

# Funkcja pingująca Render w tle
def ping_server():
    url = "https://repositorytv.onrender.com/"
    while True:
        try:
            response = requests.get(url)
            logger.info(f"Ping sent to {url}, status: {response.status_code}")
        except Exception as e:
            logger.error(f"Ping error: {e}")
        time.sleep(48)  # Ping co 48 sekund

# Uruchomienie funkcji ping w tle
ping_thread = threading.Thread(target=ping_server)
ping_thread.daemon = True
ping_thread.start()

# Start aplikacji Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
