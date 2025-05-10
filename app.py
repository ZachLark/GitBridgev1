from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

tasks = {}

@app.route("/tasks/<task_id>/message", methods=["POST"])
def post_message(task_id):
    """
    Add a message to a task
    ---
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          id: Message
          required:
            - author
            - type
            - content
          properties:
            author:
              type: string
            type:
              type: string
            content:
              type: string
    responses:
      200:
        description: Message added successfully
    """
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
    """
    Get all messages for a task
    ---
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Task messages retrieved successfully
        schema:
          id: Task
          properties:
            task_id:
              type: string
            messages:
              type: array
              items:
                type: object
                properties:
                  author:
                    type: string
                  type:
                    type: string
                  content:
                    type: string
    """
    return jsonify({"task_id": task_id, "messages": tasks.get(task_id, [])}), 200
@app.route("/tasks/<task_id>/status", methods=["PATCH"])
def update_status(task_id):
    """
    Update the status of a task
    ---
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          properties:
            status:
              type: string
    responses:
      200:
        description: Task status updated
        schema:
          properties:
            task_id:
              type: string
            new_status:
              type: string
      404:
        description: Task not found
    """
    data = request.get_json()
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    new_status = data.get("status", "unknown")
    tasks[task_id].append({"status": new_status})
    return jsonify({"task_id": task_id, "new_status": new_status}), 200
@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """
    Delete a task and all its messages
    ---
    parameters:
      - name: task_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Task deleted successfully
        schema:
          properties:
            task_id:
              type: string
            status:
              type: string
      404:
        description: Task not found
    """
    if task_id in tasks:
        del tasks[task_id]
        return jsonify({"status": "deleted", "task_id": task_id}), 200
    else:
        return jsonify({"error": "Task not found"}), 404


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

