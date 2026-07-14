from sqlalchemy import String, Integer, Boolean, ForeignKey, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base

# Many-to-many join table for clinical team members
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", String, ForeignKey("clinical_teams.id", ondelete="CASCADE"), primary_key=True),
    Column("staff_id", String, ForeignKey("staff_accounts.id", ondelete="CASCADE"), primary_key=True)
)

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    head_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    staff = relationship("StaffAccount", back_populates="department", foreign_keys="StaffAccount.department_id")
    teams = relationship("ClinicalTeam", back_populates="department")

class StaffAccount(Base):
    __tablename__ = "staff_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Active")
    department_id: Mapped[str] = mapped_column(String, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    license: Mapped[str] = mapped_column(String, nullable=True)
    shift: Mapped[str] = mapped_column(String, default="Morning")
    work_days: Mapped[str] = mapped_column(String, default="Mon,Tue,Wed,Thu,Fri")
    qualification: Mapped[str] = mapped_column(String, nullable=True)
    specialization: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    leave_balance: Mapped[int] = mapped_column(Integer, default=15)
    joining_date: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    department = relationship("Department", back_populates="staff", foreign_keys=[department_id])
    led_teams = relationship("ClinicalTeam", back_populates="leader")
    teams = relationship("ClinicalTeam", secondary=team_members, back_populates="members")

class ClinicalTeam(Base):
    __tablename__ = "clinical_teams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[str] = mapped_column(String, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    leader_id: Mapped[str] = mapped_column(String, ForeignKey("staff_accounts.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    department = relationship("Department", back_populates="teams")
    leader = relationship("StaffAccount", back_populates="led_teams")
    members = relationship("StaffAccount", secondary=team_members, back_populates="teams")

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted PII
    dob: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted PII
    gender: Mapped[str] = mapped_column(String, nullable=False)
    mobile: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted PII
    blood_group: Mapped[str] = mapped_column(String, nullable=False)
    emergency: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted PII
    insurance: Mapped[str] = mapped_column(String, nullable=False)  # Encrypted PII
    abha_id: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    consent_academic: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_commercial: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_future: Mapped[bool] = mapped_column(Boolean, default=False)
    reg_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="OPD Queue")
    photo: Mapped[str] = mapped_column(String, default="")  # Base64 string
    address: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    occupation: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    marital_status: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    allergies: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    chronic_conditions: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    referred_by: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    national_id_type: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    national_id_number: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    email: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    alt_mobile: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    billing_category: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
    emergency_relationship: Mapped[str] = mapped_column(String, nullable=True)  # Encrypted PII
