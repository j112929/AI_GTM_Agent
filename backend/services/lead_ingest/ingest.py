import uuid
from typing import Dict, Any
from backend.storage.models import Lead
from backend.storage.db import LeadStore
from backend.utils.logger import setup_logger

logger = setup_logger("LeadIngestionService")

class LeadIngestionService:
    def __init__(self, db: LeadStore):
        self.db = db

    def ingest_lead(self, raw_data: Dict[str, Any], source: str):
        # 1. Validate
        if 'name' not in raw_data or 'company' not in raw_data:
            logger.error(f"Skipping invalid lead from {source}: {raw_data}")
            return None

        # 2. Dedup (Check if email exists)
        # Assuming db has a method check_exists_by_email (to be added) or we just risk it for MVP
        
        # 3. Clean / Normalize
        lead_id = str(uuid.uuid4())
        name = raw_data['name'].strip()
        company = raw_data['company'].strip()
        email = raw_data.get('email', '').strip() or None
        
        lead = Lead(
            id=lead_id,
            source=source,
            name=name,
            company_name=company,
            email=email,
            linkedin_url=raw_data.get('linkedin', ''),
            status="new"
        )
        
        # 4. Store
        try:
            self.db.add_lead(lead)
            self.db.log_event(lead_id, "INGEST", f"Source: {source}")
            logger.info(f"Ingested lead: {name} from {company} (ID: {lead_id})")
            return lead_id
        except Exception as e:
            logger.error(f"Failed to save lead: {e}")
            return None
