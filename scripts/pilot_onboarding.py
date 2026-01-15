import requests
import time
import sys
import json

API_URL = "http://localhost:8000"

def type_writer(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.01)
    print("")

def pilot_onboarding():
    print("==========================================")
    print("   AI GTM AGENT - PILOT ONBOARDING   ")
    print("==========================================")
    
    # 1. Configuration
    type_writer("\n[1] Configuration Phase")
    company = input("Enter your Company Name: ")
    product = input("Enter your Product One-Liner: ")
    icp_desc = input("Describe your Ideal Customer Profile (e.g., CTOs at FinTech): ")
    
    # In a real app, we'd POST this to /campaigns. For MVP, we pass it or just simulate usage.
    # We will simulate that the Agent knows this context (in reality we'd update a config or Campaign obj).
    
    # 2. Lead Generation / Import
    type_writer(f"\n[2] Generating 5 Test Leads for {icp_desc}...")
    
    # Mock leads based on ICP (simple hardcoded logic for demo variety)
    mock_leads = [
        {"name": "Sarah Connor", "company": "SkyNet Defense", "source": "Pilot"},
        {"name": "John Anderson", "company": "Matrix Soft", "source": "Pilot"},
        {"name": "Bruce Wayne", "company": "Wayne Ent", "source": "Pilot"},
        {"name": "Tony Stark", "company": "Stark Ind", "source": "Pilot"},
        {"name": "Clark Kent", "company": "Daily Planet", "source": "Pilot"},
    ]
    
    lead_ids = []
    for lead in mock_leads:
        lead["email"] = f"{lead['name'].split()[0].lower()}@{lead['company'].lower().replace(' ', '')}.com"
        # Ingest
        try:
            res = requests.post(f"{API_URL}/leads", json=lead)
            if res.status_code == 200:
                lid = res.json().get("id") or res.json().get("lead_id") # Adjust based on actual API response
                if not lid: lid = res.json().get("id") # My API returns {"id":...}
                lead_ids.append(lid)
                print(f"  -> Ingested {lead['name']}")
        except Exception:
            print("  [Error] Could not connect to API. Is server running?")
            return

    # 3. Processing
    type_writer("\n[3] AI is Analyzing & Drafting emails (Wait 5s)...")
    time.sleep(2)
    for _ in range(5):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.5)
    print(" Done!")
    
    # 4. Review
    type_writer("\n[4] Review Drafts (Fetching from Review Queue...)")
    
    try:
        res = requests.get(f"{API_URL}/leads")
        all_leads = res.json()
        drafts = [l for l in all_leads if l.get('id') in lead_ids] # Filter just ours
        
        for idx, draft in enumerate(drafts):
            print(f"\n--- Draft {idx+1} ---")
            print(f"To: {draft.get('name')} ({draft.get('company')})")
            print(f"Subject: {draft.get('subject')}")
            print(f"Body: {draft.get('body', '')[:100]}...")
            
    except Exception as e:
        print(f"Error fetching drafts: {e}")
        return

    # 5. Approval actions
    confirm = input("\n[5] Approve & Send ALL 5 drafts? (y/n): ")
    if confirm.lower() == 'y':
        type_writer("\nSending Batch Approval Request...")
        try:
            res = requests.post(f"{API_URL}/leads/batch-approve", json={"lead_ids": lead_ids})
            print("Result:", res.json())
            
            type_writer("\n[6] Success! Pilot Campaign Launched. 🚀")
            print("Check http://localhost:8000 for real-time metrics.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Pilot aborted.")

if __name__ == "__main__":
    pilot_onboarding()
