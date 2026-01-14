from datetime import datetime
from backend.storage.models import Lead, EmailInteraction
from backend.utils.logger import setup_logger

logger = setup_logger("SendOrchestrator")

class SendOrchestrator:
    def __init__(self, db_store):
        self.db = db_store

    def approve_and_send(self, lead_id: str):
        lead = self.db.get_lead(lead_id)
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return

        if lead.status != "processed":
             logger.warning(f"Lead {lead_id} is not ready for sending (Status: {lead.status})")
             return

        logger.info(f"Sending email to {lead.email}...")
        
        # Simulate SMTP / Gmail API Send
        message_id = f"msg_{int(datetime.now().timestamp())}"
        thread_id = f"th_{int(datetime.now().timestamp())}"
        
        # Log Interaction
        interaction = EmailInteraction(
            lead_id=lead.id,
            sent_at=datetime.now(),
            message_id=message_id,
            thread_id=thread_id,
            subject=lead.generated_email_subject,
            body=lead.generated_email_body
        )
        
        # Update Lead Status
        lead.status = "sent"
        self.db.update_lead_status(lead.id, "sent")
        
        logger.info(f"Email sent successfully. Message ID: {message_id}")
        return interaction
