from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from backend.storage.db import LeadStore
from backend.services.lead_ingest.ingest import LeadIngestionService
from backend.services.sender.orchestrator import SendOrchestrator
from backend.agents.icp_persona.agent import ICPPersonaAgent
from backend.agents.email_gen.generator import EmailGeneratorAgent
from backend.utils.logger import setup_logger

app = FastAPI(title="AI GTM Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logger("API")
db = LeadStore("gtm_agent.db")

# Path to frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")


# Schemas
class LeadCreate(BaseModel):
    name: str
    company: str
    email: Optional[str] = None
    linkedin: Optional[str] = None
    source: str = "API"

class LeadResponse(BaseModel):
    id: str
    name: str
    company: str
    status: str
    subject: Optional[str] = None
    body: Optional[str] = None

# Background Tasks
def process_lead_pipeline(lead_id: str):
    logger.info(f"Background processing for lead {lead_id}")
    lead = db.get_lead(lead_id)
    if not lead: return

    # 1. Enrichment
    icp = ICPPersonaAgent(db)
    lead = icp.analyze_lead(lead)
    
    # 2. Generation
    # Ensure downstream agent uses the potentially updated status/content
    gen = EmailGeneratorAgent(db)
    lead = gen.generate_email(lead)
    
    # Update full lead in DB
    db.update_lead(lead)
    logger.info(f"Pipeline complete for {lead_id}")

@app.get("/metrics")
def get_metrics():
    todays = db.get_todays_metrics()
    return {
        "date": todays.date,
        "sent": todays.sent_count,
        "replied": todays.reply_count,
        "positive": todays.positive_count,
        "bounced": todays.bounce_count
    }

@app.get("/leads", response_model=List[LeadResponse])
def get_leads():
    leads = db.get_all_leads()
    return [
        LeadResponse(
            id=l.id, name=l.name, company=l.company_name, 
            status=l.status, subject=l.generated_email_subject, body=l.generated_email_body
        ) 
        for l in leads
    ]

@app.get("/leads/ids")
def get_leads_ids():
    leads = db.get_all_leads()
    return [l.id for l in leads]

@app.post("/leads")
def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks):
    ingestor = LeadIngestionService(db)
    raw_data = lead.dict()
    lead_id = ingestor.ingest_lead(raw_data, source=lead.source)
    
    if lead_id:
        background_tasks.add_task(process_lead_pipeline, lead_id)
        return {"id": lead_id, "status": "ingested"}
    else:
        raise HTTPException(status_code=400, detail="Ingestion Failed")

@app.post("/leads/{lead_id}/approve")
def approve_lead(lead_id: str):
    sender = SendOrchestrator(db)
    # In a real app we might want to allow editing the body here before sending
    try:
        sender.approve_and_send(lead_id)
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static Files (Frontend)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/index.html")
async def serve_index_file():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))

@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))

@app.post("/leads/batch-approve")
def batch_approve(payload: Dict[str, Any]):
    lead_ids = payload.get("lead_ids", [])
    overrides = payload.get("overrides", {}) # Map of lead_id -> {subject, body}
    
    sender = SendOrchestrator(db)
    results = {"success": [], "failed": []}
    
    for lid in lead_ids:
        try:
            db.log_event(lid, "APPROVE_ATTEMPT", "Batch approval triggered")
            # Extract override if any
            ovr = overrides.get(lid, {})
            sender.approve_and_send(lid, subject_override=ovr.get("subject"), body_override=ovr.get("body"))
            results["success"].append(lid)
        except Exception as e:
            logger.error(f"Failed to approve {lid}: {e}")
            db.log_event(lid, "APPROVE_ERROR", str(e))
            results["failed"].append(lid)
            
    return results

@app.get("/leads/{lead_id}/logs")
def get_lead_logs(lead_id: str):
    logs = db.get_lead_logs(lead_id)
    return [{"event": l.event_type, "details": l.details, "time": l.timestamp} for l in logs]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
