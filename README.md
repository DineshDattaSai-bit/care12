# CareQ - Smart Hospital Patient Flow & Clinical Management Platform

CareQ is a full-stack hospital operations platform designed to coordinate patient journeys — from registration and waiting queue management to doctor consultations, diagnostics, bed allocation, clinical document uploads, and discharge.

---

## 🌟 Key Features

- **📊 Live Hospital Dashboard**: Real-time tracking of patient counts, department bottlenecks, active queues, and bed occupancy.
- **👤 Patient Registration & Directory**: Unique patient ID generation (`CQ0001`, `CQ0002`), demographic recording, and status progression.
- **📋 Department Queue System**: Live waiting lists categorized by department with status updates.
- **🛏️ Bed Management Command Center**: Visual bed allocation across departments (Emergency, Cardiology, Neurology, General Ward, etc.) with Available/Occupied/Cleaning/Maintenance statuses.
- **📑 Clinical Reports & Medical Document Repository**:
  - Searchable patient records.
  - File upload system (PDF, JPG, PNG, DOCX, TXT) for Lab Reports, Doctor Prescriptions, Radiology & Scans, and Discharge Summaries.
  - In-browser document preview, download, and deletion.
  - Printable Patient Clinical Summary sheet.
- **📜 Chronological Audit Trail**: Full timeline logging of every patient transition, status update, and document upload.
- **🔐 Role-Based Authentication**: Secure bcrypt password encryption, session token handling, and role normalization (Admin, Nurse, Registration Staff, Department User).

---

## 🚀 Getting Started

### 1. Prerequisites
- [Node.js](https://nodejs.org/) (v16 or higher)
- SQLite3

### 2. Installation
```bash
git clone https://github.com/DineshDattaSai-bit/care12.git
cd care12
npm install
```

### 3. Initialize Database & Run Server
```bash
# Initialize SQLite tables & seed data
node database/database.js

# Start the application
node server.js
```

### 4. Access the Application
Open your browser and navigate to:
- **Landing Page**: `http://localhost:3000/`
- **Operations Dashboard**: `http://localhost:3000/dashboard`
- **Clinical Reports & Uploads**: `http://localhost:3000/reports`
- **Patient Queue**: `http://localhost:3000/queue`
- **Bed Management**: `http://localhost:3000/beds`
- **Staff Sign In**: `http://localhost:3000/login`

---

## 🛠️ Tech Stack
- **Backend**: Node.js, Express.js
- **Database**: SQLite3 (better-sqlite3)
- **File Uploads**: Multer
- **Security**: Bcrypt password hashing
- **Frontend**: Responsive HTML5, CSS3 (Modern Flex/Grid), Vanilla JavaScript
