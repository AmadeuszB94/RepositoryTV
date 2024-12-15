from flask import Flask, request, jsonify
import requests
import os
import threading
import time

app = Flask(__name__)

# Konfiguracja Capital.com API
CAPITAL_API_URL = "https://demo-api-capital.backend-capital.com/api/v1"
CAPITAL_API_KEY = "0ZxPppptSYX7q3F5"  # Twój poprawny klucz API
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {CAPITAL_API_KEY}"
}

# Funkcja do wysyłania zleceń
def send_order(action, ticker, quantity):
    direction = "BUY" if action.upper() == "BUY" else "SELL"
    order_data = {
        "marketId": ticker,
        "direction": direction,
        "orderType": "MARKET",
        "size": quantity,
        "timeInForce": "FILL_OR_KILL",
        "guaranteedStop": False
    }
    response = requests.post(f"{CAPITAL_API_URL}/positions", headers=HEADERS, json=order_data)
    return {"status": "success", "data": response.json()} if response.ok else {"status": "error", "message": response.text}

# Endpoint webhooka
@app.route('/api/v1/orders', methods=['POST'])
def handle_order():
    data = request.json
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    if not action or not ticker or not quantity:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    result = send_order(action, ticker, quantity)
    return jsonify(result)

# Pingowanie Rendera co 45 sekund
def ping_server():
    url = "https://tv-capital-webhook.onrender.com"
    while True:
        try:
            requests.get(url)
            print(f"Ping sent to {url}")
        except Exception as e:
            print(f"Ping error: {e}")
        time.sleep(45)

# Uruchomienie pingu w tle
ping_thread = threading.Thread(target=ping_server)
ping_thread.daemon = True
ping_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
