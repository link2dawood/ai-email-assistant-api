import asyncio
import httpx
import time
import random
import string

BASE_URL = "http://localhost:8002/api/v1/auth"

def generate_random_email():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

async def test_signup():
    email = generate_random_email()
    payload = {
        "email": email,
        "password": "Password123",
        "name": "Test User"
    }
    
    print(f"🚀 Testing Signup with {email}...")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/signup", json=payload)
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏱️ Time taken: {duration:.2f} seconds")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Signup Successful")
                print(response.json())
            else:
                print("❌ Signup Failed")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Exception Type: {type(e)}")
            print(f"❌ Exception: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(test_signup())
