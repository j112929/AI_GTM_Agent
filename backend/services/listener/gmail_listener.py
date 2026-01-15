import os
import datetime
import base64
from typing import List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from backend.storage.models import Reply
from backend.storage.db import LeadStore
from backend.agents.reply_cls.classifier import ReplyClassifierAgent
from backend.utils.logger import setup_logger

logger = setup_logger("GmailListener")

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailListener:
    def __init__(self, db: LeadStore):
        self.db = db
        self.service = self._authenticate()
        self.classifier = ReplyClassifierAgent(db)

    def _authenticate(self):
        creds = None
        # In a real deployment, manage token.json better (e.g. Secrets Manager or ENV)
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception:
                logger.warning("Invalid token.json")
        
        # If no valid credentials available, we cannot run real Gmail pull
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    logger.warning("Could not refresh token.")
                    return None
            else:
                # We can't do interactive login in headless easily without a local browser
                # For this demo, if no token, we return None and log warning
                logger.warning("No valid Gmail credentials (token.json). Listener in MOCK mode.")
                return None

        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logger.error(f"Gmail Build Error: {e}")
            return None

    def check_for_replies(self):
        if not self.service:
            # Simulate check
            logger.info("Gmail Service not active. Skipping check.")
            return

        logger.info("Polling Gmail for replies (last 24h)...")
        
        # Calculate date query
        # yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        # q = f"after:{yesterday}" 
        # Actually standard query: "newer_than:1d"
        
        try:
            # Get list of messages
            results = self.service.users().messages().list(userId='me', q='newer_than:1d').execute()
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No new messages found.")
                return

            for msg in messages:
                self._process_message(msg['id'], msg['threadId'])
                
        except Exception as e:
            logger.error(f"Gmail polling error: {e}")

    def _process_message(self, msg_id, thread_id):
        try:
            msg_detail = self.service.users().messages().get(userId='me', id=msg_id).execute()
            payload = msg_detail.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), "")
            in_reply_to = next((h['value'] for h in headers if h['name'] == 'In-Reply-To'), None)
            references = next((h['value'] for h in headers if h['name'] == 'References'), None)
            
            # Extract Body (Simplified)
            body = "Could not parse body"
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode()
                            break
            elif 'body' in payload:
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode()

            # MATCHING LOGIC
            # 1. Check if we have a Lead with this thread_id
            lead = self._find_lead_by_thread(thread_id)
            
            # 2. Or match by In-Reply-To (provider message id)
            if not lead and in_reply_to:
                 # In-Reply-To usually contains limits like <abc@xyz>. Our DB might have just raw ID.
                 # This requires loose matching or exact storage. 
                 pass 
            
            if lead:
                # Check status to avoid re-processing 
                if "replied" in lead.status or "stopped" in lead.status:
                     return

                logger.info(f"New reply from Lead {lead.id} ({from_header})")
                
                # Create Reply Object
                reply = Reply(
                    lead_id=lead.id,
                    received_at=datetime.datetime.now(),
                    content=body,
                    classification="unknown"
                )
                
                # Classify & Update
                self.classifier.classify_reply(reply)
                self.db.log_event(lead.id, "REPLY_RECEIVED", f"From: {from_header}")
                
        except Exception as e:
            logger.error(f"Error processing message {msg_id}: {e}")

    def _find_lead_by_thread(self, thread_id: str):
        # Inefficient to query all, but for MVP it works. 
        # Better: db.get_lead_by_thread_id(thread_id)
        # We need to add that query to DB logic or loop all (bad).
        # Let's add a specialized query to DB.
        
        # For now, let's assume we implement `get_lead_by_thread_id` in DB
        return self.db.get_lead_by_thread_id(thread_id)

    def simulate_incoming_reply(self, lead_id: str, content: str):
         # Keep this for demo script compatibility
        pass
