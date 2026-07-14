from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class EmergencyCase(Base):
    __tablename__ = "emergency_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    triage_level: Mapped[str] = mapped_column(String, nullable=False)  # Red, Orange, Yellow, Green, Blue
    chief_complaint: Mapped[str] = mapped_column(String, nullable=False)
    brought_by: Mapped[str] = mapped_column(String, nullable=False)
    time_of_arrival: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="Active")  # Active, Completed, Transferred
    disposition: Mapped[str] = mapped_column(String, nullable=True)  # Resus, ER Bed, ICU, Ward, Discharged
    mlc_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    mlc_details: Mapped[dict] = mapped_column(JSON, default=dict)
    assigned_team_id: Mapped[str] = mapped_column(String, ForeignKey("clinical_teams.id", ondelete="SET NULL"), nullable=True)

class IcuAdmission(Base):
    __tablename__ = "icu_admissions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    bed_number: Mapped[str] = mapped_column(String, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String, nullable=False)
    ventilator_status: Mapped[bool] = mapped_column(Boolean, default=False)
    isolation_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    acuity_level: Mapped[str] = mapped_column(String, default="Stable")  # Critical, Stable, Improving
    nurse_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    apache_score: Mapped[float] = mapped_column(Float, default=0.0)
    sofa_score: Mapped[int] = mapped_column(Integer, default=0)
    ews_score: Mapped[int] = mapped_column(Integer, default=0)
    assigned_team_id: Mapped[str] = mapped_column(String, ForeignKey("clinical_teams.id", ondelete="SET NULL"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class IcuCharting(Base):
    __tablename__ = "icu_charting"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String, default="Vitals")  # Vitals, Ventilator
    hr: Mapped[int] = mapped_column(Integer, nullable=True)
    spo2: Mapped[int] = mapped_column(Integer, nullable=True)
    rr: Mapped[int] = mapped_column(Integer, nullable=True)
    etco2: Mapped[int] = mapped_column(Integer, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Surgery(Base):
    __tablename__ = "surgeries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    procedure_name: Mapped[str] = mapped_column(String, nullable=False)
    surgeon_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    anesthetist_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    room_number: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_date: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_time: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Scheduled")  # Scheduled, In-Progress, Completed, Recovery
    pre_op_checklist: Mapped[dict] = mapped_column(JSON, default=dict)

class OtSchedule(Base):
    __tablename__ = "ot_schedule"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    room_number: Mapped[str] = mapped_column(String, nullable=False)
    procedure_name: Mapped[str] = mapped_column(String, nullable=False)
    surgeon_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    time: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Scheduled")

class WardBed(Base):
    __tablename__ = "ward_beds"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ward_name: Mapped[str] = mapped_column(String, nullable=False)
    bed_number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Available")
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)

class GeneralWardAdmission(Base):
    __tablename__ = "general_ward_admissions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    bed_number: Mapped[str] = mapped_column(String, nullable=False)
    assigned_team_id: Mapped[str] = mapped_column(String, ForeignKey("clinical_teams.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
