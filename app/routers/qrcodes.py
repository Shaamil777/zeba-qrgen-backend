from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import qrcode
import io
import os
import uuid
from ..database import get_db
from ..models import User, QRCode, ScanLog, ContactSubmission
from ..schemas import QRCodeCreate, QRCodeUpdate, QRCodeResponse
from ..auth import get_current_admin
from ..config import get_settings

router = APIRouter(prefix="/api/qrcodes", tags=["qrcodes"])
settings = get_settings()

UPLOAD_DIR = "uploads/logos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=QRCodeResponse)
def create_qrcode(qr_data: QRCodeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qr = QRCode(**qr_data.model_dump(), owner_id=current_user.id)
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr

@router.get("/", response_model=List[QRCodeResponse])
def list_qrcodes(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qrcodes = db.query(QRCode).all()
    result = []
    for qr in qrcodes:
        qr_dict = QRCodeResponse.model_validate(qr)
        qr_dict.scan_count = db.query(ScanLog).filter(ScanLog.qr_code_id == qr.id).count()
        result.append(qr_dict)
    return result

@router.get("/{qr_id}", response_model=QRCodeResponse)
def get_qrcode(qr_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    qr_response = QRCodeResponse.model_validate(qr)
    qr_response.scan_count = db.query(ScanLog).filter(ScanLog.qr_code_id == qr.id).count()
    return qr_response

@router.put("/{qr_id}", response_model=QRCodeResponse)
def update_qrcode(qr_id: int, qr_data: QRCodeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    for key, value in qr_data.model_dump(exclude_unset=True).items():
        setattr(qr, key, value)
    db.commit()
    db.refresh(qr)
    return qr

@router.delete("/{qr_id}")
def delete_qrcode(qr_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    # Delete related records first
    db.query(ContactSubmission).filter(ContactSubmission.qr_code_id == qr_id).delete()
    db.query(ScanLog).filter(ScanLog.qr_code_id == qr_id).delete()
    
    db.delete(qr)
    db.commit()
    return {"message": "QR code deleted"}

@router.post("/{qr_id}/logo")
async def upload_logo(qr_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    qr.logo_path = filepath
    db.commit()
    return {"logo_path": filepath}

@router.get("/{qr_id}/image")
def get_qr_image(qr_id: int, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    scan_url = f"{settings.frontend_url}/scan/{qr_id}"
    qr_img = qrcode.QRCode(version=1, box_size=10, border=4)
    qr_img.add_data(scan_url)
    qr_img.make(fit=True)
    img = qr_img.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
