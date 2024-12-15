from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# Endpoint do testowania
@app.route('/api/v1/orders', methods=['POST'])
def handle_order():
    data = request.json
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    if not action or not ticker or not quantity:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    return jsonify({
        "status": "success",
        "message": "Order received",
        "data": {"action": action, "ticker": ticker, "quantity": quantity}
    })

# Funkcja pingująca co 48 sekund
def keep_awake():
    while True:
        try:
            requests.get("https://repositorytv.onrender.com/")
        except Exception as e:
            print(f"Ping error: {e}")
        time.sleep(48)

# Uruchomienie pingu w tle
ping_thread = threading.Thread(target=keep_awake)
ping_thread.daemon = True
ping_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
