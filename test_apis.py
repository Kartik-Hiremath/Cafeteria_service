"""
Script to test the Cafeteria Service APIs
Run the FastAPI server first: uvicorn app.main:app --reload

IMPORTANT: After logging in through the frontend, check the server logs for:
"Generated JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

Copy that JWT token and paste it below.
"""
import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

# PASTE YOUR JWT TOKEN HERE (from server logs after login)
# Look for: "Generated JWT token: ..."
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYXJ2ZWVuLmthdXJAaWJtLmNvbSIsIm5hbWUiOiJIYXJ2ZWVuIEthdXIiLCJleHAiOjE3NzAwMTkyNTJ9.FZmroVE4O4ueVu0rFbHbdvzLWSirerIzjfALMQy6HlM"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_apis():
    """Test all the APIs"""
    
    print(f"\n🔑 Using token: {TOKEN[:50]}...")
    
    # 1. Test Seat Availability
    print("\n🪑 Testing Seat Availability...")
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    
    params = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    response = requests.get(f"{BASE_URL}/seats/availability", params=params)
    print_response("1. Seat Availability API", response)
    
    # 2. Test Create Booking
    print("\n📝 Testing Create Booking...")
    booking_data = {
        "seat_number": 42,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    response = requests.post(
        f"{BASE_URL}/bookings/create",
        params={"token": TOKEN},
        json=booking_data
    )
    print_response("2. Create Booking API", response)
    
    # 3. Test Upcoming Bookings
    print("\n📅 Testing Upcoming Bookings...")
    response = requests.get(
        f"{BASE_URL}/bookings/upcoming",
        params={"token": TOKEN}
    )
    print_response("3. Upcoming Bookings API", response)
    
    # 4. Test Current Bookings
    print("\n⏰ Testing Current Bookings...")
    response = requests.get(
        f"{BASE_URL}/bookings/current",
        params={"token": TOKEN}
    )
    print_response("4. Current Bookings API", response)
    
    print("\n✅ All API tests completed!")
    print("\n💡 Tips:")
    print("   - Check seat availability before booking")
    print("   - Use the token from login for authenticated endpoints")
    print("   - Manager balance will be deducted by $3 per booking")

if __name__ == "__main__":
    print("🚀 Starting API Tests...")
    print(f"📍 Base URL: {BASE_URL}")
    print("\n⚠️  Make sure the FastAPI server is running:")
    print("   uvicorn app.main:app --reload")
    
    input("\nPress Enter to start testing...")
    
    try:
        test_apis()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("   Make sure the FastAPI server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")

# Made with Bob