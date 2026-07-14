from sqlalchemy import String, Integer, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class BloodInventory(Base):
    __tablename__ = "blood_inventory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    blood_group: Mapped[str] = mapped_column(String, nullable=False)
    component: Mapped[str] = mapped_column(String, nullable=False)  # Whole Blood, PRBC, FFP, Platelets
    units: Mapped[int] = mapped_column(Integer, default=0)
    expiry: Mapped[str] = mapped_column(String, nullable=False)

class Donor(Base):
    __tablename__ = "donors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    blood_group: Mapped[str] = mapped_column(String, nullable=False)
    mobile: Mapped[str] = mapped_column(String, nullable=False)
    donation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    eligibility: Mapped[str] = mapped_column(String, default="Eligible")

class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    blood_group: Mapped[str] = mapped_column(String, nullable=False)
    units: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="Pending")

class DietOrder(Base):
    __tablename__ = "diet_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    diet_type: Mapped[str] = mapped_column(String, nullable=False)
    preference: Mapped[str] = mapped_column(String, default="Veg")
    allergens: Mapped[dict] = mapped_column(JSON, default=list)
    breakfast: Mapped[str] = mapped_column(String, default="Pending")
    lunch: Mapped[str] = mapped_column(String, default="Pending")
    dinner: Mapped[str] = mapped_column(String, default="Pending")

class DrugInventory(Base):
    __tablename__ = "drug_inventory"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    expiry: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="OK")
    batch: Mapped[str] = mapped_column(String, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=100)
    category: Mapped[str] = mapped_column(String, default="General")

class NarcoticsRegister(Base):
    __tablename__ = "narcotics_register"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    drug_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # Dispensed, Received, Wasted
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    authorized_by: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LabReagent(Base):
    __tablename__ = "lab_reagents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    expiry: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="OK")
    reorder_level: Mapped[int] = mapped_column(Integer, default=5)

class AmbulanceFleet(Base):
    __tablename__ = "ambulance_fleet"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_num: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Available")
    insurance_expiry: Mapped[str] = mapped_column(String, nullable=False)
    last_service_date: Mapped[str] = mapped_column(String, nullable=False)

class AmbulanceTrip(Base):
    __tablename__ = "ambulance_trips"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(String, ForeignKey("ambulance_fleet.id", ondelete="SET NULL"), nullable=True)
    caller_name: Mapped[str] = mapped_column(String, nullable=False)
    pickup_location: Mapped[str] = mapped_column(String, nullable=False)
    chief_complaint: Mapped[str] = mapped_column(String, nullable=False)
    urgency: Mapped[str] = mapped_column(String, default="Routine")
    status: Mapped[str] = mapped_column(String, default="Dispatched")
    call_received: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    handoff_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    serial_number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Active")
    last_service_date: Mapped[str] = mapped_column(String, nullable=False)
    maintenance_due: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str] = mapped_column(String, nullable=True)

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, default="Medium")
    status: Mapped[str] = mapped_column(String, default="Open")
    reported_by: Mapped[str] = mapped_column(String, nullable=False)
    assigned_to: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    resolution: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    comments: Mapped[dict] = mapped_column(JSON, default=list)

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, default="Info")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LabReagentLog(Base):
    __tablename__ = "lab_reagent_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    reagent_id: Mapped[str] = mapped_column(String, ForeignKey("lab_reagents.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False) # e.g. "Order Placed", "Stock Refilled", "Used in CBC Test"
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
