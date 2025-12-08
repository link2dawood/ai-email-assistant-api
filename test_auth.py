import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_signup():
    """Test user signup"""
    print("\n1️⃣ Testing Signup...")
    response = requests.post(f"{BASE_URL}/signup", json={
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "name": "New User"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User created: {data['user']['email']}")
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_signin():
    """Test user signin"""
    print("\n2️⃣ Testing Signin...")
    response = requests.post(f"{BASE_URL}/signin", json={
        "email": "newuser@example.com",
        "password": "SecurePass123"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logged in: {data['user']['email']}")
        return data['access_token']
    else:
        print(f"❌ Error: {response.json()}")
        return None

def test_get_me(token):
    """Test get current user"""
    print("\n3️⃣ Testing Get Current User...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User info retrieved:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.json()}")

def test_forgot_password():
    """Test forgot password"""
    print("\n4️⃣ Testing Forgot Password...")
    response = requests.post(f"{BASE_URL}/forgot-password", json={
        "email": "newuser@example.com"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_google_oauth():
    """Test Google OAuth URL generation"""
    print("\n5️⃣ Testing Google OAuth...")
    response = requests.get(f"{BASE_URL}/google")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Auth URL: {data['auth_url'][:100]}...")
    else:
        print(f"❌ Error: {response.json()}")

def run_all_tests():
    """Run all authentication tests"""
    print("="*50)
    print("🔐 Authentication API Tests")
    print("="*50)
    
    # Test signup
    token = test_signup()
    
    # Test signin
    if not token:
        token = test_signin()
    
    # Test authenticated endpoints
    if token:
        test_get_me(token)
    
    # Test other endpoints
    test_forgot_password()
    test_google_oauth()
    
    print("\n" + "="*50)
    print("✅ All tests completed!")
    print("="*50)

if __name__ == "__main__":
    run_all_tests()