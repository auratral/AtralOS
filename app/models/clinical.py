from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    department: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    time: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Booked")
    token: Mapped[int] = mapped_column(Integer, nullable=False)
    investigation_status: Mapped[str] = mapped_column(String, default="None")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Vitals(Base):
    __tablename__ = "vitals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    bp: Mapped[str] = mapped_column(String, nullable=True)
    temp: Mapped[str] = mapped_column(String, nullable=True)
    spo2: Mapped[int] = mapped_column(Integer, nullable=True)
    pulse: Mapped[int] = mapped_column(Integer, nullable=True)
    sugar: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    doctor_name: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    s: Mapped[str] = mapped_column(String, nullable=True)
    o: Mapped[str] = mapped_column(String, nullable=True)
    a: Mapped[dict] = mapped_column(JSON, default=list)  # List of diagnoses
    p: Mapped[str] = mapped_column(String, nullable=True)
    signed: Mapped[bool] = mapped_column(Boolean, default=False)
    signee: Mapped[str] = mapped_column(String, nullable=True)
    consent_flag: Mapped[bool] = mapped_column(Boolean, default=True)

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    clinical_record_id: Mapped[str] = mapped_column(String, ForeignKey("clinical_records.id", ondelete="CASCADE"), nullable=False)
    medicines: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="Pending")

class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Pending")
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    return_to_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BillingInvoice(Base):
    __tablename__ = "billing_invoices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    services: Mapped[dict] = mapped_column(JSON, default=list)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    gst: Mapped[float] = mapped_column(Float, nullable=False)
    insurance_cover: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Pending")
    payment_mode: Mapped[str] = mapped_column(String, default="Cash")
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=True)
    ip_address: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
