from flask import Flask, request, jsonify
from flasgger import Swagger
from webui.webui import webui_bp

app = Flask(__name__)
swagger = Swagger(app)

tasks = {}

app.register_blueprint(webui_bp)

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

@app.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(tasks), 200

@app.route('/debug/git-status', methods=['GET'])
def git_debug():
    import subprocess
    import os

    try:
        current_path = os.getcwd()
        git_folder_exists = os.path.isdir(os.path.join(current_path, '.git'))

        if not git_folder_exists:
            return {
                "cwd": current_path,
                "git": False,
                "message": ".git folder not found – this may not be a cloned repo"
            }

        remote_url = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=current_path).decode().strip()
        current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=current_path).decode().strip()

        return {
            "cwd": current_path,
            "git": True,
            "remote_url": remote_url,
            "branch": current_branch
        }

    except Exception as e:
        return {"error": str(e)}

@app.route('/publish', methods=['POST'])
def manual_publish():
    import base64
    import requests
    from datetime import datetime

    data = request.json
    commit_msg = data.get('commit_msg', f"Manual publish on {datetime.now().isoformat()}")
    filename = data.get('filename')
    content = data.get('content')

    if not filename or not content:
        return jsonify({"error": "Missing filename or content."}), 400

    try:
        REPO_OWNER = "ZachLark"
        REPO_NAME = "erudite-ecb-api"
        BRANCH = "main"
        GITHUB_PAT = os.getenv("GITHUB_PAT")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"

        headers = {
            "Authorization": f"Bearer {GITHUB_PAT}",
            "Accept": "application/vnd.github+json"
        }

        encoded_content = base64.b64encode(content.encode()).decode()

        payload = {
            "message": commit_msg,
            "content": encoded_content,
            "branch": BRANCH
        }

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            return jsonify({
                "status": "Success",
                "file": filename,
                "message": commit_msg
            }), 200
        else:
            return jsonify({
                "error": "GitHub API error",
                "details": response.json()
            }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port, debug=True)

