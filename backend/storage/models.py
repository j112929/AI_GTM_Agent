from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class Lead:
    id: str
    source: str  # Apollo, LinkedIn
    name: str
    company_name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: str = "new"  # new, enriched, processed, approved, sent, replied
    
    # Enrichment Data
    company_summary: Optional[str] = None
    product_summary: Optional[str] = None
    
    # Generated Content
    generated_email_subject: Optional[str] = None
    generated_email_body: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EmailInteraction:
    lead_id: str
    sent_at: datetime
    message_id: str
    thread_id: str
    subject: str
    body: str

@dataclass
class Reply:
    lead_id: str
    received_at: datetime
    content: str
    classification: str  # interested, not_interested, out_of_office, etc.
