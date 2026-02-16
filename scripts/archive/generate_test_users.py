#!/usr/bin/env python3
"""
Script to generate 50 random test users for the login screen.
Run this from the project root directory.
"""

import requests
import random
import time

# List of common first and last names for realistic test users
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn",
    "Blake", "Cameron", "Dakota", "Drew", "Emery", "Finley", "Harper",
    "Hayden", "Jamie", "Kendall", "Logan", "Marley", "Noah", "Parker",
    "Peyton", "Reese", "River", "Rowan", "Sage", "Skylar", "Spencer",
    "Charlie", "Sam", "Chris", "Pat", "Dana", "Lee", "Jean", "Kim",
    "Robin", "Terry", "Tracy", "Val", "Drew", "Gail", "Jody", "Kelly",
    "Lynn", "Mel", "Ray", "Sandy", "Shannon"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott",
    "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson",
    "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips"
]

def generate_random_name():
    """Generate a random full name"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def create_user(name):
    """Create a user via the API"""
    url = "http://localhost:8000/api/users"
    payload = {"name": name}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return True, f"Created: {name}"
            else:
                return False, f"Failed: {name} - {data.get('error', 'Unknown error')}"
        else:
            return False, f"HTTP {response.status_code}: {name}"
    except requests.exceptions.RequestException as e:
        return False, f"Error: {name} - {str(e)}"

def main():
    print("=" * 60)
    print("Generating 50 Random Test Users")
    print("=" * 60)
    print()
    
    # Generate 50 unique names
    names = set()
    while len(names) < 50:
        names.add(generate_random_name())
    
    names = sorted(list(names))
    
    print(f"Generated {len(names)} unique names")
    print("Creating users...")
    print()
    
    success_count = 0
    failed_count = 0
    
    for i, name in enumerate(names, 1):
        success, message = create_user(name)
        if success:
            success_count += 1
            print(f"[{i:2d}/50] OK {message}")
        else:
            failed_count += 1
            print(f"[{i:2d}/50] FAIL {message}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    print()
    print("=" * 60)
    print(f"Summary: {success_count} created, {failed_count} failed")
    print("=" * 60)
    print()
    print("Refresh your login page to see the users!")

if __name__ == "__main__":
    main()




