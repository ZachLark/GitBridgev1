import logging
import json
from flask import Flask, request, jsonify, send_file
from gitappv1.gitappv1_1b import collaborate, log_message  # Import from gitappv1 subdirectory

# Configure logging to output to console (stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def serve_ui():
    return send_file('index.html')

@app.route('/agent')
def agent():
    return "Agent Interface for GitBridge"

@app.route('/collaborate', methods=['POST'])
def collaborate_endpoint():
    # Log the raw request data for debugging
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Raw request data: {request.get_data(as_text=True)}")

    # Try to get JSON payload
    try:
        data = request.get_json(silent=True)
        if data is None:
            # Fallback to manually parse the raw data
            raw_data = request.get_data(as_text=True)
            data = json.loads(raw_data) if raw_data else {}
    except Exception as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Extract agent_name and task
    agent_name = data.get('agent_name')
    task = data.get('task')
    
    # Log the incoming request
    logger.info(f'Received POST request to /collaborate with agent_name="{agent_name}", task="{task}"')
    
    # Validate inputs
    if not agent_name or not task:
        logger.error('Missing agent_name or task in request body')
        return jsonify({"error": "Missing agent_name or task in request body"}), 400
    
    # Call the collaborate function from gitappv1_1b.py
    try:
        result = collaborate(agent_name, task)
        logger.info(f'Successful collaboration: {result}')
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.error(f'Error during collaboration: {str(e)}')
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10002)