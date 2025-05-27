from flask import Flask, request, jsonify
from gitappv1.gitappv1_1b import collaborate, log_message  # Import from gitappv1 subdirectory

app = Flask(__name__)

@app.route('/agent')
def agent():
    return "Agent Interface for GitBridge"

@app.route('/collaborate', methods=['GET'])
def collaborate_endpoint():
    # Get query parameters
    agent_name = request.args.get('agent_name')
    task = request.args.get('task')
    
    # Validate inputs
    if not agent_name or not task:
        return jsonify({"error": "Missing agent_name or task parameter"}), 400
     
    try:
        result = collaborate(agent_name, task)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=10002)