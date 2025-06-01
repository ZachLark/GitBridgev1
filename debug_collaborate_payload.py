import json
import requests

# Simulate the request sent by mas_delegate.py
def debug_payload():
    """Debug the payload sent to /collaborate and suggest fixes."""
    # The expected payload from sample_task_template.json
    payload = {
        "task_id": "8fdc386f1e8b2786f774a96a9f2649b10600f7d66f84620ee9e22286ebcb294d",
        "description": "Draft Developer Guide Section 3",
        "assignee": "ChatGPT",
        "max_cycles": 10,
        "token_budget": 5000
    }
    
    print("Debugging payload:")
    print(f"Payload: {payload}")
    
    # Check types of each field
    for key, value in payload.items():
        print(f"Field '{key}': Value = {value}, Type = {type(value)}")
    
    # Send the request to /collaborate
    api_url = "http://127.0.0.1:10002/collaborate"
    try:
        response = requests.post(api_url, json=payload, timeout=5)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {str(e)}")

    # Suggest fixes based on the response
    if response.status_code == 400:
        print("400 Bad Request detected. Possible issues:")
        print("- Type mismatch: Ensure max_cycles and token_budget are sent as integers, not strings.")
        print("- Missing fields: Verify all required fields are present and non-empty.")
        print("Suggested fix for mas_delegate.py:")
        print("- Open mas_delegate.py and ensure the payload is constructed with correct types:")
        print("  payload = {")
        print("      'task_id': task['task_id'],")
        print("      'description': task['description'],")
        print("      'assignee': task['assignee'],")
        print("      'max_cycles': int(task['max_cycles']),")
        print("      'token_budget': int(task['token_budget'])")
        print("  }")
        print("Suggested fix for agent_api.py:")
        print("- Open agent_api.py and add type conversion before validation:")
        print("  max_cycles = int(data.get('max_cycles')) if data.get('max_cycles') is not None else None")
        print("  token_budget = int(data.get('token_budget')) if data.get('token_budget') is not None else None")

if __name__ == "__main__":
    debug_payload()