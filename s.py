from flask import Flask, request, jsonify
from datetime import datetime
import time
import os 
import threading

app = Flask(__name__)

VIEWER_SECRET_KEY = os.environ.get("h4shp4p1", "h4shp4p1")

status_tracker = {}
tracker_lock = threading.Lock()

@app.route('/status-check', methods=['POST'])
def receive_status():
    if not request.is_json:
        return jsonify({"message": "Invalid format"}), 400

    data = request.get_json()
    user_id = data.get('user_id', 'UNKNOWN')
    status = data.get('status', 'unknown')
    ip_addr = data.get('ip', 'N/A')
    server_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with tracker_lock:
        status_tracker[user_id] = {
            "status": status,
            "ip": ip_addr,
            "last_seen": server_time,
            "client_status": status
        }
    
    print(f"[{server_time}] CLIENT DATA: {user_id} - {status.upper()} from {ip_addr}")
    return jsonify({"message": "Status received and stored"}), 200

@app.route('/live-status', methods=['GET'])
def get_live_status():
    auth_key = request.args.get('key')
    
    if auth_key != VIEWER_SECRET_KEY:
        return jsonify({"error": "Authentication Failed. Invalid key parameter."}), 401

    HEARTBEAT_TIMEOUT = 10
    current_timestamp = time.time()
    live_report = {}
    
    with tracker_lock:
        for user_id, entry in status_tracker.items():
            last_seen_dt = datetime.strptime(entry["last_seen"], "%Y-%m-%d %H:%M:%S")
            last_seen_ts = last_seen_dt.timestamp()
            
            if entry["client_status"] == "offline":
                current_status = "OFFLINE (Exit)"
            elif (current_timestamp - last_seen_ts) > HEARTBEAT_TIMEOUT:
                current_status = "TIMED OUT (Offline)"
            else:
                current_status = "ONLINE (Active)"
            
            live_report[user_id] = {
                "live_status": current_status,
                "ip": entry["ip"],
                "last_signal": entry["last_seen"]
            }
        
    return jsonify(live_report)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
