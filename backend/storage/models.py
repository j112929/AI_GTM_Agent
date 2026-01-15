from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class Campaign:
    id: str
    name: str
    icp_description: str
    email_template: str # Jinja2 style or simple format string
    blacklist_domains: List[str] = field(default_factory=list)
    daily_limit: int = 50
    status: str = "active" # active, paused
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EventLog:
    id: int # Auto-inc
    lead_id: str
    event_type: str # INGEST, ENRICH, GEN_EMAIL, APPROVE, SEND, REPLY, STOP
    details: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Lead:
    id: str
    source: str
    name: str
    company_name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Campaign Link
    campaign_id: Optional[str] = "default"
    
    # State Machine
    status: str = "new"  
    
    # Sending Logic
    send_count: int = 0
    last_sent_at: Optional[datetime] = None
    next_scheduled_at: Optional[datetime] = None
    
    # Enrichment Data
    company_summary: Optional[str] = None
    product_summary: Optional[str] = None
    
    # Generated Content
    generated_email_subject: Optional[str] = None
    generated_email_body: Optional[str] = None
    
    # Metadata for Idempotency & Ops
    last_message_id: Optional[str] = None 
    thread_id: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class DailyMetric:
    date: str 
    sent_count: int = 0
    reply_count: int = 0
    positive_count: int = 0
    bounce_count: int = 0

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
    classification: str 
