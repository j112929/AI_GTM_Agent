from backend.storage.models import Reply

class NotifierService:
    def __init__(self):
        pass

    def notify_slack(self, message: str):
        print(f"[SLACK NOTIFICATION]: {message}")

    def handle_new_reply(self, reply: Reply):
        if reply.classification == "interested":
            self.notify_slack(f"🔥 HOT LEAD: New positive reply from Lead {reply.lead_id}!")
        else:
            self.notify_slack(f"New reply from Lead {reply.lead_id}: {reply.classification}")
