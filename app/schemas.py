from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# QR Code schemas
class QRCodeCreate(BaseModel):
    name: str
    location: str
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None

class QRCodeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class QRCodeResponse(BaseModel):
    id: int
    name: str
    location: str
    company_name: Optional[str]
    phone_number: Optional[str]
    description: Optional[str]
    logo_path: Optional[str]
    is_active: bool
    created_at: datetime
    scan_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

# Scan schemas
class ScanLogResponse(BaseModel):
    id: int
    qr_code_id: int
    qr_name: Optional[str] = None
    qr_location: Optional[str] = None
    timestamp: datetime
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    city: Optional[str]
    country: Optional[str]
    
    class Config:
        from_attributes = True

# Analytics schemas
class ScansByDate(BaseModel):
    date: str
    count: int

class ScansByLocation(BaseModel):
    location: str
    count: int

class ScansByDevice(BaseModel):
    device_type: str
    count: int

class AnalyticsResponse(BaseModel):
    total_scans: int
    total_qr_codes: int
    scans_by_date: List[ScansByDate]
    scans_by_location: List[ScansByLocation]
    scans_by_device: List[ScansByDevice]
    recent_scans: List[ScanLogResponse]


# Contact submission schemas
class ContactSubmissionCreate(BaseModel):
    qr_code_id: int
    scan_id: Optional[int] = None
    name: str
    phone: str
    message: Optional[str] = None

class ContactSubmissionResponse(BaseModel):
    id: int
    qr_code_id: int
    qr_name: Optional[str] = None
    qr_location: Optional[str] = None
    name: str
    phone: str
    message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
