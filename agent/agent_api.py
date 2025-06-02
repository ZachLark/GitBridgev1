import logging
import json
from flask import Flask, request, jsonify, send_file
from flasgger import Swagger, swag_from

# Configure logging to output to console (stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Swagger
swagger = Swagger(app)

@app.route('/')
def serve_ui():
    return send_file('index.html')

@app.route('/agent')
def agent():
    return "Agent Interface for GitBridge"

@app.route('/collaborate', methods=['POST'])
@swag_from({
    'tags': ['Collaboration'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'task_id': {
                        'type': 'string',
                        'example': '8fdc386f1e8b2786f774a96a9f2649b10600f7d66f84620ee9e22286ebcb294d',
                        'description': 'Unique task identifier (SHA256 hash)'
                    },
                    'description': {
                        'type': 'string',
                        'example': 'Draft Developer Guide Section 3',
                        'description': 'Description of the task'
                    },
                    'assignee': {
                        'type': 'string',
                        'example': 'ChatGPT',
                        'description': 'Agent assigned to the task'
                    },
                    'max_cycles': {
                        'type': 'integer',
                        'example': 10,
                        'description': 'Maximum number of cycles for the task'
                    },
                    'token_budget': {
                        'type': 'integer',
                        'example': 5000,
                        'description': 'Token budget for the task'
                    }
                },
                'required': ['task_id', 'description', 'assignee', 'max_cycles', 'token_budget']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Collaboration successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'task_id': {'type': 'string', 'example': '8fdc386f1e8b2786f774a96a9f2649b10600f7d66f84620ee9e22286ebcb294d'},
                    'max_cycles': {'type': 'integer', 'example': 10},
                    'token_budget': {'type': 'integer', 'example': 5000},
                    'status': {'type': 'string', 'example': 'success'},
                    'cycle_count': {'type': 'integer', 'example': 1}
                }
            }
        },
        400: {
            'description': 'Bad request - missing or invalid input',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Missing required fields in request body'}
                }
            }
        },
        500: {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'example': 'Error during collaboration'}
                }
            }
        }
    }
})
def collaborate_endpoint():
    """Handle task delegation requests for MAS Light."""
    # Log the request headers
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Request content type: {request.content_type}")

    # Get the raw data
    raw_data = request.get_data(as_text=True)
    logger.info(f"Raw request data: {raw_data}")

    # Parse the JSON payload manually
    if not raw_data:
        logger.error("Request body is empty")
        return jsonify({"error": "Request body is empty"}), 400

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Extract and validate task details with explicit type checking
    required_fields = {
        'task_id': (str, lambda x: bool(x.strip())),
        'description': (str, lambda x: bool(x.strip())),
        'assignee': (str, lambda x: bool(x.strip())),
        'max_cycles': (int, lambda x: x > 0),
        'token_budget': (int, lambda x: x > 0)
    }

    validation_errors = []
    validated_data = {}

    for field, (expected_type, validator) in required_fields.items():
        value = data.get(field)
        if value is None:
            validation_errors.append(f"Missing field: {field}")
            continue
        
        if not isinstance(value, expected_type):
            validation_errors.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}")
            continue
        
        if not validator(value):
            validation_errors.append(f"Invalid value for {field}: {value}")
            continue
        
        validated_data[field] = value

    if validation_errors:
        error_msg = "; ".join(validation_errors)
        logger.error(f"Validation errors: {error_msg}")
        return jsonify({"error": error_msg}), 400

    # Log the validated data
    logger.info(f"Validated data: {validated_data}")

    # Construct the response
    try:
        response = {
            "task_id": validated_data["task_id"],
            "max_cycles": validated_data["max_cycles"],
            "token_budget": validated_data["token_budget"],
            "status": "success",
            "cycle_count": 1
        }
        logger.info(f'Successful collaboration: {response}')
        return jsonify(response), 200
    except Exception as e:
        logger.error(f'Error during collaboration: {str(e)}')
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10002)