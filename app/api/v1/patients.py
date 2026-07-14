from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.database import get_db
from app.models.core import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.security.encryption import pii_service
from app.api.deps import get_current_user
from app.models.core import StaffAccount

router = APIRouter()

def encrypt_patient_model(patient_in) -> dict:
    return {
        "name": pii_service.encrypt(patient_in.name),
        "dob": pii_service.encrypt(patient_in.dob),
        "gender": patient_in.gender,
        "mobile": pii_service.encrypt(patient_in.mobile),
        "blood_group": patient_in.blood_group,
        "emergency": pii_service.encrypt(patient_in.emergency),
        "insurance": pii_service.encrypt(patient_in.insurance),
        "abha_id": pii_service.encrypt(patient_in.abha_id) if patient_in.abha_id else None,
        "consent_academic": patient_in.consent_academic,
        "consent_commercial": patient_in.consent_commercial,
        "consent_future": patient_in.consent_future,
        "photo": patient_in.photo,
        "address": pii_service.encrypt(patient_in.address) if patient_in.address else None,
        "occupation": pii_service.encrypt(patient_in.occupation) if patient_in.occupation else None,
        "marital_status": pii_service.encrypt(patient_in.marital_status) if patient_in.marital_status else None,
        "allergies": pii_service.encrypt(patient_in.allergies) if patient_in.allergies else None,
        "chronic_conditions": pii_service.encrypt(patient_in.chronic_conditions) if patient_in.chronic_conditions else None,
        "referred_by": pii_service.encrypt(patient_in.referred_by) if patient_in.referred_by else None,
        "national_id_type": pii_service.encrypt(patient_in.national_id_type) if patient_in.national_id_type else None,
        "national_id_number": pii_service.encrypt(patient_in.national_id_number) if patient_in.national_id_number else None,
        "email": pii_service.encrypt(patient_in.email) if patient_in.email else None,
        "alt_mobile": pii_service.encrypt(patient_in.alt_mobile) if patient_in.alt_mobile else None,
        "billing_category": pii_service.encrypt(patient_in.billing_category) if patient_in.billing_category else None,
        "emergency_relationship": pii_service.encrypt(patient_in.emergency_relationship) if patient_in.emergency_relationship else None
    }

def decrypt_patient_model(patient: Patient) -> dict:
    return {
        "id": patient.id,
        "name": pii_service.decrypt(patient.name),
        "dob": pii_service.decrypt(patient.dob),
        "gender": patient.gender,
        "mobile": pii_service.decrypt(patient.mobile),
        "blood_group": patient.blood_group,
        "emergency": pii_service.decrypt(patient.emergency),
        "insurance": pii_service.decrypt(patient.insurance),
        "abha_id": pii_service.decrypt(patient.abha_id) if patient.abha_id else None,
        "consent_academic": patient.consent_academic,
        "consent_commercial": patient.consent_commercial,
        "consent_future": patient.consent_future,
        "photo": patient.photo,
        "address": pii_service.decrypt(patient.address) if patient.address else None,
        "occupation": pii_service.decrypt(patient.occupation) if patient.occupation else None,
        "marital_status": pii_service.decrypt(patient.marital_status) if patient.marital_status else None,
        "allergies": pii_service.decrypt(patient.allergies) if patient.allergies else None,
        "chronic_conditions": pii_service.decrypt(patient.chronic_conditions) if patient.chronic_conditions else None,
        "referred_by": pii_service.decrypt(patient.referred_by) if patient.referred_by else None,
        "national_id_type": pii_service.decrypt(patient.national_id_type) if patient.national_id_type else None,
        "national_id_number": pii_service.decrypt(patient.national_id_number) if patient.national_id_number else None,
        "email": pii_service.decrypt(patient.email) if patient.email else None,
        "alt_mobile": pii_service.decrypt(patient.alt_mobile) if patient.alt_mobile else None,
        "billing_category": pii_service.decrypt(patient.billing_category) if patient.billing_category else None,
        "emergency_relationship": pii_service.decrypt(patient.emergency_relationship) if patient.emergency_relationship else None,
        "status": patient.status,
        "reg_date": patient.reg_date
    }

@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_in.id))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")

    encrypted_data = encrypt_patient_model(patient_in)
    db_patient = Patient(id=patient_in.id, **encrypted_data)
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    return decrypt_patient_model(db_patient)

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    result = await db.execute(select(Patient))
    patients = result.scalars().all()
    return [decrypt_patient_model(p) for p in patients]

@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    result = await db.execute(select(Patient))
    patients = result.scalars().all()
    
    query_lower = q.lower()
    matches = []
    
    for p in patients:
        decrypted = decrypt_patient_model(p)
        if (
            query_lower in decrypted["id"].lower() or
            query_lower in decrypted["name"].lower() or
            query_lower in decrypted["mobile"].lower() or
            (decrypted["abha_id"] and query_lower in decrypted["abha_id"].lower())
        ):
            matches.append(decrypted)
            
    return matches

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return decrypt_patient_model(patient)

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_in: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    update_data = patient_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in [
            "name", "dob", "mobile", "emergency", "insurance", "abha_id",
            "address", "occupation", "marital_status", "allergies",
            "chronic_conditions", "referred_by"
        ]:
            if value is not None:
                setattr(patient, field, pii_service.encrypt(value))
            else:
                setattr(patient, field, None)
        else:
            setattr(patient, field, value)
            
    await db.commit()
    await db.refresh(patient)
    return decrypt_patient_model(patient)

@router.post("/abha/verify")
async def verify_abha_otp(abha_id: str, otp: str):
    if otp == "123456":
        return {"status": "success", "message": "ABHA verification completed successfully", "abha_id": abha_id}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

import random

@router.post("/register_form")
async def register_patient_form(
    name: str = Form(...),
    dob: str = Form(...),
    gender: str = Form(...),
    mobile: str = Form(...),
    blood_group: str = Form(...),
    emergency: str = Form(...),
    insurance: str = Form(""),
    address: str = Form(""),
    occupation: str = Form(""),
    marital_status: str = Form(""),
    allergies: str = Form(""),
    chronic_conditions: str = Form(""),
    referred_by: str = Form(""),
    abha_id: Optional[str] = Form(None),
    consent_academic: bool = Form(False),
    consent_commercial: bool = Form(False),
    national_id_type: Optional[str] = Form(None),
    national_id_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    alt_mobile: Optional[str] = Form(None),
    billing_category: Optional[str] = Form(None),
    emergency_relationship: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    rand_id = f"AURA-2026-{random.randint(1000, 9999)}"
    
    patient_in = PatientCreate(
        id=rand_id,
        name=name,
        dob=dob,
        gender=gender,
        mobile=mobile,
        blood_group=blood_group,
        emergency=emergency,
        insurance=insurance,
        address=address,
        occupation=occupation,
        marital_status=marital_status,
        allergies=allergies,
        chronic_conditions=chronic_conditions,
        referred_by=referred_by,
        abha_id=abha_id,
        consent_academic=consent_academic,
        consent_commercial=consent_commercial,
        national_id_type=national_id_type,
        national_id_number=national_id_number,
        email=email,
        alt_mobile=alt_mobile,
        billing_category=billing_category,
        emergency_relationship=emergency_relationship
    )
    
    encrypted_data = encrypt_patient_model(patient_in)
    db_patient = Patient(id=rand_id, **encrypted_data)
    db.add(db_patient)
    await db.commit()
    
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Patient <strong>{name}</strong> registered successfully! UHID: <strong>{rand_id}</strong>
        </div>
    """)
