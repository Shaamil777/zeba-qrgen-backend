from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional, List
from ..database import get_db
from ..models import User, QRCode, ScanLog, ContactSubmission
from ..schemas import AnalyticsResponse, ScansByDate, ScansByLocation, ScansByDevice, ScanLogResponse, ContactSubmissionResponse
from ..auth import get_current_admin

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/", response_model=AnalyticsResponse)
def get_analytics(
    qr_id: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Base query
    scan_query = db.query(ScanLog)
    
    # Apply filters
    if qr_id:
        scan_query = scan_query.filter(ScanLog.qr_code_id == qr_id)
    if start_date:
        scan_query = scan_query.filter(ScanLog.timestamp >= start_date)
    if end_date:
        scan_query = scan_query.filter(ScanLog.timestamp <= end_date)
    if location:
        qr_ids = db.query(QRCode.id).filter(QRCode.location.ilike(f"%{location}%")).subquery()
        scan_query = scan_query.filter(ScanLog.qr_code_id.in_(qr_ids))
    
    total_scans = scan_query.count()
    total_qr_codes = db.query(QRCode).count()
    
    # Scans by date (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    scans_by_date_query = db.query(
        func.date(ScanLog.timestamp).label("date"),
        func.count(ScanLog.id).label("count")
    ).filter(ScanLog.timestamp >= thirty_days_ago)
    
    if qr_id:
        scans_by_date_query = scans_by_date_query.filter(ScanLog.qr_code_id == qr_id)
    
    scans_by_date = scans_by_date_query.group_by(func.date(ScanLog.timestamp)).order_by(func.date(ScanLog.timestamp)).all()
    
    # Scans by location
    scans_by_location = db.query(
        QRCode.location,
        func.count(ScanLog.id).label("count")
    ).join(ScanLog).group_by(QRCode.location).order_by(desc("count")).limit(10).all()
    
    # Scans by device
    scans_by_device = db.query(
        ScanLog.device_type,
        func.count(ScanLog.id).label("count")
    ).group_by(ScanLog.device_type).all()
    
    # Recent scans with QR info
    recent_scans_raw = scan_query.order_by(desc(ScanLog.timestamp)).limit(20).all()
    recent_scans = []
    for s in recent_scans_raw:
        qr = db.query(QRCode).filter(QRCode.id == s.qr_code_id).first()
        recent_scans.append(ScanLogResponse(
            id=s.id,
            qr_code_id=s.qr_code_id,
            qr_name=qr.name if qr else None,
            qr_location=qr.location if qr else None,
            timestamp=s.timestamp,
            device_type=s.device_type,
            browser=s.browser,
            os=s.os,
            city=s.city,
            country=s.country
        ))
    
    return AnalyticsResponse(
        total_scans=total_scans,
        total_qr_codes=total_qr_codes,
        scans_by_date=[ScansByDate(date=str(s.date), count=s.count) for s in scans_by_date],
        scans_by_location=[ScansByLocation(location=s.location or "Unknown", count=s.count) for s in scans_by_location],
        scans_by_device=[ScansByDevice(device_type=s.device_type or "Unknown", count=s.count) for s in scans_by_device],
        recent_scans=recent_scans
    )

@router.get("/qr/{qr_id}/scans")
def get_qr_scans(
    qr_id: int,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    scans = db.query(ScanLog).filter(ScanLog.qr_code_id == qr_id).order_by(desc(ScanLog.timestamp)).limit(limit).all()
    return [ScanLogResponse.model_validate(s) for s in scans]

@router.get("/locations")
def get_locations(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    locations = db.query(QRCode.location).distinct().all()
    return [loc[0] for loc in locations if loc[0]]


@router.get("/contacts", response_model=List[ContactSubmissionResponse])
def get_contacts(
    qr_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = db.query(ContactSubmission)
    if qr_id:
        query = query.filter(ContactSubmission.qr_code_id == qr_id)
    
    contacts_raw = query.order_by(desc(ContactSubmission.created_at)).limit(50).all()
    contacts = []
    for c in contacts_raw:
        qr = db.query(QRCode).filter(QRCode.id == c.qr_code_id).first()
        contacts.append(ContactSubmissionResponse(
            id=c.id,
            qr_code_id=c.qr_code_id,
            qr_name=qr.name if qr else None,
            qr_location=qr.location if qr else None,
            name=c.name,
            phone=c.phone,
            message=c.message,
            created_at=c.created_at
        ))
    return contacts
