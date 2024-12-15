from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Webhook działa poprawnie!", 200

@app.route('/api/v1/orders', methods=['POST'])
def handle_order():
    data = request.json
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    if not action or not ticker or not quantity:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    # Wysłanie prostego potwierdzenia dla testów
    return jsonify({"status": "success", "message": "Order received", "data": data}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render ustawia PORT na 10000
    app.run(host='0.0.0.0', port=port)
