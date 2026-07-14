import os
import casbin

# Path to the config model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "rbac_model.conf")

enforcer = casbin.Enforcer(MODEL_PATH)

def init_rbac():
    enforcer.clear_policy()

    # 1. Super Admin permissions (global domain '*')
    enforcer.add_policy("role:admin", "*", "system_settings", "write")
    enforcer.add_policy("role:admin", "*", "staff_accounts", "write")
    enforcer.add_policy("role:admin", "*", "audit_logs", "read")
    
    # 2. Reception permissions
    enforcer.add_policy("role:receptionist", "reception", "patients", "write")
    enforcer.add_policy("role:receptionist", "reception", "appointments", "write")
    enforcer.add_policy("role:receptionist", "reception", "patients", "read")
    enforcer.add_policy("role:receptionist", "reception", "appointments", "read")
    
    # 3. Nurse permissions
    enforcer.add_policy("role:nurse", "nursing", "vitals", "write")
    enforcer.add_policy("role:nurse", "nursing", "ward_beds", "write")
    enforcer.add_policy("role:nurse", "nursing", "shift_notes", "write")
    enforcer.add_policy("role:nurse", "nursing", "vitals", "read")
    enforcer.add_policy("role:nurse", "nursing", "ward_beds", "read")
    
    # 4. Doctor permissions
    enforcer.add_policy("role:doctor", "clinical", "clinical_records", "write")
    enforcer.add_policy("role:doctor", "clinical", "prescriptions", "write")
    enforcer.add_policy("role:doctor", "clinical", "investigations", "write")
    enforcer.add_policy("role:doctor", "clinical", "clinical_records", "read")
    enforcer.add_policy("role:doctor", "clinical", "prescriptions", "read")
    enforcer.add_policy("role:doctor", "clinical", "investigations", "read")
    
    # 5. Laboratory permissions
    enforcer.add_policy("role:lab_tech", "laboratory", "lab_results", "write")
    enforcer.add_policy("role:lab_tech", "laboratory", "reagents", "write")
    enforcer.add_policy("role:lab_tech", "laboratory", "lab_results", "read")
    
    # 6. Radiology permissions
    enforcer.add_policy("role:radiologist", "radiology", "scan_reports", "write")
    enforcer.add_policy("role:radiologist", "radiology", "scan_reports", "read")
    
    # 7. Pharmacy permissions
    enforcer.add_policy("role:pharmacist", "pharmacy", "dispensing", "write")
    enforcer.add_policy("role:pharmacist", "pharmacy", "drug_inventory", "write")
    enforcer.add_policy("role:pharmacist", "pharmacy", "dispensing", "read")
    
    # 8. Finance permissions
    enforcer.add_policy("role:finance_officer", "finance", "invoices", "write")
    enforcer.add_policy("role:finance_officer", "finance", "billing", "write")
    enforcer.add_policy("role:finance_officer", "finance", "invoices", "read")
    
    # 9. Emergency Team permissions
    enforcer.add_policy("role:emergency", "emergency", "emergency_cases", "write")
    enforcer.add_policy("role:emergency", "emergency", "triage", "write")
    enforcer.add_policy("role:emergency", "emergency", "emergency_cases", "read")
    
    # 10. ICU Team permissions
    enforcer.add_policy("role:icu", "icu", "icu_admissions", "write")
    enforcer.add_policy("role:icu", "icu", "icu_charting", "write")
    enforcer.add_policy("role:icu", "icu", "ventilators", "write")
    enforcer.add_policy("role:icu", "icu", "icu_admissions", "read")
    
    # 11. OT Team permissions
    enforcer.add_policy("role:ot", "ot", "surgeries", "write")
    enforcer.add_policy("role:ot", "ot", "ot_schedule", "write")
    enforcer.add_policy("role:ot", "ot", "surgeries", "read")
    
    # 12. Blood Bank permissions
    enforcer.add_policy("role:blood_bank", "blood_bank", "blood_inventory", "write")
    enforcer.add_policy("role:blood_bank", "blood_bank", "blood_requests", "write")
    enforcer.add_policy("role:blood_bank", "blood_bank", "blood_inventory", "read")

    # 13. Diet permissions
    enforcer.add_policy("role:diet", "diet", "diet_orders", "write")
    enforcer.add_policy("role:diet", "diet", "diet_orders", "read")

    # 14. Transport/Ambulance permissions
    enforcer.add_policy("role:transport", "ambulance", "fleet", "write")
    enforcer.add_policy("role:transport", "ambulance", "trips", "write")
    enforcer.add_policy("role:transport", "ambulance", "fleet", "read")

    enforcer.save_policy()

init_rbac()

def check_permission(sub: str, dom: str, obj: str, act: str) -> bool:
    # Super admins have global access
    if enforcer.enforce(sub, "*", obj, act):
        return True
    return enforcer.enforce(sub, dom, obj, act)
