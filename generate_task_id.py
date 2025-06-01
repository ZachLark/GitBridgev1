import hashlib
import json
import os
from typing import Union, Dict, Any

def generate_sha256(data: Union[str, Dict[str, Any]]) -> str:
    """
    Generate SHA256 hash from input data.

    Args:
        data (Union[str, Dict[str, Any]]): Input data to hash. Can be a string or a dictionary.

    Returns:
        str: Hexadecimal representation of the SHA256 hash.

    Raises:
        TypeError: If data cannot be serialized to a string for hashing.
    """
    if not isinstance(data, (str, dict)):
        raise TypeError("Input data must be a string or dictionary")
    if not isinstance(data, str):
        data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def validate_task_id(task_data: Dict[str, Any], expected_task_id: str) -> bool:
    """
    Validate the task_id in task_data against the expected_task_id.

    Args:
        task_data (Dict[str, Any]): Task data to hash for validation.
        expected_task_id (str): Expected SHA256 hash to compare against.

    Returns:
        bool: True if the computed task_id matches the expected_task_id, False otherwise.
    """
    computed_task_id = generate_sha256(task_data)
    return computed_task_id == expected_task_id

def update_task_template(template_path: str, description: str, assignee: str) -> str:
    """
    Update task_template.json with a new task_id based on description and assignee.

    This function follows the MAS Lite Protocol v2.1 for task structure, ensuring
    task_id is generated using SHA256 hashing of task fields.

    Args:
        template_path (str): Path to the task_template.json file.
        description (str): Task description.
        assignee (str): Task assignee.

    Returns:
        str: The generated task_id.

    Raises:
        FileNotFoundError: If the template_path does not exist.
        ValueError: If description or assignee is empty.
        json.JSONDecodeError: If the JSON file is invalid.
        IOError: If there are issues reading or writing the file.
    """
    # Input validation
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    if not description or not description.strip():
        raise ValueError("Description cannot be empty")
    if not assignee or not assignee.strip():
        raise ValueError("Assignee cannot be empty")

    # Load the existing task template
    try:
        with open(template_path, 'r') as f:
            task_template = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {template_path}: {str(e)}", e.doc, e.pos)
    except IOError as e:
        raise IOError(f"Error reading {template_path}: {str(e)}")

    # Create a dictionary of fields to hash (excluding task_id)
    task_data = {
        "description": description,
        "assignee": assignee,
        "max_cycles": task_template["max_cycles"],
        "token_budget": task_template["token_budget"]
    }

    # Generate task_id
    task_template["task_id"] = generate_sha256(task_data)
    task_template["description"] = description
    task_template["assignee"] = assignee

    # Save the updated task template
    try:
        with open(template_path, 'w') as f:
            json.dump(task_template, f, indent=4)
    except IOError as e:
        raise IOError(f"Error writing to {template_path}: {str(e)}")

    return task_template["task_id"]

# Example usage
if __name__ == "__main__":
    try:
        template_path = "task_template.json"
        description = "Log out to console"
        assignee = "Grok"

        new_task_id = update_task_template(template_path, description, assignee)
        print(f"Generated task_id: {new_task_id}")

        # Validate the task_id
        with open(template_path, 'r') as f:
            task_template = json.load(f)

        task_data = {
            "description": task_template["description"],
            "assignee": task_template["assignee"],
            "max_cycles": task_template["max_cycles"],
            "token_budget": task_template["token_budget"]
        }

        is_valid = validate_task_id(task_data, task_template["task_id"])
        print(f"Task ID validation: {'Valid' if is_valid else 'Invalid'}")
    except Exception as e:
        print(f"Error during execution: {str(e)}")