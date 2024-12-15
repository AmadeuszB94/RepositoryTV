from flask import Flask, request, jsonify
import threading
import requests
import os
import time

app = Flask(__name__)

# Endpoint główny do sprawdzenia działania serwera
@app.route('/')
def home():
    return "Webhook działa poprawnie!", 200

# Endpoint webhooka do obsługi zleceń z TradingView
@app.route('/api/v1/orders', methods=['POST'])
def handle_order():
    data = request.json
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    # Walidacja danych wejściowych
    if not action or not ticker or not quantity:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    # Logowanie zlecenia (dla celów testowych)
    print(f"Otrzymano zlecenie: Action={action}, Ticker={ticker}, Quantity={quantity}")

    # Zwrócenie sukcesu
    return jsonify({
        "status": "success",
        "message": "Order received",
        "data": {"action": action, "ticker": ticker, "quantity": quantity}
    }), 200

# Funkcja pingująca serwer co 48 sekund
def keep_server_alive():
    url = "https://repositorytv.onrender.com/"  # Zmień na swój URL Render
    while True:
        try:
            response = requests.get(url)
            print(f"Ping sent to {url}, status code: {response.status_code}")
        except Exception as e:
            print(f"Error during ping: {e}")
        time.sleep(48)  # Pingowanie co 48 sekund

# Uruchamianie funkcji pingującej w osobnym wątku
ping_thread = threading.Thread(target=keep_server_alive)
ping_thread.daemon = True  # Wątek kończy się wraz z główną aplikacją
ping_thread.start()

# Uruchomienie serwera Flask
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Port ustawiony przez Render
    app.run(host='0.0.0.0', port=port)
