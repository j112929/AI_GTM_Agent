from typing import List, Optional
from backend.storage.models import Lead

if __name__ == "__main__":
    from backend.storage.db import LeadStore
    LeadStore("gtm_test.db") 

# Re-outputting the file content to ensure consistency is not always needed but safer here given prior context.
# Actually, I will just ensure the update_lead_status is correct and add get_pending_leads for the API.
import sqlite3
import json
from datetime import datetime
from backend.storage.models import Lead
from backend.utils.logger import setup_logger

logger = setup_logger("LeadStore")

class LeadStore:
    def __init__(self, db_path="gtm_agent.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
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
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        self.conn.commit()

    def add_lead(self, lead: Lead):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO leads (
                id, source, name, company_name, email, linkedin_url, status,
                company_summary, product_summary, generated_email_subject,
                generated_email_body, metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead.id, lead.source, lead.name, lead.company_name, lead.email,
            lead.linkedin_url, lead.status, lead.company_summary,
            lead.product_summary, lead.generated_email_subject,
            lead.generated_email_body, json.dumps(lead.metadata),
            lead.created_at.isoformat(), lead.updated_at.isoformat()
        ))
        self.conn.commit()

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_lead(row)
        return None

    def get_leads_by_status(self, status: str) -> List[Lead]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM leads WHERE status = ?', (status,))
        rows = cursor.fetchall()
        return [self._row_to_lead(row) for row in rows]
        
    def get_all_leads(self) -> List[Lead]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM leads')
        rows = cursor.fetchall()
        return [self._row_to_lead(row) for row in rows]

    def update_lead(self, lead: Lead):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE leads SET 
                source=?, name=?, company_name=?, email=?, linkedin_url=?, status=?,
                company_summary=?, product_summary=?, generated_email_subject=?,
                generated_email_body=?, metadata=?, updated_at=?
            WHERE id=?
        ''', (
            lead.source, lead.name, lead.company_name, lead.email,
            lead.linkedin_url, lead.status, lead.company_summary,
            lead.product_summary, lead.generated_email_subject,
            lead.generated_email_body, json.dumps(lead.metadata),
            datetime.now().isoformat(), lead.id
        ))
        self.conn.commit()

    def update_lead_status(self, lead_id: str, status: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
        self.conn.commit()
        
    def _row_to_lead(self, row):
        return Lead(
            id=row[0], source=row[1], name=row[2], company_name=row[3],
            email=row[4], linkedin_url=row[5], status=row[6],
            company_summary=row[7], product_summary=row[8],
            generated_email_subject=row[9], generated_email_body=row[10]
        )
