from typing import Optional
from sqlalchemy.orm import Session
import httpx
from app.models.alert import Alert
from app.core.config import settings


class AlertService:
    """Creates alerts in DB with optional webhook dispatch."""

    def __init__(self, db: Session):
        self.db = db
        self.webhook_url = settings.ALERT_WEBHOOK_URL or None

    def create_alert(
        self,
        spider_id: int,
        task_id: Optional[int],
        alert_type: str,
        severity: str,
        message: str,
        context: dict = None,
    ) -> Alert:
        alert = Alert(
            spider_id=spider_id,
            task_id=task_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            context=context,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        if self.webhook_url:
            self._send_webhook(alert)

        return alert

    def _send_webhook(self, alert: Alert) -> None:
        try:
            payload = {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "spider_id": alert.spider_id,
                "context": alert.context,
            }
            httpx.post(self.webhook_url, json=payload, timeout=5)
        except Exception:
            pass

    def acknowledge(self, alert_id: int) -> bool:
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.acknowledged = True
            self.db.commit()
            return True
        return False

    def get_unacked_count(self) -> int:
        return self.db.query(Alert).filter(Alert.acknowledged == False).count()
