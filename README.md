# AtralOS (formerly HealthOS) — Hospital EHR & Data Management

AtralOS is a modern, high-fidelity Hospital Electronic Health Records (EHR) and administrative workflow management system. It features client-side Zero-Knowledge Encryption for PII, a reactive Convex.dev backend, and a comprehensive role-based workflow designed to satisfy HIPAA, GDPR, and DPDPA compliance.

---

## 🚀 Tech Stack

* **Frontend**: Vanilla HTML5, CSS3, and JavaScript (ES6 Modules) powered by **Vite**.
* **Database & Realtime Backend**: **Convex** (`convex` NPM package for reactive web socket subscriptions, queries, and mutations).
* **Cryptography**: Client-side **AES-GCM (256-bit)** using the Web Crypto API for zero-knowledge patient data privacy.
* **CI/CD**: GitHub Actions workflow deploying build output (`./dist`) to GitHub Pages.

---

## 🤖 Guide for AI Agents (Agentic Instructions)

If you are an AI agent developer or autonomous coding system working with AtralOS, please refer to this section to understand the layout, system access, and element mapping.

### 🔑 Authentication
* **Default Login Page**: Appears as a full-screen glass overlay (`#login-overlay`).
* **Credentials**:
  * **Username**: `User`
  * **Password**: `Admin123`

### 🗺️ User Roles & Navigation
The application uses a simulated global environment. After logging in, select roles from the dropdown in the top-right corner of the top navbar (`#global-role-select`) to change panels.
* **Available Roles**:
  * `admin`: Super Admin dashboard (Staff HR, equipment, complaints, system settings, security, and audit logs).
  * `reception`: Patient registration (with webcam photo capture, symptom triage, ABHA IDs, consent) and appointment scheduling.
  * `nursing`: Checked-in queues, patient vitals recording, bed utilization grids, and shift handovers.
  * `doctor`: Clinical SOAP consultations, prescription builder, diagnostics referrals, e-sign controls.
  * `lab`: Pathology tests queue, turnaround stats, sample tracking, QC control.
  * `radiology`: Scan orders queue, template selector, DICOM reports, image uploads.
  * `pharmacy`: Prescriptions dispatch desk, inventory levels, expiry warnings.
  * `finance`: Outpatient invoicing, department revenues, claim pre-auth status.
  * `patient`: Mobile simulator preview of the patient portal.

### 🧩 Key Element Selectors (DOM ID Cheat Sheet)

* **Common Elements**:
  * Role Dropdown: `select#global-role-select`
  * Global Search: `input#global-patient-search`
  * Notification Bell: `div#notification-bell`
* **Super Admin Panel** (`#role-panel-admin`):
  * Open System Settings: `button` in topnav (triggers `window.navigateToSettings()`)
  * Settings Panel: `div#admin-settings-panel`
  * Audit Logs Viewport: `div#audit-logs-viewport`
* **Reception Panel** (`#role-panel-reception`):
  * Registration Form: `form#reception-registration-form`
  * Webcam Capture: `button#btn-capture-photo` -> opens `div#modal-webcam`
  * Symptom Triage Check: `textarea#symptom-triage-input` -> click `button#btn-triage-check`
* **Nursing Panel** (`#role-panel-nursing`):
  * Vitals Entry: `form#nursing-vitals-form` (inputs: `BP`, `temp`, `spo2`, `pulse`, `sugar`)
  * Bed Grid: `div#bed-management-grid` (24-bed visual status)
* **Doctor Panel** (`#role-panel-doctor`):
  * SOAP Textareas: `#soap-s`, `#soap-o`, `#soap-a-search`, `#soap-p`
  * Investigation Selector: Lab & Radiology chip triggers
  * E-Sign/Finalize: `button#btn-doc-esign-finalize` -> opens signature pad `div#modal-doctor-esign`
* **Lab / Radiology** (`#role-panel-lab` / `#role-panel-radiology`):
  * Submit Report: `button#btn-lab-submit-final` / `button#btn-radiology-submit`

---

## 🛠️ Installation & Local Development

### Prerequisites
* Node.js (v18+)
* NPM

### Setup
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/auratral/AtralOS.git
   cd AtralOS
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the Vite frontend server locally (defaults to `http://localhost:3000`):
   ```bash
   npm run dev
   ```
4. Start the Convex local/cloud dev backend:
   ```bash
   npx convex dev
   ```

---

## 🔒 Security & Regulatory Compliance (HIPAA, GDPR, DPDPA)

1. **Decoupled Demographics & Clinical Readings (HIPAA *Minimum Necessary*)**:
   * Patient vital signs (`bp`, `temp`, `spo2`, `pulse`, `sugar`) are stored in a standalone `vitals` table.
   * Demographic data is stored in the `patients` table.
   * Both tables relate only via a pseudonymized `patientId` string (e.g. `PAT-XXXX`), isolating clinical history from general reception queries.
2. **Zero-Knowledge Encryption-at-Rest**:
   * PII attributes (`name`, `dob`, `mobile`, `emergency`, `insurance`, and `abhaId`) are encrypted on the client side using **AES-GCM-256** prior to sending database mutations to Convex.
   * Key derivation is managed on-client from the hospital-wide passphrase (`AuratralHospitalOSSecurePIIKey2026!`). The cloud database database contains only encrypted base64 ciphertexts.
3. **GDPR / DPDPA Consent Log**:
   * Patient portal contains explicit, verifiable toggles for consent to clinical research, secondary academic use, and notification preferences.

---

## 🔄 Patient Lifecycle Walkthrough (End-to-End Simulation)

To test the application's core patient management flow:
1. **Login**: Go to the site, input `User` / `Admin123`.
2. **Register**: Switch to the **Receptionist** role. Fill out the Patient Registration Form, click the Webcam Capture to take a placeholder photo, accept the Consent forms, and click **Submit Patient**.
3. **Book Appointment**: Select the newly registered patient, pick a doctor/department, and click **Schedule Appointment**.
4. **Vitals Station**: Switch to the **Nurse** role. Select the patient in the queue, enter vital readings (BP, Temp, SpO2, Pulse, Blood Sugar), and click **Save Vitals & Send to Doctor**.
5. **Consultation**: Switch to the **Doctor** role. Select the patient, input SOAP notes, click the Lab/Radiology tags to order diagnostic tests, sign the digital e-signature pad, and click **Refer for Investigation**.
6. **Diagnostics**: Switch to the **Lab** (or **Radiology**) role. Pick the active test, input values/observations, upload files if needed, and click **Finalize & Notify**.
7. **Recall/Review**: Switch back to the **Nurse** role. The patient will appear highlighted in the queue with a **Results Ready** badge. Click **Send to Doctor** to put them back in consultation.
8. **Discharge**: Switch to the **Doctor** role, review the lab results under the patient details panel, and click **Close & Discharge Case** to complete the cycle.
