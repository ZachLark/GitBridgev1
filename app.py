from flask import Flask, request, jsonify

app = Flask(__name__)
tasks = {}

@app.route("/tasks/<task_id>/message", methods=["POST"])
def post_message(task_id):
    data = request.get_json()
    if task_id not in tasks:
        tasks[task_id] = []
    tasks[task_id].append({
        "author": data.get("author"),
        "type": data.get("type"),
        "content": data.get("content"),
    })
    return jsonify({"status": "ok", "messages": tasks[task_id]}), 200

@app.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    return jsonify({"task_id": task_id, "messages": tasks.get(task_id, [])}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Welcome to the Atlas PALM v1.5 API.",
        "version": "1.5.0",
        "routes": [
            "/tasks/<task_id>",
            "/tasks/<task_id>/message",
            "/tasks/<task_id>/status"
        ]
    }), 200

