import time
from backend.storage.db import LeadStore
from backend.services.lead_ingest.ingest import LeadIngestionService
from backend.agents.icp_persona.agent import ICPPersonaAgent
from backend.agents.email_gen.generator import EmailGeneratorAgent
from backend.services.sender.orchestrator import SendOrchestrator
from backend.services.listener.gmail_listener import InboxListener
from backend.agents.reply_cls.classifier import ReplyClassifierAgent
from backend.services.notify.notifier import NotifierService

def main():
    print("=== Starting AI GTM Agent System ===")
    
    # 0. Setup Storage
    db = LeadStore("gtm_agent.db")
    
    # 1. Ingest Lead
    ingestor = LeadIngestionService(db)
    raw_lead = {
        "name": "Alice Digits",
        "company": "Tech Corp",
        "email": "alice@techcorp.example.com",
        "linkedin": "https://linkedin.com/in/alicedigits"
    }
    lead_id = ingestor.ingest_lead(raw_lead, source="LinkedIn")
    print(f"Lead Ingested ID: {lead_id}")
    
    # 2. Enrichment & ICP Analysis
    icp_agent = ICPPersonaAgent()
    lead = db.get_lead(lead_id)
    lead = icp_agent.process_lead(lead)
    db.update_lead_status(lead.id, lead.status) # Update DB
    
    # 3. Email Generation
    email_agent = EmailGeneratorAgent()
    lead = email_agent.generate_email(lead)
    db.update_lead_status(lead.id, lead.status)
    
    print("\n--- Review Queue ---")
    print(f"Subject: {lead.generated_email_subject}")
    print(f"Body: {lead.generated_email_body}")
    print("Status: Waiting for Approval")
    
    # 4. Human Approval (Simulated)
    # In real UI, user clicks "Approve"
    print("\n[User clicks Approve]")
    
    # 5. Sending
    sender = SendOrchestrator(db)
    sender.approve_and_send(lead.id)
    
    # 6. Listen for Reply (Simulated)
    listener = InboxListener(db)
    # Simulate a time gap
    # time.sleep(1) 
    print("\n--- Waiting for Reply ---")
    reply = listener.simulate_incoming_reply(lead.id, "Hi, thanks for reaching out. We are interested to hear more. Let's talk.")
    
    # 7. Classify Reply
    classifier = ReplyClassifierAgent(db)
    classified_reply = classifier.classify_reply(reply)
    
    # 8. Notify
    notifier = NotifierService()
    notifier.handle_new_reply(classified_reply)
    
    print("\n=== Workflow Complete ===")

if __name__ == "__main__":
    main()
