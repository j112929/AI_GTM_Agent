import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
from backend.storage.models import Lead, DailyMetric, Campaign, EventLog
from backend.utils.logger import setup_logger

logger = setup_logger("LeadStore")

class LeadStore:
    def __init__(self, db_path="gtm_agent.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Leads Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                source TEXT,
                name TEXT,
                company_name TEXT,
                email TEXT,
                linkedin_url TEXT,
                status TEXT,
                company_summary TEXT,
                product_summary TEXT,
                generated_email_subject TEXT,
                generated_email_body TEXT,
                send_count INTEGER DEFAULT 0,
                last_sent_at TEXT,
                next_scheduled_at TEXT,
                last_message_id TEXT,
                thread_id TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT,
                campaign_id TEXT DEFAULT 'default'
            )
        ''')
        
        # Metrics Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date TEXT PRIMARY KEY,
                sent_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                bounce_count INTEGER DEFAULT 0
            )
        ''')

        # Campaigns Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                icp_description TEXT,
                email_template TEXT,
                blacklist_domains TEXT,
                daily_limit INTEGER,
                status TEXT,
                created_at TEXT
            )
        ''')

        # Event Log Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                event_type TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        self.conn.commit()

    # --- Lead Methods ---

    def add_lead(self, lead: Lead):
        self.save_lead(lead)

    def update_lead(self, lead: Lead):
        self.save_lead(lead)

    def save_lead(self, lead: Lead):
        cursor = self.conn.cursor()
        # Ensure we handle the new campaign_id column if it didn't exist in old DBs (migration hack)
        # For this demo, assuming we just re-create DB or it's fine.
        # Actually sqlite doesn't throw if col missing in INSERT unless specified.
        # But safest is to DROP table or use ALTER in production.
        # Here we rely on "CREATE IF NOT EXISTS".
        
        # Check if column exists, if not add it (Simple Migration)
        try:
            cursor.execute('SELECT campaign_id FROM leads LIMIT 1')
        except sqlite3.OperationalError:
            cursor.execute('ALTER TABLE leads ADD COLUMN campaign_id TEXT DEFAULT "default"')
            self.conn.commit()
            
        cursor.execute('''
            INSERT OR REPLACE INTO leads (
                id, source, name, company_name, email, linkedin_url, status,
                company_summary, product_summary, generated_email_subject,
                generated_email_body, send_count, last_sent_at, next_scheduled_at,
                last_message_id, thread_id, metadata, created_at, updated_at, campaign_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead.id, lead.source, lead.name, lead.company_name, lead.email,
            lead.linkedin_url, lead.status, lead.company_summary,
            lead.product_summary, lead.generated_email_subject,
            lead.generated_email_body, lead.send_count,
            lead.last_sent_at.isoformat() if lead.last_sent_at else None,
            lead.next_scheduled_at.isoformat() if lead.next_scheduled_at else None,
            lead.last_message_id, lead.thread_id,
            json.dumps(lead.metadata),
            lead.created_at.isoformat(), datetime.now().isoformat(),
            lead.campaign_id
        ))
        self.conn.commit()

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        cursor = self.conn.cursor()
        try:
            # Need to handle potential missing column if migrating on the fly without restart
            cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        except Exception:
             return None 
             
        row = cursor.fetchone()
        if row:
            return self._row_to_lead(row)
        return None

    def get_all_leads(self) -> List[Lead]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM leads')
        rows = cursor.fetchall()
        return [self._row_to_lead(row) for row in rows]

    def update_lead_status(self, lead_id: str, status: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE leads SET status = ?, updated_at = ? WHERE id = ?', 
                       (status, datetime.now().isoformat(), lead_id))
        self.conn.commit()

    # --- Campaign Methods ---
    def save_campaign(self, campaign: Campaign):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO campaigns (
                id, name, icp_description, email_template, blacklist_domains,
                daily_limit, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign.id, campaign.name, campaign.icp_description, campaign.email_template,
            json.dumps(campaign.blacklist_domains), campaign.daily_limit,
            campaign.status, campaign.created_at.isoformat()
        ))
        self.conn.commit()

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        row = cursor.fetchone()
        if row:
            return Campaign(
                id=row[0], name=row[1], icp_description=row[2], email_template=row[3],
                blacklist_domains=json.loads(row[4]), daily_limit=row[5],
                status=row[6], created_at=datetime.fromisoformat(row[7])
            )
        return None

    # --- Event Log Methods ---
    def log_event(self, lead_id: str, event_type: str, details: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO event_logs (lead_id, event_type, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (lead_id, event_type, details, datetime.now().isoformat()))
        logger.info(f"[EVENT] {event_type} for {lead_id}: {details}")
        self.conn.commit()

    def get_lead_logs(self, lead_id: str) -> List[EventLog]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM event_logs WHERE lead_id = ? ORDER BY timestamp DESC', (lead_id,))
        rows = cursor.fetchall()
        return [EventLog(id=row[0], lead_id=row[1], event_type=row[2], details=row[3], timestamp=datetime.fromisoformat(row[4])) for row in rows]
    
    # --- Metrics Methods ---
    def get_todays_metrics(self) -> DailyMetric:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM daily_metrics WHERE date = ?', (today,))
        row = cursor.fetchone()
        if row:
            return DailyMetric(date=row[0], sent_count=row[1], reply_count=row[2], positive_count=row[3], bounce_count=row[4])
        else:
            return DailyMetric(date=today)

    def increment_metric(self, field: str):
        today = datetime.now().strftime("%Y-%m-%d")
        valid_fields = ["sent_count", "reply_count", "positive_count", "bounce_count"]
        if field not in valid_fields:
            return
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO daily_metrics (date) VALUES (?)', (today,))
        cursor.execute(f'UPDATE daily_metrics SET {field} = {field} + 1 WHERE date = ?', (today,))
        self.conn.commit()

    def _row_to_lead(self, row):
        # Handle dynamic column length if strictly needed, but for now assuming fixed schema or recreating DB
        # If campaign_id was added last (index 19)
        # 0..18 match previous
        campaign_id = "default"
        if len(row) > 19:
            campaign_id = row[19]
            
        return Lead(
            id=row[0], source=row[1], name=row[2], company_name=row[3],
            email=row[4], linkedin_url=row[5], status=row[6],
            company_summary=row[7], product_summary=row[8],
            generated_email_subject=row[9], generated_email_body=row[10],
            send_count=row[11],
            last_sent_at=datetime.fromisoformat(row[12]) if row[12] else None,
            next_scheduled_at=datetime.fromisoformat(row[13]) if row[13] else None,
            last_message_id=row[14],
            thread_id=row[15],
            metadata=json.loads(row[16]) if row[16] else {},
            created_at=datetime.fromisoformat(row[17]),
            updated_at=datetime.fromisoformat(row[18]),
            campaign_id=campaign_id
        )
