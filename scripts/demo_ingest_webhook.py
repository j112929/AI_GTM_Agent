import requests
import json
import time

def simulate_apollo_push():
    """
    Simulates Apollo.io or a similar tool pushing a new lead to our API.
    """
    url = "http://localhost:8000/leads"
    
    # Payload similar to what an enriched CSV or API response might look like
    payload = {
        "name": "Sarah Connor",
        "company": "SkyNet Defense Systems",
        "email": "sarah.connor@skynet.example.com",
        "linkedin": "https://linkedin.com/in/sarahconnor-demo",
        "source": "Apollo-V1-Webhook"
    }
    
    print(f"📡 Simulating webhook push from Apollo to {url}...")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Success! Lead ingested.")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect. Is the backend server running?")

if __name__ == "__main__":
    simulate_apollo_push()
