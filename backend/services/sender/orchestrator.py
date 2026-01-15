from datetime import datetime
from backend.services.sender.providers.sendgrid_adapter import SendGridEmailProvider
from backend.storage.models import Lead, EmailInteraction
from backend.storage.db import LeadStore
from backend.services.sender.risk_control import RiskController
from backend.utils.logger import setup_logger

logger = setup_logger("SendOrchestrator")

class SendOrchestrator:
    def __init__(self, db_store: LeadStore):
        self.db = db_store
        self.risk_control = RiskController(db_store)
        self.provider = SendGridEmailProvider()

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
        if subject_override or body_override:
            self.db.update_lead(lead)

        # 1. State & Idempotency Validations
        if lead.status == "sent":
             logger.warning(f"Idempotency Block: Lead {lead_id} already sent. Refusing to resend.")
             return
             
        if lead.last_message_id and lead.status == "sent":
             logger.warning(f"Idempotency Block: Lead {lead_id} has message_id {lead.last_message_id}. Refusing.")
             return

        if "stopped" in lead.status:
             logger.warning(f"Lead {lead_id} is stopped ({lead.status}). Skipping.")
             return

        # 2. Risk Checks
        if not self.risk_control.can_send(lead_id):
            self.db.log_event(lead_id, "SEND_BLOCKED", "Risk Control Limit Reached")
            logger.error(f"Risk Control blocked sending for lead {lead_id}")
            raise Exception("Risk Control Blocked")

        logger.info(f"Sending email to {lead.email}...")
        
        try:
            db_event_type = "SEND_ATTEMPT"
            self.db.log_event(lead.id, db_event_type, "Initiating Provider Send")
            
            # 3. Call Provider
            provider_msg_id = self.provider.send_email(
                to_email=lead.email,
                subject=lead.generated_email_subject,
                content=lead.generated_email_body
            )
            
            # 4. Success State Update (Atomic-ish)
            # Determine step: if new -> step0. If step0 -> step1.
            # Simplified logic: just increment send_count and use that for step
            current_step = lead.send_count # 0 initially
            new_status = f"sent_step{current_step}"
            
            thread_id = lead.thread_id or f"th_{lead.id}_{int(datetime.now().timestamp())}"
            
            lead.status = new_status
            lead.last_sent_at = datetime.now()
            lead.send_count += 1
            lead.last_message_id = provider_msg_id
            lead.thread_id = thread_id
            
            # Reset schedule for next step (e.g. +3 days) - Placeholder logic
            # lead.next_scheduled_at = datetime.now() + timedelta(days=3)
            
            self.db.update_lead(lead) 
            self.db.log_event(lead_id, "SEND_OK", f"Provider ID: {provider_msg_id}, New Status: {new_status}")
            self.risk_control.record_send_success() 
            
            logger.info(f"Email sent successfully. ID: {provider_msg_id}")
            
            return EmailInteraction(
                lead_id=lead.id,
                sent_at=datetime.now(),
                message_id=provider_msg_id,
                thread_id=thread_id,
                subject=lead.generated_email_subject,
                body=lead.generated_email_body
            )
        except Exception as e:
            logger.error(f"Failed to send email to {lead.email}: {e}")
            self.db.log_event(lead_id, "SEND_ERR", str(e))
            raise e
