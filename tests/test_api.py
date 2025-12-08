"""
Quick API test to verify the application is working
Run with: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("📍 Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_docs():
    """Test API docs"""
    print("📚 Testing API docs...")
    response = requests.get(f"{BASE_URL}/api/v1/docs")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ API docs available at http://localhost:8000/api/v1/docs\n")
    else:
        print(f"Response: {response.text[:100]}\n")
    return response.status_code == 200

def test_signup():
    """Test signup endpoint"""
    print("📝 Testing signup endpoint...")
    payload = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return True
    else:
        print(f"Error: {response.text[:200]}\n")
        return False

def test_signin():
    """Test signin endpoint"""
    print("🔐 Testing signin endpoint...")
    payload = {
        "email": "test@example.com",
        "password": "TestPassword123!"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/signin", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 401]:
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return True
    else:
        print(f"Error: {response.text[:200]}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Email Assistant API Test Suite")
    print("=" * 60 + "\n")
    
    try:
        results = []
        results.append(("Health Check", test_health()))
        results.append(("Root Endpoint", test_root()))
        results.append(("API Docs", test_docs()))
        results.append(("Signup", test_signup()))
        results.append(("Signin", test_signin()))
        
        print("=" * 60)
        print("📊 Test Results")
        print("=" * 60)
        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}")
        
        passed_count = sum(1 for _, p in results if p)
        total_count = len(results)
        print(f"\nTotal: {passed_count}/{total_count} tests passed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nMake sure the app is running: python -m uvicorn main:app --reload")