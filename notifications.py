"""
Multi-Channel Notification Engine for AnnRakshak AI.
Dispatches event-driven notifications across SMS, WhatsApp, and Email channels.
Persists immutable records into SQLite notifications table with 'queued' / 'sent' status.
Pluggable architecture allowing seamless swap between mock adapters and real Twilio/SendGrid APIs.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from database import get_connection, get_ist_now, format_ist_str, _db_lock

class BaseDispatcher:
    def send(self, recipient_id: str, title: str, body: str) -> bool:
        raise NotImplementedError

class SMSDispatcher(BaseDispatcher):
    def send(self, recipient_id: str, title: str, body: str) -> bool:
        # Pilot/Mock integration: In production, connects to Twilio / Fast2SMS
        return True

class WhatsAppDispatcher(BaseDispatcher):
    def send(self, recipient_id: str, title: str, body: str) -> bool:
        # Pilot/Mock integration: In production, connects to WhatsApp Business API / Gupshup
        return True

class EmailDispatcher(BaseDispatcher):
    def send(self, recipient_id: str, title: str, body: str) -> bool:
        # Pilot/Mock integration: In production, connects to SMTP / AWS SES / SendGrid
        return True

class NotificationEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.dispatchers = {
            "sms": SMSDispatcher(),
            "whatsapp": WhatsAppDispatcher(),
            "email": EmailDispatcher()
        }

    def emit(
        self,
        event_type: str,
        recipient_id: str,
        recipient_type: str,
        title: str,
        body: str,
        channels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Emits multi-channel notifications and records them in the database.
        Channels default to SMS, WhatsApp, and Email.
        """
        if channels is None:
            channels = ["sms", "whatsapp", "email"]

        results = []
        now = get_ist_now()
        now_str = format_ist_str(now)

        with _db_lock:
            conn = get_connection(self.db_path)
            try:
                cursor = conn.cursor()
                for channel in channels:
                    if channel not in self.dispatchers:
                        continue
                    notif_id = f"NOTIF-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                    dispatcher = self.dispatchers[channel]
                    
                    # Dispatch to adapter
                    sent_ok = dispatcher.send(recipient_id, title, body)
                    status = "sent" if sent_ok else "failed"

                    cursor.execute("""
                        INSERT INTO notifications (
                            id, recipient_id, recipient_type, channel, event_type,
                            title, body, status, created_at, sent_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        notif_id, recipient_id, recipient_type, channel, event_type,
                        title, body, status, now_str, now_str if sent_ok else None
                    ))

                    results.append({
                        "id": notif_id,
                        "recipient_id": recipient_id,
                        "recipient_type": recipient_type,
                        "channel": channel,
                        "event_type": event_type,
                        "title": title,
                        "body": body,
                        "status": status,
                        "created_at": now_str,
                        "sent_at": now_str if sent_ok else None
                    })
                conn.commit()
            finally:
                conn.close()

        return results

    def list_notifications(
        self,
        recipient_id: Optional[str] = None,
        recipient_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch recorded notifications."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            if recipient_id:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE recipient_id = ?
                    ORDER BY created_at DESC LIMIT ?;
                """, (recipient_id, limit))
            elif recipient_type:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE recipient_type = ?
                    ORDER BY created_at DESC LIMIT ?;
                """, (recipient_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM notifications
                    ORDER BY created_at DESC LIMIT ?;
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

# Global default instance
notification_engine = NotificationEngine()

def emit_workflow_notification(
    event_type: str,
    donation_id: str,
    request_id: Optional[str] = None,
    donor_id: Optional[str] = None,
    ngo_id: Optional[str] = None,
    portions: int = 0,
    food_name: str = "food",
    donor_name: str = "Donor",
    ngo_name: str = "NGO"
) -> None:
    """Helper to dispatch formatted notifications upon workflow state transitions."""
    if event_type == "donation_created" and donor_id:
        notification_engine.emit(
            event_type="donation_created",
            recipient_id=donor_id,
            recipient_type="donor",
            title=f"🌾 Listing Published: {donation_id}",
            body=f"Your donation listing of {portions} portions of {food_name} is now live and visible to verified recovery NGOs in Prayagraj."
        )

    elif event_type == "request_submitted":
        if donor_id:
            notification_engine.emit(
                event_type="request_submitted",
                recipient_id=donor_id,
                recipient_type="donor",
                title=f"📦 New Pickup Claim: {request_id}",
                body=f"Verified NGO '{ngo_name}' requested {portions} portions for listing {donation_id}. Please review and confirm in your portal."
            )
        if ngo_id:
            notification_engine.emit(
                event_type="request_submitted",
                recipient_id=ngo_id,
                recipient_type="ngo",
                title=f"⏳ Claim Awaiting Confirmation: {request_id}",
                body=f"Your claim for {portions} portions of {food_name} has been sent to '{donor_name}'. You will be notified once confirmed."
            )

    elif event_type == "request_confirmed":
        if ngo_id:
            notification_engine.emit(
                event_type="request_confirmed",
                recipient_id=ngo_id,
                recipient_type="ngo",
                title=f"✅ Pickup Confirmed: {request_id}",
                body=f"Donor '{donor_name}' confirmed your pickup request for {portions} portions. Coordinate collection van immediately!"
            )
        if donor_id:
            notification_engine.emit(
                event_type="request_confirmed",
                recipient_id=donor_id,
                recipient_type="donor",
                title=f"✅ You Confirmed Pickup: {request_id}",
                body=f"You confirmed pickup with '{ngo_name}'. Ensure food is held at safe temperature until collection."
            )

    elif event_type == "request_collected":
        if donor_id:
            notification_engine.emit(
                event_type="request_collected",
                recipient_id=donor_id,
                recipient_type="donor",
                title=f"🚚 Food Collected: {request_id}",
                body=f"'{ngo_name}' has successfully collected {portions} portions of {food_name}. In transit for distribution."
            )

    elif event_type == "request_delivered":
        if donor_id:
            notification_engine.emit(
                event_type="request_delivered",
                recipient_id=donor_id,
                recipient_type="donor",
                title=f"🎉 Food Rescued & Delivered: {request_id}",
                body=f"'{ngo_name}' successfully distributed {portions} portions to vulnerable communities! Thank you for reducing waste."
            )
        if ngo_id:
            notification_engine.emit(
                event_type="request_delivered",
                recipient_id=ngo_id,
                recipient_type="ngo",
                title=f"🎉 Milestone Complete: {request_id}",
                body=f"Delivery confirmed for {portions} portions. ESG environmental impact logged in AnnRakshak AI."
            )

    elif event_type == "request_cancelled":
        if donor_id:
            notification_engine.emit(
                event_type="request_cancelled",
                recipient_id=donor_id,
                recipient_type="donor",
                title=f"⚠️ Request Cancelled: {request_id}",
                body=f"Pickup request {request_id} was cancelled. Unclaimed portions returned to available pool."
            )
        if ngo_id:
            notification_engine.emit(
                event_type="request_cancelled",
                recipient_id=ngo_id,
                recipient_type="ngo",
                title=f"⚠️ Request Cancelled: {request_id}",
                body=f"Pickup request {request_id} has been marked Cancelled."
            )

    elif event_type == "donation_expired" and donor_id:
        notification_engine.emit(
            event_type="donation_expired",
            recipient_id=donor_id,
            recipient_type="donor",
            title=f"⏰ Listing Expired: {donation_id}",
            body=f"Pickup deadline elapsed for {donation_id}. Food has been marked Expired to prevent food safety violations."
        )
