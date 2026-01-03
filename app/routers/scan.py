from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from user_agents import parse
from ..database import get_db
from ..models import QRCode, ScanLog, ContactSubmission
from ..schemas import QRCodeResponse, ContactSubmissionCreate

router = APIRouter(prefix="/api/scan", tags=["scan"])

@router.get("/{qr_id}")
def scan_qrcode(qr_id: int, request: Request, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id, QRCode.is_active == True).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found or inactive")
    
    # Parse user agent
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)
    
    device_type = "mobile" if user_agent.is_mobile else "tablet" if user_agent.is_tablet else "desktop"
    
    # Get client IP
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0] if forwarded else request.client.host
    
    # Log the scan
    scan = ScanLog(
        qr_code_id=qr_id,
        ip_address=ip,
        user_agent=user_agent_str,
        device_type=device_type,
        browser=f"{user_agent.browser.family} {user_agent.browser.version_string}",
        os=f"{user_agent.os.family} {user_agent.os.version_string}"
    )
    db.add(scan)
    db.commit()
    
    # Return QR code details for the landing page
    return {
        "id": qr.id,
        "name": qr.name,
        "location": qr.location,
        "company_name": qr.company_name,
        "phone_number": qr.phone_number,
        "description": qr.description,
        "logo_path": qr.logo_path
    }

@router.get("/{qr_id}/logo")
def get_logo(qr_id: int, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr or not qr.logo_path:
        raise HTTPException(status_code=404, detail="Logo not found")
    return FileResponse(qr.logo_path)


@router.post("/{qr_id}/contact")
def submit_contact(qr_id: int, data: ContactSubmissionCreate, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    contact = ContactSubmission(
        qr_code_id=qr_id,
        scan_id=data.scan_id,
        name=data.name,
        phone=data.phone,
        message=data.message
    )
    db.add(contact)
    db.commit()
    return {"message": "Contact submitted successfully"}


@router.get("/{qr_id}/vcard")
def get_vcard(qr_id: int, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    # Build vCard content
    vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{qr.company_name or qr.name}
ORG:{qr.company_name or ''}
TEL;TYPE=WORK,VOICE:{qr.phone_number or ''}
NOTE:{qr.description or ''} - Location: {qr.location}
END:VCARD"""
    
    filename = f"{qr.company_name or qr.name}.vcf".replace(" ", "_")
    
    return Response(
        content=vcard,
        media_type="text/vcard",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
