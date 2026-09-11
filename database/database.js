const Database = require("better-sqlite3");

// Create/Open CareQ database
const db = new Database("database/careq.db");

// ===============================
// USERS TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
`).run();

// ===============================
// PATIENTS TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        department TEXT,
        status TEXT DEFAULT 'Registered',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`).run();

// ===============================
// DEPARTMENTS TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
`).run();

// ===============================
// BEDS TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_number TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        patient_id TEXT
    )
`).run();

// ===============================
// PATIENT JOURNEY TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS patient_journey (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        status TEXT NOT NULL,
        updated_by TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`).run();

// ===============================
// AUDIT LOG TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        action TEXT NOT NULL,

        patient_id TEXT,

        previous_status TEXT,

        new_status TEXT,

        department TEXT,

        performed_by TEXT,

        performed_role TEXT,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`).run();

// ===============================
// ADD MISSING COLUMNS
// ===============================
// This keeps your existing careq.db safe.
// We are NOT deleting the old database.

// Check existing columns
const columns = db.prepare(`
    PRAGMA table_info(audit_logs)
`).all();

const columnNames = columns.map(
    column => column.name
);

// Add previous_status if missing
if (!columnNames.includes("previous_status")) {

    db.prepare(`
        ALTER TABLE audit_logs
        ADD COLUMN previous_status TEXT
    `).run();

}

// Add new_status if missing
if (!columnNames.includes("new_status")) {

    db.prepare(`
        ALTER TABLE audit_logs
        ADD COLUMN new_status TEXT
    `).run();

}

// Add department if missing
if (!columnNames.includes("department")) {

    db.prepare(`
        ALTER TABLE audit_logs
        ADD COLUMN department TEXT
    `).run();

}

// Add performed_by if missing
if (!columnNames.includes("performed_by")) {

    db.prepare(`
        ALTER TABLE audit_logs
        ADD COLUMN performed_by TEXT
    `).run();

}

// Add performed_role if missing
if (!columnNames.includes("performed_role")) {

    db.prepare(`
        ALTER TABLE audit_logs
        ADD COLUMN performed_role TEXT
    `).run();
}

// ===============================
// PATIENT DOCUMENTS TABLE
// ===============================

db.prepare(`
    CREATE TABLE IF NOT EXISTS patient_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        document_name TEXT NOT NULL,
        document_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        mime_type TEXT,
        uploaded_by TEXT DEFAULT 'Staff',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
`).run();

// ===============================
// DATABASE READY
// ===============================

console.log(
    "✅ CareQ database created successfully!"
);

db.close();