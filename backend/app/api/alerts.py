from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    spider_id: int = Query(None),
    alert_type: str = Query(None),
    severity: str = Query(None),
    acknowledged: bool = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if spider_id:
        q = q.filter(Alert.spider_id == spider_id)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    if severity:
        q = q.filter(Alert.severity == severity)
    if acknowledged is not None:
        q = q.filter(Alert.acknowledged == acknowledged)
    return q.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


@router.put("/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"ok": True}


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db)):
    results = (
        db.query(Alert.alert_type, Alert.severity, func.count(Alert.id))
        .filter(Alert.acknowledged == False)
        .group_by(Alert.alert_type, Alert.severity)
        .all()
    )
    summary = {}
    total = 0
    for alert_type, severity, count in results:
        summary.setdefault(alert_type, {})[severity] = count
        total += count
    return {"total_unacked": total, "by_type": summary}
