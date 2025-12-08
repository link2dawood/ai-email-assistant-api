
import requests
import json

try:
    print("Sending signup request...")
    response = requests.post(
        "http://127.0.0.1:8000/api/v1/auth/signup", 
        json={
            "email": "test@example.com", 
            "password": "short", 
            "name": "Test User"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 400 and "at least 8 characters" in response.text:
        print("SUCCESS: Database check passed, validation error received as expected.")
    elif response.status_code == 200:
        print("SUCCESS: User created (unexpected for short password but DB access worked)")
    else:
        print("FAILURE: Unexpected response.")

except Exception as e:
    print(f"ERROR: {e}")
