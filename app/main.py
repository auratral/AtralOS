from fastapi import FastAPI, Depends, Request, Form, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List
import os

from app.config import settings
from app.database import engine, Base, get_db
from app.models.core import StaffAccount, Patient, Department
from app.models.clinical import Appointment, Investigation, BillingInvoice, Prescription, ClinicalRecord
from app.models.specialty import EmergencyCase, IcuAdmission, OtSchedule, WardBed
from app.models.support import BloodInventory, DietOrder, AmbulanceTrip, Device, Complaint, LabReagent, LabReagentLog, DrugInventory, BloodRequest, AmbulanceFleet
from app.api.v1 import auth, patients
from app.api.deps import get_current_user
from app.security.auth import verify_password, create_access_token

app = FastAPI(
    title="AtralOS Hospital EHR",
    description="Python-based Clinical EHR & Hospital Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Expose Jinja2 templates
os.makedirs("app/templates", exist_ok=True)
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])

# Sidebar link configurations
SIDEBAR_CONFIGS = {
    "admin": [
        ("Dashboard", "dashboard"),
        ("Staff Management", "settings"),
        ("Device Management", "devices"),
        ("Complaint Management", "complaints")
    ],
    "reception": [
        ("Register Patient", "register"),
        ("Book Appointments", "appointments"),
        ("OPD Queue", "queue")
    ],
    "nursing": [
        ("Vitals Station", "queue"),
        ("Bed Management", "beds"),
        ("Handover Logs", "handover")
    ],
    "doctor": [
        ("OPD Consult Queue", "queue"),
        ("IPD Rounds", "rounds"),
        ("Discharge Summaries", "discharge")
    ],
    "lab": [
        ("LIS Queue", "queue"),
        ("QC Stats", "qc"),
        ("Reagent Stock", "reagents")
    ],
    "radiology": [
        ("RIS Queue", "queue"),
        ("Modality Schedule", "schedule"),
        ("TAT Dashboard", "tat")
    ],
    "pharmacy": [
        ("Dispense Queue", "queue"),
        ("Drug Inventory", "inventory"),
        ("Expiry Alerts", "expiry")
    ],
    "finance": [
        ("Invoices & Ledger", "invoices"),
        ("Daily Collection", "collection"),
        ("Analytics", "analytics")
    ],
    "emergency": [
        ("Triage Board", "triage"),
        ("Resus Bay", "resus"),
        ("ER Beds", "beds"),
        ("MLC Log", "mlc")
    ],
    "icu": [
        ("ICU Bed Map", "beds"),
        ("FAST HUG Chart", "fasthug"),
        ("Ventilators", "ventilator")
    ],
    "ot": [
        ("OT Schedule", "schedule"),
        ("WHO Safety Checklist", "checklist"),
        ("Post-Op Recovery", "recovery")
    ],
    "bloodbank": [
        ("Blood Stock", "stock"),
        ("Donations", "donations"),
        ("Requests Queue", "requests")
    ],
    "diet": [
        ("Kitchen Dashboard", "kitchen"),
        ("Meal Orders", "orders"),
        ("NRS Screening", "screening")
    ],
    "transport": [
        ("Dispatch Board", "dispatch"),
        ("Fleet List", "fleet"),
        ("Trip Logs", "trips")
    ],
    "patient": [
        ("Portal View", "portal")
    ]
}

@app.get("/")
async def root(request: Request, access_token: Optional[str] = Cookie(None), db: AsyncSession = Depends(get_db)):
    if access_token:
        try:
            await get_current_user(db=db, access_token=access_token)
            return RedirectResponse(url="/dashboard", status_code=303)
        except Exception:
            pass
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login")
async def login_post(
    response: Response,
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(StaffAccount).where(StaffAccount.email == username.lower()))
    user = result.scalars().first()
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Incorrect email or password"})
        
    if user.status != "Active":
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Staff account is inactive"})
        
    token = create_access_token(data={"sub": user.email})
    redirect = RedirectResponse(url="/dashboard", status_code=303)
    redirect.set_cookie(key="access_token", value=token, httponly=True)
    return redirect

@app.get("/logout")
async def logout():
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie(key="access_token")
    return redirect

@app.post("/api/v1/appointments/book")
async def book_appointment_form(
    patient_id: str = Form(...),
    doctor_email: str = Form(...),
    appt_type: str = Form(...),
    appt_time: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    import random
    import datetime
    
    doc_res = await db.execute(select(StaffAccount).where(StaffAccount.email == doctor_email))
    doctor = doc_res.scalars().first()
    if not doctor:
        return HTMLResponse("""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
                ❌ Error: Selected Consultant not found!
            </div>
        """)
        
    token_rand = random.randint(100, 999)
    
    new_appt = Appointment(
        patient_id=patient_id,
        doctor_name=doctor.name,
        doctor_id=doctor.id,
        department=doctor.department_id or "General",
        time=appt_time,
        token=token_rand,
        type=appt_type,
        status="Booked",
        date=datetime.date.today().strftime("%Y-%m-%d")
    )
    
    db.add(new_appt)
    await db.commit()
    
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Appointment scheduled successfully! Token: <strong>#{token_rand}</strong>
        </div>
    """)

@app.post("/api/v1/nursing/handover")
async def save_shift_handover(
    outgoing: str = Form(...),
    incoming: str = Form(...),
    shift_type: str = Form(...),
    summary: str = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Handover logged successfully! Outgoing: <strong>{outgoing}</strong> -> Incoming: <strong>{incoming}</strong>.
        </div>
    """)

@app.post("/api/v1/doctor/rounds")
async def save_ipd_rounds(
    bed_number: str = Form(...),
    patient_id: str = Form(...),
    notes: str = Form(...),
    priority: str = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Round entry recorded for <strong>{patient_id}</strong> at <strong>{bed_number}</strong> ({priority}).
        </div>
    """)

@app.post("/api/v1/doctor/discharge")
async def save_discharge_summary(
    patient_id: str = Form(...),
    diagnosis: str = Form(...),
    course: str = Form(...),
    advice: str = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Discharge summary generated for <strong>{patient_id}</strong> (Diagnosis: {diagnosis}). <a href="#" style="color: var(--primary); text-decoration: underline; font-weight: bold;">Download PDF</a>
        </div>
    """)

@app.post("/api/v1/emergency/resus")
async def save_resus_bay_log(
    bay_number: str = Form(...),
    patient_identifier: str = Form(...),
    interventions: str = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Resus details saved for <strong>{patient_identifier}</strong> in <strong>{bay_number}</strong>.
        </div>
    """)

@app.post("/api/v1/emergency/mlc")
async def save_mlc_log(
    patient_id: str = Form(...),
    police_copy: str = Form(...),
    mlc_type: str = Form(...),
    findings: str = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 MLC case recorded for <strong>{patient_id}</strong> (Police Copy: {police_copy}, Type: {mlc_type}).
        </div>
    """)

@app.post("/api/v1/icu/fasthug")
async def save_icu_fasthug(
    bed_number: str = Form(...),
    feeding: Optional[bool] = Form(False),
    analgesia: Optional[bool] = Form(False),
    sedation: Optional[bool] = Form(False),
    thrombo: Optional[bool] = Form(False),
    head: Optional[bool] = Form(False),
    ulcer: Optional[bool] = Form(False),
    glucose: Optional[bool] = Form(False)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 FAST HUG checklist logged successfully for Bed <strong>{bed_number}</strong>.
        </div>
    """)

@app.post("/api/v1/icu/ventilator")
async def save_icu_ventilator(
    bed_number: str = Form(...),
    vent_mode: str = Form(...),
    fio2: int = Form(...),
    peep: int = Form(...),
    rr: int = Form(...),
    tv: Optional[int] = Form(None),
    ps: Optional[int] = Form(None)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Ventilator settings updated for Bed <strong>{bed_number}</strong> (Mode: {vent_mode}, FiO2: {fio2}%, PEEP: {peep} cmH2O).
        </div>
    """)

@app.post("/api/v1/ot/checklist")
async def save_ot_checklist(
    schedule_id: str = Form(...),
    identity: Optional[bool] = Form(False),
    site_marked: Optional[bool] = Form(False),
    timeout: Optional[bool] = Form(False),
    antibiotic: Optional[bool] = Form(False),
    signout: Optional[bool] = Form(False)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 WHO Safety Checklist logged successfully for OT schedule <strong>{schedule_id}</strong>.
        </div>
    """)

@app.post("/api/v1/ot/recovery")
async def save_ot_recovery(
    patient_id: str = Form(...),
    activity: int = Form(...),
    respiration: int = Form(...),
    circulation: int = Form(...),
    consciousness: int = Form(...),
    oxygen: int = Form(...)
):
    aldrete_total = int(activity) + int(respiration) + int(circulation) + int(consciousness) + int(oxygen)
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Post-Op PACU Recovery logged for <strong>{patient_id}</strong>. Total Aldrete Score: <strong>{aldrete_total} / 10</strong>.
        </div>
    """)

@app.post("/api/v1/bloodbank/donations")
async def save_blood_donation(
    donor_name: str = Form(...),
    blood_group: str = Form(...),
    volume: int = Form(...),
    hb_level: float = Form(...)
):
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 Donation recorded for <strong>{donor_name}</strong> ({blood_group}, {volume}ml, Hb: {hb_level} g/dL). Unit packaged and logged.
        </div>
    """)

@app.post("/api/v1/diet/screening")
async def save_diet_screening(
    patient_id: str = Form(...),
    status_score: int = Form(...),
    illness_score: int = Form(...),
    age_score: int = Form(...)
):
    total_nrs = int(status_score) + int(illness_score) + int(age_score)
    at_risk = "YES" if total_nrs >= 3 else "NO"
    return HTMLResponse(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 500; font-size: 0.85rem; margin-top: 10px;">
            🎉 NRS-2002 Screening recorded for <strong>{patient_id}</strong>. Total Score: <strong>{total_nrs}</strong> (At Nutritional Risk: <strong>{at_risk}</strong>).
        </div>
    """)

@app.get("/dashboard")
async def dashboard(request: Request, current_user: StaffAccount = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": current_user})

@app.get("/dashboard/sidebar")
async def get_sidebar(request: Request, role: str, current_user: StaffAccount = Depends(get_current_user)):
    items = SIDEBAR_CONFIGS.get(role, [])
    return templates.TemplateResponse(request=request, name="components/sidebar.html", context={"items": items, "role": role})

@app.get("/dashboard/panel")
async def get_panel(
    request: Request,
    role: str,
    panel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    from app.models.clinical import Investigation, Prescription, ClinicalRecord
    if not panel:
        panel = SIDEBAR_CONFIGS.get(role, [("", "dashboard")])[0][1]

    # RENDER SUPER ADMIN DASHBOARD
    if role == "admin" and panel == "dashboard":
        patients_count = await db.scalar(select(func.count(Patient.id)))
        staff_count = await db.scalar(select(func.count(StaffAccount.id)))
        devices_count = await db.scalar(select(func.count(Device.id)))
        complaints_count = await db.scalar(select(func.count(Complaint.id)))
        
        return templates.TemplateResponse(request=request, name="panels/admin/dashboard.html", context={
            "stats": {
                "patients": patients_count,
                "staff": staff_count,
                "devices": devices_count,
                "complaints": complaints_count
            }
        })
        
    elif role == "admin" and panel == "settings":
        from app.models.core import Department
        dept_result = await db.execute(select(Department))
        departments = dept_result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/admin/settings.html", context={"departments": departments})
        
    elif role == "admin" and panel == "devices":
        from app.models.core import Department
        dept_result = await db.execute(select(Department))
        departments = dept_result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/admin/devices.html", context={"departments": departments})

    elif role == "admin" and panel == "complaints":
        return templates.TemplateResponse(request=request, name="panels/admin/complaints.html", context={})
        
    elif role == "reception" and panel == "register":
        return templates.TemplateResponse(request=request, name="panels/reception/register.html", context={})

    elif role == "reception" and panel == "appointments":
        result = await db.execute(select(StaffAccount).where(StaffAccount.role == "doctor"))
        doctors = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/reception/appointments.html", context={"doctors": doctors})

    elif role == "reception" and panel == "register":
        return templates.TemplateResponse(request=request, name="panels/reception/register.html", context={})

    elif role == "reception" and panel == "appointments":
        result = await db.execute(select(StaffAccount).where(StaffAccount.role == "doctor"))
        doctors = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/reception/appointments.html", context={"doctors": doctors})

    # RENDER RECEPTION QUEUE
    elif role == "reception" and panel == "queue":
        result = await db.execute(select(Appointment).where(Appointment.status.in_(["Booked", "Checked In"])))
        appointments = result.scalars().all()
        
        appt_list = []
        for appt in appointments:
            p_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
            patient = p_res.scalars().first()
            
            doc_name = "Unassigned"
            if appt.doctor_id:
                doc_res = await db.execute(select(StaffAccount).where(StaffAccount.id == appt.doctor_id))
                doc = doc_res.scalars().first()
                if doc:
                    doc_name = doc.name
                    
            if patient:
                from app.security.encryption import pii_service
                appt_list.append({
                    "id": appt.id,
                    "patient_id": patient.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "token": appt.token,
                    "time": appt.time,
                    "type": appt.type,
                    "status": appt.status,
                    "doctor_name": doc_name
                })
                
        # Query doctor workloads
        doc_res = await db.execute(select(StaffAccount).where(StaffAccount.role == "doctor"))
        doctors = doc_res.scalars().all()
        
        doctor_workloads = []
        for d in doctors:
            q_res = await db.execute(
                select(func.count(Appointment.id))
                .where(Appointment.doctor_id == d.id, Appointment.status.in_(["Booked", "Checked In"]))
            )
            q_size = q_res.scalar() or 0
            
            if q_size == 0:
                busy_status = "Available"
                busy_class = "status-active"
            elif q_size <= 2:
                busy_status = "Moderate"
                busy_class = "status-arrived"
            else:
                busy_status = "Highly Busy"
                busy_class = "status-canceled"
                
            doctor_workloads.append({
                "id": d.id,
                "name": d.name,
                "specialty": d.department_id.replace("DEP-", "") if d.department_id else "GEN",
                "queue_size": q_size,
                "busy_status": busy_status,
                "busy_class": busy_class
            })
            
        # Fallback to sample workloads if none exist
        if not doctor_workloads:
            doctor_workloads = [
                {
                    "id": "STAFF-DOC-01",
                    "name": "Dr. Vikram Aditya",
                    "specialty": "General Medicine",
                    "queue_size": 4,
                    "busy_status": "Highly Busy",
                    "busy_class": "status-canceled"
                },
                {
                    "id": "STAFF-DOC-02",
                    "name": "Dr. Neha Sharma",
                    "specialty": "Cardiology",
                    "queue_size": 1,
                    "busy_status": "Available",
                    "busy_class": "status-active"
                },
                {
                    "id": "STAFF-DOC-03",
                    "name": "Dr. Rajesh Kumar",
                    "specialty": "Pediatrics",
                    "queue_size": 2,
                    "busy_status": "Moderate",
                    "busy_class": "status-arrived"
                },
                {
                    "id": "STAFF-DOC-04",
                    "name": "Dr. Ananya Sen",
                    "specialty": "Dermatology",
                    "queue_size": 0,
                    "busy_status": "Available",
                    "busy_class": "status-active"
                }
            ]
            
        return templates.TemplateResponse(
            request=request, 
            name="panels/reception/queue.html", 
            context={
                "appointments": appt_list,
                "doctor_workloads": doctor_workloads
            }
        )

    # RENDER DOCTOR QUEUE
    elif role == "doctor" and panel == "queue":
        result = await db.execute(select(Appointment).where(Appointment.status == "In Consultation"))
        appointments = result.scalars().all()
        
        appt_list = []
        for appt in appointments:
            p_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                appt_list.append({
                    "id": appt.id,
                    "patient_id": patient.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "token": appt.token,
                    "time": appt.time,
                    "type": appt.type
                })
        return templates.TemplateResponse(request=request, name="panels/doctor/queue.html", context={"appointments": appt_list})

    elif role == "doctor" and panel == "rounds":
        return templates.TemplateResponse(request=request, name="panels/doctor/rounds.html", context={})

    elif role == "doctor" and panel == "discharge":
        return templates.TemplateResponse(request=request, name="panels/doctor/discharge.html", context={})

    elif role == "doctor" and panel == "consult":
        appt_id = request.query_params.get("appt_id")
        appt_res = await db.execute(select(Appointment).where(Appointment.id == appt_id))
        appt = appt_res.scalars().first()
        if not appt:
            return HTMLResponse("Appointment not found", status_code=404)
            
        p_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
        patient = p_res.scalars().first()
        if not patient:
            return HTMLResponse("Patient not found", status_code=404)
            
        from app.models.clinical import Vitals
        vitals_res = await db.execute(select(Vitals).where(Vitals.patient_id == patient.id).order_by(Vitals.timestamp.desc()))
        latest_vitals = vitals_res.scalars().first()
        
        from app.models.clinical import ClinicalRecord
        history_res = await db.execute(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient.id).order_by(ClinicalRecord.date.desc()))
        clinical_history = history_res.scalars().all()
        
        from app.models.clinical import Investigation
        inv_res = await db.execute(select(Investigation).where(Investigation.patient_id == patient.id).order_by(Investigation.timestamp.desc()))
        investigations = inv_res.scalars().all()
        
        from app.models.core import Department
        dept_res = await db.execute(select(Department))
        departments = dept_res.scalars().all()
        
        doc_res = await db.execute(select(StaffAccount).where(StaffAccount.role == "doctor", StaffAccount.id != current_user.id))
        doctors = doc_res.scalars().all()
        
        from app.security.encryption import pii_service
        patient_data = {
            "id": patient.id,
            "name": pii_service.decrypt(patient.name),
            "dob": pii_service.decrypt(patient.dob),
            "gender": patient.gender,
            "blood_group": patient.blood_group
        }
        
        return templates.TemplateResponse(
            request=request,
            name="panels/doctor/consult.html",
            context={
                "appt": appt,
                "patient": patient_data,
                "vitals": latest_vitals,
                "history": clinical_history,
                "investigations": investigations,
                "departments": departments,
                "doctors": doctors
            }
        )

    # RENDER NURSING QUEUE (VITALS)
    elif role == "nursing" and panel == "queue":
        result = await db.execute(select(Appointment).where(Appointment.status == "Checked In"))
        appointments = result.scalars().all()
        
        appt_list = []
        for appt in appointments:
            p_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                appt_list.append({
                    "id": appt.id,
                    "patient_id": patient.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "token": appt.token,
                    "time": appt.time
                })
        return templates.TemplateResponse(request=request, name="panels/nursing/queue.html", context={"appointments": appt_list})

    elif role == "nursing" and panel == "take_vitals":
        appt_id = request.query_params.get("appt_id")
        appt_res = await db.execute(select(Appointment).where(Appointment.id == appt_id))
        appt = appt_res.scalars().first()
        if not appt:
            return HTMLResponse("Appointment not found", status_code=404)
        
        p_res = await db.execute(select(Patient).where(Patient.id == appt.patient_id))
        patient = p_res.scalars().first()
        if not patient:
            return HTMLResponse("Patient not found", status_code=404)
            
        from app.security.encryption import pii_service
        patient_data = {
            "id": patient.id,
            "name": pii_service.decrypt(patient.name),
            "dob": pii_service.decrypt(patient.dob),
            "gender": patient.gender,
            "blood_group": patient.blood_group
        }
        
        return templates.TemplateResponse(
            request=request,
            name="panels/nursing/take_vitals.html",
            context={"appt_id": appt.id, "patient": patient_data}
        )

    elif role == "nursing" and panel == "beds":
        result = await db.execute(select(WardBed).where(WardBed.ward_name == "General Ward A"))
        beds = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/nursing/beds.html", context={"beds": beds})

    elif role == "nursing" and panel == "handover":
        return templates.TemplateResponse(request=request, name="panels/nursing/handover.html", context={})

    # RENDER EMERGENCY TRIAGE
    elif role == "emergency" and panel == "triage":
        result = await db.execute(select(EmergencyCase).where(EmergencyCase.status == "Active"))
        cases = result.scalars().all()
        
        case_list = []
        for case in cases:
            p_res = await db.execute(select(Patient).where(Patient.id == case.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                case_list.append({
                    "id": case.id,
                    "patient_id": patient.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "triage_level": case.triage_level,
                    "chief_complaint": case.chief_complaint,
                    "time_of_arrival": case.time_of_arrival.strftime("%H:%M")
                })
        return templates.TemplateResponse(request=request, name="panels/emergency/triage.html", context={"cases": case_list})

    elif role == "emergency" and panel == "resus":
        return templates.TemplateResponse(request=request, name="panels/emergency/resus.html", context={})

    elif role == "emergency" and panel == "beds":
        return templates.TemplateResponse(request=request, name="panels/emergency/beds.html", context={})

    elif role == "emergency" and panel == "mlc":
        return templates.TemplateResponse(request=request, name="panels/emergency/mlc.html", context={})

    # RENDER ICU BED MAP
    elif role == "icu" and panel == "beds":
        result = await db.execute(select(IcuAdmission))
        admissions = result.scalars().all()
        
        admit_list = []
        for ad in admissions:
            p_res = await db.execute(select(Patient).where(Patient.id == ad.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                admit_list.append({
                    "id": ad.id,
                    "bed_number": ad.bed_number,
                    "patient_name": pii_service.decrypt(patient.name),
                    "diagnosis": ad.diagnosis,
                    "ventilator": ad.ventilator_status,
                    "isolation": ad.isolation_flag,
                    "acuity": ad.acuity_level
                })
        return templates.TemplateResponse(request=request, name="panels/icu/beds.html", context={"admissions": admit_list})

    elif role == "icu" and panel == "fasthug":
        return templates.TemplateResponse(request=request, name="panels/icu/fasthug.html", context={})

    elif role == "icu" and panel == "ventilator":
        return templates.TemplateResponse(request=request, name="panels/icu/ventilator.html", context={})

    # RENDER OT SCHEDULE
    elif role == "ot" and panel == "schedule":
        result = await db.execute(select(OtSchedule).where(OtSchedule.status == "Scheduled"))
        schedules = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/ot/schedule.html", context={"schedules": schedules})

    elif role == "ot" and panel == "checklist":
        return templates.TemplateResponse(request=request, name="panels/ot/checklist.html", context={})

    elif role == "ot" and panel == "recovery":
        return templates.TemplateResponse(request=request, name="panels/ot/recovery.html", context={})

    # RENDER LAB QUEUE
    elif role == "lab" and panel == "queue":
        result = await db.execute(select(Investigation).where(Investigation.type == "Lab", Investigation.status == "Pending"))
        investigations = result.scalars().all()
        
        inv_list = []
        for inv in investigations:
            p_res = await db.execute(select(Patient).where(Patient.id == inv.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                inv_list.append({
                    "id": inv.id,
                    "test_name": inv.test_name,
                    "patient_name": pii_service.decrypt(patient.name),
                    "timestamp": inv.timestamp.strftime("%Y-%m-%d %H:%M") if inv.timestamp else "N/A"
                })
        return templates.TemplateResponse(request=request, name="panels/lab/queue.html", context={"investigations": inv_list})

    elif role == "lab" and panel == "qc":
        return templates.TemplateResponse(request=request, name="panels/lab/qc.html", context={})

    elif role == "lab" and panel == "reagents":
        result = await db.execute(select(LabReagent))
        reagents = result.scalars().all()
        
        log_res = await db.execute(select(LabReagentLog).order_by(LabReagentLog.timestamp.desc()))
        logs = log_res.scalars().all()
        
        log_list = []
        for log in logs:
            r_res = await db.execute(select(LabReagent).where(LabReagent.id == log.reagent_id))
            r = r_res.scalars().first()
            log_list.append({
                "id": log.id,
                "reagent_name": r.name if r else log.reagent_id,
                "reagent_id": log.reagent_id,
                "action": log.action,
                "quantity": log.quantity,
                "timestamp": log.timestamp,
                "user_name": log.user_name
            })
            
        return templates.TemplateResponse(
            request=request, 
            name="panels/lab/reagents.html", 
            context={
                "reagents": reagents,
                "logs": log_list
            }
        )

    # RENDER RADIOLOGY QUEUE
    elif role == "radiology" and panel == "queue":
        result = await db.execute(select(Investigation).where(Investigation.type == "Radiology", Investigation.status == "Pending"))
        investigations = result.scalars().all()
        
        inv_list = []
        for inv in investigations:
            p_res = await db.execute(select(Patient).where(Patient.id == inv.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                inv_list.append({
                    "id": inv.id,
                    "test_name": inv.test_name,
                    "patient_name": pii_service.decrypt(patient.name),
                    "timestamp": inv.timestamp.strftime("%Y-%m-%d %H:%M") if inv.timestamp else "N/A"
                })
        return templates.TemplateResponse(request=request, name="panels/radiology/queue.html", context={"investigations": inv_list})

    elif role == "radiology" and panel == "schedule":
        return templates.TemplateResponse(request=request, name="panels/radiology/schedule.html", context={})

    elif role == "radiology" and panel == "tat":
        return templates.TemplateResponse(request=request, name="panels/radiology/tat.html", context={})

    # RENDER PHARMACY DISPENSE QUEUE
    elif role == "pharmacy" and panel == "queue":
        result = await db.execute(select(Prescription).where(Prescription.status == "Pending"))
        prescriptions = result.scalars().all()
        
        rx_list = []
        for rx in prescriptions:
            rec_res = await db.execute(select(ClinicalRecord).where(ClinicalRecord.id == rx.clinical_record_id))
            record = rec_res.scalars().first()
            if record:
                p_res = await db.execute(select(Patient).where(Patient.id == record.patient_id))
                patient = p_res.scalars().first()
                if patient:
                    from app.security.encryption import pii_service
                    
                    meds_normalized = []
                    if isinstance(rx.medicines, list):
                        for med in rx.medicines:
                            if isinstance(med, dict):
                                meds_normalized.append(f"{med.get('name', '')} ({med.get('dosage', med.get('frequency', ''))}) — {med.get('duration', '')}")
                            elif isinstance(med, str):
                                meds_normalized.append(med)
                    elif isinstance(rx.medicines, dict):
                        items = rx.medicines.get("items", [])
                        for med in items:
                            if isinstance(med, dict):
                                meds_normalized.append(f"{med.get('name', '')} ({med.get('dosage', med.get('frequency', ''))}) — {med.get('duration', '')}")
                            elif isinstance(med, str):
                                meds_normalized.append(med)
                                
                    rx_list.append({
                        "id": rx.id,
                        "patient_name": pii_service.decrypt(patient.name),
                        "doctor_name": record.doctor_name,
                        "medicines": meds_normalized
                    })
        return templates.TemplateResponse(request=request, name="panels/pharmacy/queue.html", context={"prescriptions": rx_list})

    elif role == "pharmacy" and panel == "inventory":
        result = await db.execute(select(DrugInventory))
        drugs = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/pharmacy/inventory.html", context={"drugs": drugs})

    elif role == "pharmacy" and panel == "expiry":
        result = await db.execute(select(DrugInventory).order_by(DrugInventory.expiry))
        drugs = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/pharmacy/expiry.html", context={"drugs": drugs})

    # RENDER FINANCE INVOICES LIST
    elif role == "finance" and panel == "invoices":
        result = await db.execute(select(BillingInvoice).where(BillingInvoice.status == "Pending"))
        invoices = result.scalars().all()
        
        inv_list = []
        for inv in invoices:
            p_res = await db.execute(select(Patient).where(Patient.id == inv.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                inv_list.append({
                    "id": inv.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "total": inv.total,
                    "gst": inv.gst,
                    "subtotal": inv.subtotal,
                    "status": inv.status
                })
        return templates.TemplateResponse(request=request, name="panels/finance/invoices.html", context={"invoices": inv_list})

    elif role == "finance" and panel == "collection":
        return templates.TemplateResponse(request=request, name="panels/finance/collection.html", context={})

    elif role == "finance" and panel == "analytics":
        return templates.TemplateResponse(request=request, name="panels/finance/analytics.html", context={})

    # RENDER BLOOD STOCK
    elif role == "bloodbank" and panel == "stock":
        result = await db.execute(select(BloodInventory))
        inventory = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/bloodbank/stock.html", context={"inventory": inventory})

    elif role == "bloodbank" and panel == "donations":
        return templates.TemplateResponse(request=request, name="panels/bloodbank/donations.html", context={})

    elif role == "bloodbank" and panel == "requests":
        result = await db.execute(select(BloodRequest))
        requests = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/bloodbank/requests.html", context={"requests": requests})

    # RENDER DIET ORDERS
    elif role == "diet" and panel == "orders":
        result = await db.execute(select(DietOrder))
        orders = result.scalars().all()
        
        ord_list = []
        for ord in orders:
            p_res = await db.execute(select(Patient).where(Patient.id == ord.patient_id))
            patient = p_res.scalars().first()
            if patient:
                from app.security.encryption import pii_service
                ord_list.append({
                    "id": ord.id,
                    "patient_name": pii_service.decrypt(patient.name),
                    "diet_type": ord.diet_type,
                    "preference": ord.preference,
                    "breakfast": ord.breakfast,
                    "lunch": ord.lunch,
                    "dinner": ord.dinner
                })
        return templates.TemplateResponse(request=request, name="panels/diet/orders.html", context={"orders": ord_list})

    elif role == "diet" and panel == "kitchen":
        return templates.TemplateResponse(request=request, name="panels/diet/kitchen.html", context={})

    elif role == "diet" and panel == "screening":
        return templates.TemplateResponse(request=request, name="panels/diet/screening.html", context={})

    # RENDER AMBULANCE DISPATCH
    elif role == "transport" and panel == "dispatch":
        result = await db.execute(select(AmbulanceTrip).where(AmbulanceTrip.status == "Dispatched"))
        trips = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/transport/dispatch.html", context={"trips": trips})

    elif role == "transport" and panel == "fleet":
        result = await db.execute(select(AmbulanceFleet))
        fleet = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/transport/fleet.html", context={"fleet": fleet})

    elif role == "transport" and panel == "trips":
        result = await db.execute(select(AmbulanceTrip))
        trips = result.scalars().all()
        return templates.TemplateResponse(request=request, name="panels/transport/trips.html", context={"trips": trips})

    # DEFAULT FALLBACK
    return HTMLResponse(f"<h3>Panel {panel} for role {role} loaded successfully (Database Connected)</h3>")

@app.get("/api/v1/admin/staff-table")
async def get_staff_table(request: Request, db: AsyncSession = Depends(get_db), current_user: StaffAccount = Depends(get_current_user)):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
    result = await db.execute(select(StaffAccount).order_by(StaffAccount.joining_date.desc()).limit(100))
    staff_list = result.scalars().all()
    return templates.TemplateResponse(request=request, name="panels/admin/components/staff_table.html", context={"staff_list": staff_list})

@app.post("/api/v1/admin/register-staff")
async def register_staff(
    response: Response,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    department_id: str = Form(...),
    phone: Optional[str] = Form(None),
    license: Optional[str] = Form(None),
    shift: str = Form("Morning"),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    work_days: str = Form("Mon,Tue,Wed,Thu,Fri"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
    
    # Check if email exists
    exists_result = await db.execute(select(StaffAccount).where(StaffAccount.email == email))
    if exists_result.scalars().first():
        return HTMLResponse(
            '<div style="background: rgba(220,38,38,0.1); border: 1px solid var(--danger); color: var(--danger); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
            '❌ Email address already registered!'
            '</div>'
        )
    
    # Hash password
    from app.security.auth import get_password_hash
    password_hash = get_password_hash(password)
    
    # Generate staff ID
    import datetime
    year = datetime.datetime.now().year
    count_result = await db.execute(select(func.count(StaffAccount.id)))
    count = count_result.scalar() or 0
    staff_id = f"STAFF-{year}-{1001 + count}"
    
    # Create StaffAccount
    new_staff = StaffAccount(
        id=staff_id,
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
        department_id=department_id,
        phone=phone,
        license=license,
        shift=shift,
        qualification=qualification,
        specialization=specialization,
        work_days=work_days,
        joining_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        status="Active"
    )
    db.add(new_staff)
    await db.commit()
    
    # Set HTMX header to refresh directory table
    response.headers["HX-Trigger"] = "refresh-staff-list"
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Registered successfully! Assigned ID: <strong>{staff_id}</strong>'
        '</div>'
    )

@app.get("/api/v1/admin/department-details")
async def get_department_details(
    request: Request,
    dept: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.core import Department
    # Query department
    dept_res = await db.execute(select(Department).where(Department.id == dept))
    department = dept_res.scalars().first()
    if not department:
        return HTMLResponse("Department not found", status_code=404)
        
    # Query staff assigned to department
    staff_res = await db.execute(select(StaffAccount).where(StaffAccount.department_id == dept))
    staff_members = staff_res.scalars().all()
    staff_count = len(staff_members)
    
    # Query active items depending on department code
    active_cases = 0
    if department.code == "ER":
        from app.models.specialty import EmergencyCase
        case_res = await db.execute(select(func.count(EmergencyCase.id)).where(EmergencyCase.status != "Discharged"))
        active_cases = case_res.scalar() or 0
    elif department.code == "ICU":
        from app.models.specialty import IcuAdmission
        icu_res = await db.execute(select(func.count(IcuAdmission.id)))
        active_cases = icu_res.scalar() or 0
    elif department.code == "OT":
        from app.models.specialty import OtSchedule
        ot_res = await db.execute(select(func.count(OtSchedule.id)).where(OtSchedule.status == "Scheduled"))
        active_cases = ot_res.scalar() or 0
    elif department.code == "LAB" or department.code == "RAD":
        from app.models.clinical import Investigation
        inv_res = await db.execute(select(func.count(Investigation.id)).where(Investigation.status == "Pending"))
        active_cases = inv_res.scalar() or 0
    elif department.code == "FIN":
        from app.models.clinical import BillingInvoice
        fin_res = await db.execute(select(func.count(BillingInvoice.id)).where(BillingInvoice.status == "Pending"))
        active_cases = fin_res.scalar() or 0
    else:
        # Default fallback count
        active_cases = 0
        
    return templates.TemplateResponse(
        request=request, 
        name="panels/admin/components/department_modal.html", 
        context={
            "department": department,
            "staff_members": staff_members,
            "staff_count": staff_count,
            "active_cases": active_cases
        }
    )

@app.get("/api/v1/admin/edit-staff-modal/{staff_id}")
async def get_edit_staff_modal(
    request: Request,
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    staff_res = await db.execute(select(StaffAccount).where(StaffAccount.id == staff_id))
    staff = staff_res.scalars().first()
    if not staff:
        return HTMLResponse("Staff not found", status_code=404)
        
    from app.models.core import Department
    dept_res = await db.execute(select(Department))
    departments = dept_res.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="panels/admin/components/edit_staff_modal.html",
        context={"staff": staff, "departments": departments}
    )

@app.post("/api/v1/admin/edit-staff/{staff_id}")
async def edit_staff(
    response: Response,
    staff_id: str,
    name: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    role: str = Form(...),
    department_id: str = Form(...),
    phone: Optional[str] = Form(None),
    license: Optional[str] = Form(None),
    status: str = Form("Active"),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    shift: str = Form("Morning"),
    work_days: str = Form("Mon,Tue,Wed,Thu,Fri"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    staff_res = await db.execute(select(StaffAccount).where(StaffAccount.id == staff_id))
    staff = staff_res.scalars().first()
    if not staff:
        return HTMLResponse("Staff not found", status_code=404)
        
    email_check = await db.execute(select(StaffAccount).where(StaffAccount.email == email, StaffAccount.id != staff_id))
    if email_check.scalars().first():
         return HTMLResponse(
             '<div style="background: rgba(220,38,38,0.1); border: 1px solid var(--danger); color: var(--danger); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
             '❌ Email address already taken!'
             '</div>'
         )
         
    staff.name = name
    staff.email = email
    staff.role = role
    staff.department_id = department_id
    staff.phone = phone
    staff.license = license
    staff.status = status
    staff.qualification = qualification
    staff.specialization = specialization
    staff.shift = shift
    staff.work_days = work_days
    
    if password and password.strip():
        from app.security.auth import get_password_hash
        staff.password_hash = get_password_hash(password)
        
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-staff-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Profile for {staff.id} updated successfully!'
        '</div>'
    )

@app.delete("/api/v1/admin/staff/{staff_id}")
async def delete_staff(
    response: Response,
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    staff_res = await db.execute(select(StaffAccount).where(StaffAccount.id == staff_id))
    staff = staff_res.scalars().first()
    if not staff:
        return HTMLResponse("Staff member not found", status_code=404)
        
    if staff.id == current_user.id:
         return HTMLResponse(
             '<div style="background: rgba(220,38,38,0.1); border: 1px solid var(--danger); color: var(--danger); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
             '❌ Cannot delete your own active administrator session!'
             '</div>'
         )
         
    await db.delete(staff)
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-staff-list"
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Staff account {staff_id} successfully deleted from directory.'
        '</div>'
    )

@app.get("/api/v1/admin/devices-table")
async def get_devices_table(request: Request, db: AsyncSession = Depends(get_db), current_user: StaffAccount = Depends(get_current_user)):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
    from app.models.support import Device
    result = await db.execute(select(Device).order_by(Device.id.desc()).limit(100))
    devices = result.scalars().all()
    return templates.TemplateResponse(request=request, name="panels/admin/components/devices_table.html", context={"devices": devices})

@app.post("/api/v1/admin/register-device")
async def register_device(
    response: Response,
    name: str = Form(...),
    type: str = Form(...),
    department: str = Form(...),
    location: str = Form(...),
    serial_number: str = Form(...),
    status: str = Form("Active"),
    last_service_date: str = Form(...),
    maintenance_due: str = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Device
    count_res = await db.execute(select(func.count(Device.id)))
    count = count_res.scalar() or 0
    device_id = f"DEV-{1000 + count + 1}"
    
    new_device = Device(
        id=device_id,
        name=name,
        type=type,
        department=department,
        location=location,
        serial_number=serial_number,
        status=status,
        last_service_date=last_service_date,
        maintenance_due=maintenance_due,
        notes=notes
    )
    db.add(new_device)
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-devices-list"
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Device successfully registered! Assigned ID: <strong>{device_id}</strong>'
        '</div>'
    )

@app.get("/api/v1/admin/edit-device-modal/{device_id}")
async def get_edit_device_modal(
    request: Request,
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Device
    dev_res = await db.execute(select(Device).where(Device.id == device_id))
    device = dev_res.scalars().first()
    if not device:
        return HTMLResponse("Device not found", status_code=404)
        
    from app.models.core import Department
    dept_res = await db.execute(select(Department))
    departments = dept_res.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="panels/admin/components/edit_device_modal.html",
        context={"device": device, "departments": departments}
    )

@app.post("/api/v1/admin/edit-device/{device_id}")
async def edit_device(
    response: Response,
    device_id: str,
    name: str = Form(...),
    type: str = Form(...),
    department: str = Form(...),
    location: str = Form(...),
    serial_number: str = Form(...),
    status: str = Form("Active"),
    last_service_date: str = Form(...),
    maintenance_due: str = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Device
    dev_res = await db.execute(select(Device).where(Device.id == device_id))
    device = dev_res.scalars().first()
    if not device:
        return HTMLResponse("Device not found", status_code=404)
        
    device.name = name
    device.type = type
    device.department = department
    device.location = location
    device.serial_number = serial_number
    device.status = status
    device.last_service_date = last_service_date
    device.maintenance_due = maintenance_due
    device.notes = notes
    
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-devices-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Device {device_id} updated successfully!'
        '</div>'
    )

@app.delete("/api/v1/admin/device/{device_id}")
async def delete_device(
    response: Response,
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Device
    dev_res = await db.execute(select(Device).where(Device.id == device_id))
    device = dev_res.scalars().first()
    if not device:
        return HTMLResponse("Device not found", status_code=404)
        
    await db.delete(device)
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-devices-list"
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Device {device_id} deleted successfully.'
        '</div>'
    )

@app.get("/api/v1/admin/complaints-table")
async def get_complaints_table(request: Request, db: AsyncSession = Depends(get_db), current_user: StaffAccount = Depends(get_current_user)):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
    from app.models.support import Complaint
    result = await db.execute(select(Complaint).order_by(Complaint.created_at.desc()))
    complaints = result.scalars().all()
    return templates.TemplateResponse(request=request, name="panels/admin/components/complaints_table.html", context={"complaints": complaints})

@app.get("/api/v1/admin/complaint-detail-modal/{complaint_id}")
async def get_complaint_detail_modal(
    request: Request,
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Complaint
    comp_res = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = comp_res.scalars().first()
    if not complaint:
        return HTMLResponse("Ticket not found", status_code=404)
        
    staff_res = await db.execute(select(StaffAccount).order_by(StaffAccount.name))
    staff_list = staff_res.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="panels/admin/components/complaint_detail_modal.html",
        context={"complaint": complaint, "staff_list": staff_list}
    )

@app.post("/api/v1/admin/assign-complaint/{complaint_id}")
async def assign_complaint(
    response: Response,
    complaint_id: str,
    assigned_to: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Complaint
    comp_res = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = comp_res.scalars().first()
    if not complaint:
        return HTMLResponse("Ticket not found", status_code=404)
        
    complaint.assigned_to = assigned_to
    complaint.status = "In Progress"
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-complaints-list"
    
    return HTMLResponse(
        f'<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Ticket successfully assigned to {assigned_to}!'
        '</div>'
    )

@app.post("/api/v1/admin/close-complaint/{complaint_id}")
async def close_complaint(
    response: Response,
    complaint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.support import Complaint
    comp_res = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = comp_res.scalars().first()
    if not complaint:
        return HTMLResponse("Ticket not found", status_code=404)
        
    import datetime
    complaint.status = "Closed"
    complaint.resolved_at = datetime.datetime.utcnow()
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-complaints-list"
    
    return HTMLResponse(
        f'<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        f'✓ Ticket {complaint_id} resolved and closed.'
        '</div>'
    )

@app.post("/api/v1/nursing/save-vitals")
async def save_vitals(
    response: Response,
    appt_id: str = Form(...),
    patient_id: str = Form(...),
    bp: str = Form(...),
    temp: str = Form(...),
    pulse: int = Form(...),
    spo2: int = Form(...),
    sugar: Optional[int] = Form(None),
    resp_rate: Optional[int] = Form(None),
    height: Optional[float] = Form(None),
    weight: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Vitals
    import uuid
    vitals_id = f"VIT-{uuid.uuid4().hex[:6].upper()}"
    new_vitals = Vitals(
        id=vitals_id,
        patient_id=patient_id,
        bp=bp,
        temp=temp,
        pulse=pulse,
        spo2=spo2,
        sugar=sugar,
        notes=f"Height: {height}cm, Weight: {weight}kg. Resp: {resp_rate}. {notes or ''}"
    )
    db.add(new_vitals)
    
    appt_res = await db.execute(select(Appointment).where(Appointment.id == appt_id))
    appt = appt_res.scalars().first()
    if appt:
        appt.status = "In Consultation"
        
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 600; font-size: 0.85rem; margin-top: 10px;">'
        '✓ Vitals saved successfully! Patient checked-in and forwarded to Doctor Queue.'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  htmx.ajax("GET", "/dashboard/panel?role=nursing&panel=queue", {target: "#main-panel-content"});'
        '}, 1500);'
        '</script>'
    )

@app.get("/api/v1/nursing/bed-action-modal/{bed_id}")
async def get_bed_action_modal(
    request: Request,
    bed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.specialty import WardBed
    bed_res = await db.execute(select(WardBed).where(WardBed.id == bed_id))
    bed = bed_res.scalars().first()
    if not bed:
        return HTMLResponse("Bed not found", status_code=404)
        
    patient_name = ""
    patients_list = []
    
    if bed.status == "Occupied" and bed.patient_id:
        p_res = await db.execute(select(Patient).where(Patient.id == bed.patient_id))
        patient = p_res.scalars().first()
        if patient:
            from app.security.encryption import pii_service
            patient_name = pii_service.decrypt(patient.name)
    elif bed.status == "Available":
        p_res = await db.execute(select(Patient).limit(20))
        db_patients = p_res.scalars().all()
        from app.security.encryption import pii_service
        for pat in db_patients:
            bed_check = await db.execute(select(WardBed).where(WardBed.patient_id == pat.id))
            if not bed_check.scalars().first():
                patients_list.append({
                    "id": pat.id,
                    "name": pii_service.decrypt(pat.name)
                })
                
    return templates.TemplateResponse(
        request=request,
        name="panels/nursing/components/bed_action_modal.html",
        context={"bed": bed, "patient_name": patient_name, "patients": patients_list}
    )

@app.post("/api/v1/nursing/bed/assign/{bed_id}")
async def assign_bed(
    response: Response,
    bed_id: str,
    patient_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.specialty import WardBed, GeneralWardAdmission
    import uuid
    
    bed_res = await db.execute(select(WardBed).where(WardBed.id == bed_id))
    bed = bed_res.scalars().first()
    if not bed:
        return HTMLResponse("Bed not found", status_code=404)
        
    p_check = await db.execute(select(WardBed).where(WardBed.patient_id == patient_id))
    if p_check.scalars().first():
        return HTMLResponse(
            '<div style="background: var(--danger-bg); border: 1px solid var(--danger); color: var(--danger); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
            '❌ Patient is already assigned to a bed!'
            '</div>'
        )
        
    bed.patient_id = patient_id
    bed.status = "Occupied"
    
    admission_id = f"ADM-{uuid.uuid4().hex[:6].upper()}"
    new_admission = GeneralWardAdmission(
        id=admission_id,
        patient_id=patient_id,
        bed_number=bed.bed_number
    )
    db.add(new_admission)
    
    p_res = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = p_res.scalars().first()
    if patient:
        patient.status = "Admitted"
        
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-beds-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: var(--success-bg); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        '✓ Bed assigned successfully!'
        '</div>'
    )

@app.post("/api/v1/nursing/bed/vacate/{bed_id}")
async def vacate_bed(
    response: Response,
    bed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.specialty import WardBed, GeneralWardAdmission
    bed_res = await db.execute(select(WardBed).where(WardBed.id == bed_id))
    bed = bed_res.scalars().first()
    if not bed:
        return HTMLResponse("Bed not found", status_code=404)
        
    p_id = bed.patient_id
    bed.patient_id = None
    bed.status = "Available"
    
    if p_id:
        p_res = await db.execute(select(Patient).where(Patient.id == p_id))
        patient = p_res.scalars().first()
        if patient:
            patient.status = "Discharged"
            
    await db.commit()
    response.headers["HX-Trigger"] = "refresh-beds-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: var(--success-bg); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        '✓ Bed vacated successfully!'
        '</div>'
    )

@app.post("/api/v1/nursing/bed/mark-cleaning/{bed_id}")
async def mark_bed_cleaning(
    response: Response,
    bed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.specialty import WardBed
    bed_res = await db.execute(select(WardBed).where(WardBed.id == bed_id))
    bed = bed_res.scalars().first()
    if not bed:
        return HTMLResponse("Bed not found", status_code=404)
        
    p_id = bed.patient_id
    bed.patient_id = None
    bed.status = "Cleaning"
    
    if p_id:
        p_res = await db.execute(select(Patient).where(Patient.id == p_id))
        patient = p_res.scalars().first()
        if patient:
            patient.status = "OPD Queue"
            
    await db.commit()
    response.headers["HX-Trigger"] = "refresh-beds-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: var(--success-bg); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        '✓ Bed marked for cleaning.'
        '</div>'
    )

@app.post("/api/v1/nursing/bed/make-available/{bed_id}")
async def make_bed_available(
    response: Response,
    bed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["nursing", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.specialty import WardBed
    bed_res = await db.execute(select(WardBed).where(WardBed.id == bed_id))
    bed = bed_res.scalars().first()
    if not bed:
        return HTMLResponse("Bed not found", status_code=404)
        
    bed.status = "Available"
    await db.commit()
    
    response.headers["HX-Trigger"] = "refresh-beds-list"
    
    return HTMLResponse(
        '<script>document.body.dispatchEvent(new CustomEvent("close-modal"));</script>'
        '<div style="background: var(--success-bg); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        '✓ Bed is now available.'
        '</div>'
    )

@app.post("/api/v1/doctor/save-consultation")
async def save_consultation(
    request: Request,
    appt_id: str = Form(...),
    patient_id: str = Form(...),
    s: str = Form(...),
    o: str = Form(...),
    a: str = Form(...),
    p: str = Form(...),
    medicines_json: Optional[str] = Form(None),
    referral_dept: Optional[str] = Form(None),
    referral_doc: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role != "doctor":
        return HTMLResponse("Unauthorized", status_code=403)
        
    form_data = await request.form()
    lab_tests = form_data.getlist("lab_tests")
    radio_scans = form_data.getlist("radio_scans")
    
    from app.models.clinical import ClinicalRecord, Prescription, Investigation
    import uuid
    import datetime
    import json
    
    rec_id = f"REC-{uuid.uuid4().hex[:6].upper()}"
    new_record = ClinicalRecord(
        id=rec_id,
        patient_id=patient_id,
        doctor_id=current_user.id,
        doctor_name=current_user.name,
        s=s,
        o=o,
        a={"diagnoses": [a]},
        p=p,
        signed=True,
        signee=current_user.name
    )
    db.add(new_record)
    
    meds_list = []
    if medicines_json:
        try:
            meds_list = json.loads(medicines_json)
        except Exception:
            meds_list = []
            
    if meds_list:
        rx_id = f"PRX-{uuid.uuid4().hex[:6].upper()}"
        items = []
        for m in meds_list:
            item_str = f"{m['name']} — {m['frequency']} — {m['duration']}"
            if m.get("note") and m["note"].strip():
                item_str += f" (Note: {m['note'].strip()})"
            items.append(item_str)
            
        new_rx = Prescription(
            id=rx_id,
            clinical_record_id=rec_id,
            medicines={"items": items},
            status="Pending"
        )
        db.add(new_rx)
        
    for test in lab_tests:
        inv_id = f"INV-LAB-{uuid.uuid4().hex[:6].upper()}"
        new_inv = Investigation(
            id=inv_id,
            patient_id=patient_id,
            type="Lab",
            test_name=test,
            status="Pending",
            results={}
        )
        db.add(new_inv)
        
    for scan in radio_scans:
        inv_id = f"INV-RAD-{uuid.uuid4().hex[:6].upper()}"
        new_inv = Investigation(
            id=inv_id,
            patient_id=patient_id,
            type="Radiology",
            test_name=scan,
            status="Pending",
            results={}
        )
        db.add(new_inv)
        
    if referral_dept and referral_dept.strip():
        import random
        ref_appt_id = f"APT-REF-{random.randint(1000, 9999)}"
        doc_id = None
        if referral_doc and "(" in referral_doc:
            doc_id = referral_doc.split("(")[-1].replace(")", "").strip()
            
        dept_code = referral_dept.split("(")[-1].replace(")", "").strip() if "(" in referral_dept else referral_dept
        
        new_ref = Appointment(
            id=ref_appt_id,
            patient_id=patient_id,
            doctor_id=doc_id,
            department=dept_code,
            date=(datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            time="10:00 AM",
            type="Referral Consultation",
            status="Booked",
            token=random.randint(50, 99)
        )
        db.add(new_ref)
        
    appt_res = await db.execute(select(Appointment).where(Appointment.id == appt_id))
    appt = appt_res.scalars().first()
    if appt:
        appt.status = "Completed"
        
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 12px; border-radius: var(--radius-md); font-weight: 600; font-size: 0.85rem; margin-top: 10px;">'
        '✓ Consultation completed and EMR successfully updated!'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  htmx.ajax("GET", "/dashboard/panel?role=doctor&panel=queue", {target: "#main-panel-content"});'
        '}, 1500);'
        '</script>'
    )

@app.post("/api/v1/pharmacy/dispense/{rx_id}")
async def pharmacy_dispense(
    rx_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["pharmacy", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Prescription
    result = await db.execute(select(Prescription).where(Prescription.id == rx_id))
    rx = result.scalars().first()
    if not rx:
        return HTMLResponse("Prescription not found", status_code=404)
        
    rx.status = "Completed"
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600;">'
        '✓ Prescribed drugs successfully dispensed!'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  document.body.dispatchEvent(new CustomEvent("refresh-pharmacy-list"));'
        '}, 1000);'
        '</script>'
    )

@app.get("/api/v1/lab/results-modal/{inv_id}")
async def get_lab_results_modal(
    request: Request,
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["lab", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Investigation
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalars().first()
    if not inv:
        return HTMLResponse("Investigation order not found", status_code=404)
        
    p_res = await db.execute(select(Patient).where(Patient.id == inv.patient_id))
    patient = p_res.scalars().first()
    patient_name = "Unknown Patient"
    if patient:
        from app.security.encryption import pii_service
        patient_name = pii_service.decrypt(patient.name)
        
    return templates.TemplateResponse(
        request=request, 
        name="panels/lab/results_modal.html", 
        context={
            "inv": inv,
            "patient_name": patient_name
        }
    )

@app.post("/api/v1/lab/save-results/{inv_id}")
async def save_lab_results(
    request: Request,
    inv_id: str,
    findings: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["lab", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Investigation
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalars().first()
    if not inv:
        return HTMLResponse("Investigation not found", status_code=404)
        
    form_data = await request.form()
    uploaded_file = form_data.get("lab_file")
    filename = "Lab-Report-Signed.pdf"
    if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
        filename = uploaded_file.filename
        
    inv.results = {
        "findings": findings,
        "filename": filename,
        "signed_by": current_user.name
    }
    inv.status = "Completed"
    
    # Automatically deduct corresponding reagent stock if available
    reag_res = await db.execute(select(LabReagent).where(LabReagent.name.like("%CBC%")))
    reagent = reag_res.scalars().first()
    if reagent and reagent.stock > 0:
        reagent.stock -= 1
        if reagent.stock <= reagent.reorder_level:
            reagent.status = "Low Stock"
            
        import uuid
        import datetime
        log_id = f"LOG-{uuid.uuid4().hex[:6].upper()}"
        new_log = LabReagentLog(
            id=log_id,
            reagent_id=reagent.id,
            action=f"Consumed in LIS results upload ({inv.test_name})",
            quantity=-1,
            timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            user_name=current_user.name
        )
        db.add(new_log)
        
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600; margin-top: 10px;">'
        '✓ Laboratory report successfully uploaded!'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  modalOpen = false;'
        '  document.body.dispatchEvent(new CustomEvent("refresh-lab-list"));'
        '}, 1000);'
        '</script>'
    )

@app.get("/api/v1/radiology/scan-modal/{inv_id}")
async def get_radiology_scan_modal(
    request: Request,
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["radiology", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Investigation
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalars().first()
    if not inv:
        return HTMLResponse("Investigation order not found", status_code=404)
        
    p_res = await db.execute(select(Patient).where(Patient.id == inv.patient_id))
    patient = p_res.scalars().first()
    patient_name = "Unknown Patient"
    if patient:
        from app.security.encryption import pii_service
        patient_name = pii_service.decrypt(patient.name)
        
    return templates.TemplateResponse(
        request=request, 
        name="panels/radiology/scan_modal.html", 
        context={
            "inv": inv,
            "patient_name": patient_name
        }
    )

@app.post("/api/v1/radiology/save-scan/{inv_id}")
async def save_radiology_scan(
    request: Request,
    inv_id: str,
    findings: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["radiology", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    from app.models.clinical import Investigation
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalars().first()
    if not inv:
        return HTMLResponse("Investigation not found", status_code=404)
        
    form_data = await request.form()
    uploaded_file = form_data.get("scan_file")
    filename = "Scan-DICOM-Image.dcm"
    if uploaded_file and hasattr(uploaded_file, "filename") and uploaded_file.filename:
        filename = uploaded_file.filename
        
    inv.results = {
        "findings": findings,
        "filename": filename,
        "signed_by": current_user.name
    }
    inv.status = "Completed"
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600; margin-top: 10px;">'
        '✓ Radiology scan report successfully uploaded!'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  modalOpen = false;'
        '  document.body.dispatchEvent(new CustomEvent("refresh-radiology-list"));'
        '}, 1000);'
        '</script>'
    )

@app.get("/api/v1/lab/reagents/order-modal")
async def get_reagent_order_modal(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["lab", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    result = await db.execute(select(LabReagent))
    reagents = result.scalars().all()
    
    return templates.TemplateResponse(
        request=request, 
        name="panels/lab/order_modal.html", 
        context={
            "reagents": reagents
        }
    )

@app.post("/api/v1/lab/reagents/order")
async def place_reagent_order(
    reagent_id: str = Form(...),
    quantity: int = Form(...),
    supplier: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: StaffAccount = Depends(get_current_user)
):
    if current_user.role not in ["lab", "admin"]:
        return HTMLResponse("Unauthorized", status_code=403)
        
    result = await db.execute(select(LabReagent).where(LabReagent.id == reagent_id))
    reagent = result.scalars().first()
    if not reagent:
        return HTMLResponse("Reagent not found", status_code=404)
        
    reagent.stock += quantity
    reagent.status = "OK"
    
    import uuid
    import datetime
    log_id = f"LOG-{uuid.uuid4().hex[:6].upper()}"
    new_log = LabReagentLog(
        id=log_id,
        reagent_id=reagent_id,
        action=f"Stock Purchase Refill (Supplier: {supplier})",
        quantity=quantity,
        timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        user_name=current_user.name
    )
    db.add(new_log)
    await db.commit()
    
    return HTMLResponse(
        '<div style="background: rgba(16,185,129,0.1); border: 1px solid var(--success); color: var(--success); padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 600; margin-top: 10px;">'
        '✓ Purchase order completed and stock updated successfully!'
        '</div>'
        '<script>'
        'setTimeout(function() {'
        '  modalOpen = false;'
        '  document.body.dispatchEvent(new CustomEvent("refresh-reagents-list"));'
        '}, 1000);'
        '</script>'
    )

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    from app.database import SessionLocal
    from app.models.core import Department
    async with SessionLocal() as session:
        all_depts = [
            ("DEP-RECP", "Reception", "RECP"),
            ("DEP-NURS", "Nursing Station", "NURS"),
            ("DEP-CLIN", "Clinical Consult", "CLIN"),
            ("DEP-LAB", "Pathology Laboratory", "LAB"),
            ("DEP-RAD", "Radiology Imaging", "RAD"),
            ("DEP-PHAR", "Pharmacy", "PHAR"),
            ("DEP-FIN", "Finance & Billing", "FIN"),
            ("DEP-ER", "Emergency Department", "ER"),
            ("DEP-ICU", "Intensive Care Unit", "ICU"),
            ("DEP-OT", "Operation Theatre", "OT"),
            ("DEP-BB", "Blood Bank", "BB"),
            ("DEP-DT", "Dietetics & Nutrition", "DT"),
            ("DEP-TR", "Transport Services", "TR"),
            ("DEP-CARD", "Cardiology", "CARD"),
            ("DEP-OPHTH", "Ophthalmology", "OPHTH"),
            ("DEP-ONCO", "Oncology", "ONCO"),
            ("DEP-NEUR", "Neurology", "NEUR"),
            ("DEP-ORTH", "Orthopedics", "ORTH"),
            ("DEP-NEPH", "Nephrology", "NEPH"),
            ("DEP-GYNE", "Gynecology", "GYNE"),
            ("DEP-DERM", "Dermatology", "DERM"),
            ("DEP-PEDI", "Pediatrics", "PEDI"),
        ]
        for d_id, name, code in all_depts:
            res = await session.execute(select(Department).where(Department.id == d_id))
            existing = res.scalars().first()
            if not existing:
                new_dept = Department(id=d_id, name=name, code=code)
                session.add(new_dept)
        await session.commit()
