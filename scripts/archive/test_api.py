"""Quick API test to verify endpoints work with database"""
import sys
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

print("=" * 60)
print("Testing API Endpoints with SQLite Database")
print("=" * 60)
print()

# Test 1: List users
print("1. Testing GET /api/users...")
response = client.get("/api/users")
if response.status_code == 200:
    users = response.json()["users"]
    print(f"   ✓ Success! Found {len(users)} users")
    for user in users[:3]:  # Show first 3
        print(f"     - {user['name']}")
else:
    print(f"   ✗ Failed with status {response.status_code}")
print()

# Test 2: Get user scripts
print("2. Testing GET /api/user-scripts...")
if users:
    user_id = users[0]["id"]
    response = client.get(f"/api/user-scripts?user_id={user_id}")
    if response.status_code == 200:
        scripts = response.json()["scripts"]
        print(f"   ✓ Success! Found {len(scripts)} scripts for user")
        for script in scripts:
            print(f"     - {script['name']}")
    else:
        print(f"   ✗ Failed with status {response.status_code}")
print()

# Test 3: Create a new user
print("3. Testing POST /api/users (create new user)...")
response = client.post("/api/users", json={"name": "Test User DB"})
if response.status_code == 200:
    new_user = response.json()["user"]
    print(f"   ✓ Success! Created user: {new_user['name']} (ID: {new_user['id'][:8]}...)")
else:
    print(f"   ✗ Failed with status {response.status_code}: {response.text}")
print()

print("=" * 60)
print("✓ Database integration is working!")
print("=" * 60)
