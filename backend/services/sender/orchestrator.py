from datetime import datetime
from backend.storage.models import Lead, EmailInteraction
from backend.storage.db import LeadStore
from backend.services.sender.risk_control import RiskController
from backend.utils.logger import setup_logger

logger = setup_logger("SendOrchestrator")

class SendOrchestrator:
    def __init__(self, db_store: LeadStore):
        self.db = db_store
        self.risk_control = RiskController(db_store)

    def approve_and_send(self, lead_id: str, subject_override: str = None, body_override: str = None):
        lead = self.db.get_lead(lead_id)
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return

        # Apply edits if provided
        if subject_override:
            lead.generated_email_subject = subject_override
        if body_override:
            lead.generated_email_body = body_override
        # If edits made, we should persist them now? 
        # Yes, standard practice: save the final approved version.
        if subject_override or body_override:
            self.db.update_lead(lead)

        # 1. State Validations
        if lead.status != "processed":
             logger.warning(f"Lead {lead_id} status '{lead.status}' is not 'processed'. Skipping.")
             return
             
        if "stopped" in lead.status:
             logger.warning(f"Lead {lead_id} is stopped. Skipping.")
             return

        # 2. Risk Checks
        if not self.risk_control.can_send(lead_id):
            self.db.log_event(lead_id, "SEND_BLOCKED", "Risk Control Limit Reached")
            logger.error(f"Risk Control blocked sending for lead {lead_id}")
            raise Exception("Risk Control Blocked")

        # 3. Idempotency Check
        if lead.status == "sent": 
            logger.warning("Idempotency Block: Lead already marked as sent.")
            return

        logger.info(f"Sending email to {lead.email}...")
        
        # Simulate SMTP / Gmail API Send
        message_id = f"msg_{lead.id}_{int(datetime.now().timestamp())}"
        thread_id = f"th_{lead.id}"
        
        # 4. Update Lead State (Atomic-ish)
        lead.status = "sent"
        lead.last_sent_at = datetime.now()
        lead.send_count += 1
        lead.last_message_id = message_id
        lead.thread_id = thread_id
        
        self.db.update_lead(lead) 
        self.db.log_event(lead_id, "SENT", f"MsgID: {message_id}")
        self.risk_control.record_send_success() 
        
        logger.info(f"Email sent successfully. Message ID: {message_id}")
        
        return EmailInteraction(
            lead_id=lead.id,
            sent_at=datetime.now(),
            message_id=message_id,
            thread_id=thread_id,
            subject=lead.generated_email_subject,
            body=lead.generated_email_body
        )
