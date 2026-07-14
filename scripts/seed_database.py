import asyncio
import os
import sys
import base64
from datetime import datetime, timedelta

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.config import settings
from app.database import Base
from app.security.auth import get_password_hash
from app.security.encryption import pii_service
from app.models.core import Department, StaffAccount, ClinicalTeam, Patient, team_members
from app.models.clinical import Appointment, Vitals, ClinicalRecord, Prescription, Investigation, BillingInvoice, AuditLog
from app.models.specialty import EmergencyCase, IcuAdmission, IcuCharting, Surgery, OtSchedule, WardBed, GeneralWardAdmission
from app.models.support import BloodInventory, Donor, BloodRequest, DietOrder, DrugInventory, NarcoticsRegister, LabReagent, AmbulanceFleet, AmbulanceTrip, Device, Complaint, Notification

# Initialize database connection
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def seed_database():
    print("Dropping and recreating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("Starting Database Seeding...")

        # 1. Seed Departments
        dept_data = [
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
        ]
        
        departments = []
        for d_id, name, code in dept_data:
            dept = Department(id=d_id, name=name, code=code)
            session.add(dept)
            departments.append(dept)
        await session.flush()
        print(f"Seeded {len(dept_data)} departments.")

        # 2. Seed Staff Accounts (10 Doctors & 10 Nurses per department)
        password_h = get_password_hash("Admin123")
        doctors = []
        nurses = []
        
        # Admin Account
        admin = StaffAccount(
            id="STF-ADMIN",
            name="Dr. Vikram Aditya",
            email="admin@atralos.com",
            password_hash=password_h,
            role="admin",
            status="Active",
            department_id="DEP-CLIN"
        )
        session.add(admin)

        for d_id, name, code in dept_data:
            for i in range(1, 11):
                # Doctor
                doc_id = f"DOC-{code}-{i:02d}"
                doc = StaffAccount(
                    id=doc_id,
                    name=f"Dr. {name} Doctor {i}",
                    email=f"doc.{code.lower()}.{i}@atralos.com",
                    password_hash=password_h,
                    role="doctor",
                    status="Active",
                    department_id=d_id,
                    license=f"MCI-{code}-{100000+i}",
                    specialization=f"{name} Specialist",
                    qualification="MD / MS"
                )
                session.add(doc)
                doctors.append(doc)

                # Nurse
                nur_id = f"NUR-{code}-{i:02d}"
                nur = StaffAccount(
                    id=nur_id,
                    name=f"Nurse {name} Nurse {i}",
                    email=f"nur.{code.lower()}.{i}@atralos.com",
                    password_hash=password_h,
                    role="nurse",
                    status="Active",
                    department_id=d_id,
                    qualification="B.Sc. Nursing"
                )
                session.add(nur)
                nurses.append(nur)
                
        await session.flush()
        print(f"Seeded {len(doctors)} doctors and {len(nurses)} nurses.")

        # 3. Seed Clinical Teams (10 members each for ER, ICU, OT, Ward)
        team_configs = [
            ("TM-ER-A", "ER Trauma Team A", "DEP-ER"),
            ("TM-ICU-B", "ICU Critical Care Team B", "DEP-ICU"),
            ("TM-OT-C", "Surgical Team C", "DEP-OT"),
            ("TM-WARD-D", "General Ward Care Team D", "DEP-NURS"),
        ]
        
        for t_id, name, d_id in team_configs:
            # Assign team leader
            doc_leader = f"DOC-{d_id.split('-')[1]}-01"
            team = ClinicalTeam(
                id=t_id,
                name=name,
                department_id=d_id,
                leader_id=doc_leader
            )
            session.add(team)
            await session.flush()

            # Assign 10 members (5 docs, 5 nurses from that department)
            code = d_id.split('-')[1]
            for i in range(1, 6):
                await session.execute(team_members.insert().values(team_id=t_id, staff_id=f"DOC-{code}-{i:02d}"))
                await session.execute(team_members.insert().values(team_id=t_id, staff_id=f"NUR-{code}-{i:02d}"))
                
        await session.flush()
        print("Seeded clinical teams with 10 members each.")

        # 4. Seed Ward Beds
        for i in range(1, 25):
            bed = WardBed(id=f"BED-{i:02d}", ward_name="General Ward A", bed_number=f"Bed {i}", status="Available")
            session.add(bed)
        for i in range(1, 13):
            bed = WardBed(id=f"ICU-BED-{i:02d}", ward_name="ICU Ward B", bed_number=f"Bed {i}", status="Available")
            session.add(bed)
        await session.flush()

        # 5. Seed Patients & Queues (10 Patients per interface/status)
        patients = []
        for i in range(1, 141):
            p_id = f"AURA-2026-{i:04d}"
            # Encrypt PII
            p = Patient(
                id=p_id,
                name=pii_service.encrypt(f"Patient Name {i}"),
                dob=pii_service.encrypt("1990-01-01"),
                gender="Male" if i % 2 == 0 else "Female",
                mobile=pii_service.encrypt(f"987654{i:04d}"),
                blood_group="O+" if i % 4 == 0 else "A+",
                emergency=pii_service.encrypt("9111223344"),
                insurance=pii_service.encrypt("AIG-100439201"),
                abha_id=pii_service.encrypt(f"{i:02d}-4829-1039-4820"),
                consent_academic=True,
                consent_commercial=True,
                consent_future=True,
                address=pii_service.encrypt("123 Main St, New Delhi"),
                occupation=pii_service.encrypt("Engineer"),
                marital_status=pii_service.encrypt("Single"),
                allergies=pii_service.encrypt("Sulfa drugs"),
                chronic_conditions=pii_service.encrypt("None"),
                referred_by=pii_service.encrypt("Self")
            )
            session.add(p)
            patients.append(p)
        await session.flush()
        print(f"Seeded {len(patients)} patients with encrypted PII.")

        # Assign patients to specific queues (10 patients per queue)
        # Queue 1: OPD Waiting (Booked)
        for idx, p in enumerate(patients[0:10], 1):
            p.status = "Booked"
            appt = Appointment(
                id=f"APT-001-{idx:02d}",
                patient_id=p.id,
                doctor_id="DOC-CLIN-01",
                department="DEP-CLIN",
                date="2026-07-12",
                time=f"10:{idx*5:02d}",
                type="OPD",
                status="Booked",
                token=idx
            )
            session.add(appt)

        # Queue 2: Nurses Vitals Checks Bay
        for idx, p in enumerate(patients[10:20], 1):
            p.status = "Checked In"
            appt = Appointment(
                id=f"APT-002-{idx:02d}",
                patient_id=p.id,
                doctor_id="DOC-CLIN-02",
                department="DEP-CLIN",
                date="2026-07-12",
                time=f"11:{idx*5:02d}",
                type="OPD",
                status="Checked In",
                token=idx
            )
            session.add(appt)

        # Queue 3: In Consultation (Doctor)
        for idx, p in enumerate(patients[20:30], 1):
            p.status = "In Consultation"
            appt = Appointment(
                id=f"APT-003-{idx:02d}",
                patient_id=p.id,
                doctor_id="DOC-CLIN-03",
                department="DEP-CLIN",
                date="2026-07-12",
                time=f"12:{idx*5:02d}",
                type="OPD",
                status="In Consultation",
                token=idx
            )
            session.add(appt)

        # Queue 4: Emergency/Trauma
        for idx, p in enumerate(patients[30:40], 1):
            p.status = "Emergency"
            er_case = EmergencyCase(
                id=f"ER-2026-{idx:02d}",
                patient_id=p.id,
                triage_level="Red" if idx <= 2 else "Orange" if idx <= 5 else "Yellow",
                chief_complaint="Trauma case, chest pain",
                brought_by="Ambulance Tri-01",
                status="Active",
                assigned_team_id="TM-ER-A"
            )
            session.add(er_case)

        # Queue 5: ICU Beds
        for idx, p in enumerate(patients[40:50], 1):
            p.status = "ICU"
            bed_id = f"ICU-BED-{idx:02d}"
            # Lock Bed
            result = await session.execute(select(WardBed).where(WardBed.id == bed_id))
            bed = result.scalars().first()
            if bed:
                bed.status = "Occupied"
                bed.patient_id = p.id
            
            icu_admit = IcuAdmission(
                id=f"ICU-2026-{idx:02d}",
                patient_id=p.id,
                bed_number=bed_id,
                diagnosis="Post-cardiac arrest support",
                ventilator_status=True if idx % 2 == 0 else False,
                isolation_flag=True if idx == 10 else False,
                acuity_level="Critical" if idx <= 4 else "Stable",
                nurse_id="NUR-ICU-01",
                apache_score=15.5,
                sofa_score=4,
                ews_score=5,
                assigned_team_id="TM-ICU-B"
            )
            session.add(icu_admit)

        # Queue 6: Radiology Queue (Pending Scans)
        for idx, p in enumerate(patients[50:60], 1):
            p.status = "Radiology"
            scan_order = Investigation(
                id=f"INV-RAD-{idx:02d}",
                patient_id=p.id,
                type="Radiology",
                test_name="Chest CT Scan" if idx % 2 == 0 else "MRI Brain",
                status="Pending",
                results={},
                return_to_doctor=True
            )
            session.add(scan_order)

        # Queue 7: Laboratory Queue (Pending Lab Tests)
        for idx, p in enumerate(patients[60:70], 1):
            p.status = "Laboratory"
            lab_order = Investigation(
                id=f"INV-LAB-{idx:02d}",
                patient_id=p.id,
                type="Lab",
                test_name="CBC Panel" if idx % 2 == 0 else "Liver Function Test",
                status="Pending",
                results={},
                return_to_doctor=True
            )
            session.add(lab_order)

        # Queue 8: Pharmacy Dispensing Queue
        for idx, p in enumerate(patients[70:80], 1):
            p.status = "Pharmacy"
            record = ClinicalRecord(
                id=f"REC-{idx:02d}",
                patient_id=p.id,
                doctor_id="DOC-CLIN-01",
                doctor_name="Dr. Vikram Aditya",
                s="Fatigue and cough",
                o="Vitals stable",
                a=[{"code": "J06.9", "desc": "Acute upper respiratory infection"}],
                p="Dispense basic meds",
                signed=True,
                signee="Dr. Vikram Aditya"
            )
            session.add(record)
            
            rx = Prescription(
                id=f"RX-{idx:02d}",
                clinical_record_id=f"REC-{idx:02d}",
                medicines=[
                    {"name": "Paracetamol 650mg", "dosage": "1-0-1", "duration": "5 Days"},
                    {"name": "Amoxicillin 500mg", "dosage": "1-1-1", "duration": "7 Days"}
                ],
                status="Pending"
            )
            session.add(rx)

        # Queue 9: Finance Pending Bills
        for idx, p in enumerate(patients[80:90], 1):
            p.status = "Finance"
            invoice = BillingInvoice(
                id=f"INV-{idx:02d}",
                patient_id=p.id,
                services=[
                    {"name": "Doctor Consultation Fee", "price": 500.0, "qty": 1},
                    {"name": "Laboratory Panel Fee", "price": 1200.0, "qty": 1}
                ],
                subtotal=1700.0,
                gst=306.0,
                insurance_cover=1000.0,
                total=1006.0,
                status="Pending"
            )
            session.add(invoice)

        # Queue 10: OT Operation Theatre Scheduled
        for idx, p in enumerate(patients[90:100], 1):
            p.status = "Surgery"
            surgery = Surgery(
                id=f"SURG-{idx:02d}",
                patient_id=p.id,
                procedure_name="Laparoscopic Cholecystectomy" if idx % 2 == 0 else "Appendectomy",
                surgeon_id="DOC-OT-01",
                anesthetist_id="DOC-OT-02",
                room_number=f"OT-Room-{1 if idx <= 5 else 2}",
                scheduled_date="2026-07-12",
                scheduled_time=f"{8+idx}:00",
                status="Scheduled",
                pre_op_checklist={"npo_verified": True, "consent_signed": True}
            )
            session.add(surgery)

            sched = OtSchedule(
                id=f"OTS-{idx:02d}",
                room_number=f"OT-Room-{1 if idx <= 5 else 2}",
                procedure_name=surgery.procedure_name,
                surgeon_id="DOC-OT-01",
                date="2026-07-12",
                time=surgery.scheduled_time,
                status="Scheduled"
            )
            session.add(sched)

        # Queue 11: Blood Bank Requests
        for idx, p in enumerate(patients[100:110], 1):
            p.status = "Blood Bank"
            blood_req = BloodRequest(
                id=f"BLR-2026-{idx:02d}",
                patient_id=p.id,
                blood_group="O+" if idx % 2 == 0 else "A+",
                units=2,
                status="Pending"
            )
            session.add(blood_req)

        # Queue 12: Diet Kitchen Orders
        for idx, p in enumerate(patients[110:120], 1):
            p.status = "General Ward"
            diet_ord = DietOrder(
                id=f"DT-ORD-2026-{idx:02d}",
                patient_id=p.id,
                diet_type="Diabetic Diet" if idx % 2 == 0 else "Regular Soft",
                preference="Veg",
                allergens=["Peanuts"] if idx == 5 else [],
                breakfast="Pending",
                lunch="Pending",
                dinner="Pending"
            )
            session.add(diet_ord)

        # Queue 13: Ambulance Dispatch Trips
        for idx, p in enumerate(patients[120:130], 1):
            p.status = "Ambulance Dispatch"
            fleet_id = f"AMB-{idx:02d}"
            trip = AmbulanceTrip(
                id=f"TRIP-2026-{idx:02d}",
                vehicle_id=fleet_id,
                caller_name=f"Emergency Caller {idx}",
                pickup_location=f"Sector {idx}, Noida",
                chief_complaint="Difficulty breathing",
                urgency="Critical" if idx <= 5 else "Routine",
                status="Dispatched"
            )
            session.add(trip)

        # 6. Seed Ambulance Fleet
        for idx in range(1, 13):
            amb = AmbulanceFleet(
                id=f"AMB-{idx:02d}",
                vehicle_num=f"DL-01-AM-{1000+idx}",
                type="ALS" if idx <= 4 else "BLS" if idx <= 8 else "Transport",
                status="On-Trip" if idx <= 10 else "Available",
                insurance_expiry="2027-01-01",
                last_service_date="2026-06-01"
            )
            session.add(amb)

        # 7. Seed Devices
        for idx in range(1, 11):
            dev = Device(
                id=f"DEV-{idx:02d}",
                name=f"Philips ICU Monitor Model {idx}",
                type="Patient Monitor",
                department="DEP-ICU",
                location=f"Bed {idx}",
                serial_number=f"SN-PH-ICU-882{idx}",
                status="Active",
                last_service_date="2026-05-15",
                maintenance_due="2026-11-15"
            )
            session.add(dev)

        # 8. Seed Complaints
        for idx in range(1, 11):
            comp = Complaint(
                id=f"CMP-{idx:02d}",
                title=f"ECG Signal Noise Bed {idx}",
                category="Device Malfunction",
                department="DEP-ICU",
                priority="High" if idx <= 4 else "Medium",
                status="Open" if idx <= 8 else "In Progress",
                reported_by="NUR-ICU-01",
                assigned_to="STF-ADMIN",
                description="Intermittent signal loss on Lead II",
                comments=[]
            )
            session.add(comp)

        # 9. Seed Blood Inventory
        groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        components = ["Whole Blood", "PRBC", "FFP", "Platelets"]
        idx = 1
        for g in groups:
            for c in components:
                inv = BloodInventory(
                    id=f"BLI-{idx:03d}",
                    blood_group=g,
                    component=c,
                    units=15 if c == "Whole Blood" else 20,
                    expiry="2026-08-15"
                )
                session.add(inv)
                idx += 1

        # 10. Seed Lab Reagents
        for idx in range(1, 11):
            reagent = LabReagent(
                id=f"REAG-{idx:02d}",
                name=f"CBC Diluent Reagent {idx}",
                stock=25,
                expiry="2026-12-15",
                status="OK",
                reorder_level=5
            )
            session.add(reagent)

        # 11. Seed Pharmacy Drugs
        for idx in range(1, 11):
            drug = DrugInventory(
                id=f"DRG-{idx:02d}",
                name=f"Paracetamol 650mg Tablet {idx}",
                stock=500,
                expiry="2027-06-01",
                status="OK",
                batch=f"BT-PR-{200+idx}",
                reorder_level=100,
                category="Analgesic"
            )
            session.add(drug)

        await session.commit()
        print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_database())
