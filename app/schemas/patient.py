from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PatientBaseSchema(BaseModel):
    name: str
    dob: str
    gender: str
    mobile: str
    blood_group: str
    emergency: str
    insurance: str
    abha_id: Optional[str] = None
    consent_academic: bool = False
    consent_commercial: bool = False
    consent_future: bool = False
    photo: Optional[str] = ""
    address: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    referred_by: Optional[str] = None
    national_id_type: Optional[str] = None
    national_id_number: Optional[str] = None
    email: Optional[str] = None
    alt_mobile: Optional[str] = None
    billing_category: Optional[str] = None
    emergency_relationship: Optional[str] = None

class PatientCreate(PatientBaseSchema):
    id: str

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None
    blood_group: Optional[str] = None
    emergency: Optional[str] = None
    insurance: Optional[str] = None
    abha_id: Optional[str] = None
    consent_academic: Optional[bool] = None
    consent_commercial: Optional[bool] = None
    consent_future: Optional[bool] = None
    status: Optional[str] = None
    photo: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    referred_by: Optional[str] = None
    national_id_type: Optional[str] = None
    national_id_number: Optional[str] = None
    email: Optional[str] = None
    alt_mobile: Optional[str] = None
    billing_category: Optional[str] = None
    emergency_relationship: Optional[str] = None

class PatientResponse(PatientBaseSchema):
    id: str
    status: str
    reg_date: datetime

    class Config:
        from_attributes = True
