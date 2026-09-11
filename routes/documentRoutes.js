const express = require("express");
const path = require("path");
const fs = require("fs");
const multer = require("multer");
const Database = require("better-sqlite3");

const router = express.Router();

// Database connection
const dbPath = path.join(__dirname, "..", "database", "careq.db");
const db = new Database(dbPath);

// Ensure upload directory exists
const uploadDir = path.join(__dirname, "..", "public", "uploads");
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

// Ensure patient_documents table exists
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

// Multer storage setup
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
        const cleanOriginalName = file.originalname.replace(/[^a-zA-Z0-9.-]/g, "_");
        cb(null, `${uniqueSuffix}-${cleanOriginalName}`);
    }
});

// Allowed file types: PDF, images, Word docs, text
const fileFilter = (req, file, cb) => {
    const allowedMimes = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ];
    if (allowedMimes.includes(file.mimetype) || file.originalname.match(/\.(pdf|jpe?g|png|webp|gif|docx?|txt)$/i)) {
        cb(null, true);
    } else {
        cb(new Error("File type not supported. Allowed formats: PDF, Images (JPG, PNG), Word documents (.docx), and TXT."));
    }
};

const upload = multer({
    storage: storage,
    limits: { fileSize: 25 * 1024 * 1024 }, // 25 MB
    fileFilter: fileFilter
});

// ==========================================
// 1. UPLOAD DOCUMENT
// ==========================================
router.post("/upload", (req, res) => {
    upload.single("file")(req, res, function (err) {
        if (err instanceof multer.MulterError) {
            return res.status(400).json({ success: false, message: `Upload error: ${err.message}` });
        } else if (err) {
            return res.status(400).json({ success: false, message: err.message });
        }

        if (!req.file) {
            return res.status(400).json({ success: false, message: "No document file was uploaded." });
        }

        const {
            patient_id,
            document_name,
            document_type,
            uploaded_by,
            notes
        } = req.body;

        const cleanPatientId = String(patient_id || "").trim().toUpperCase();
        const cleanDocName = String(document_name || req.file.originalname).trim();
        const cleanDocType = String(document_type || "Lab Report").trim();
        const cleanUploadedBy = String(uploaded_by || "Clinical Staff").trim();
        const cleanNotes = String(notes || "").trim();

        if (!cleanPatientId) {
            try { fs.unlinkSync(req.file.path); } catch (e) {}
            return res.status(400).json({ success: false, message: "Patient ID is required." });
        }

        try {
            const patient = db.prepare("SELECT * FROM patients WHERE patient_id = ?").get(cleanPatientId);
            if (!patient) {
                try { fs.unlinkSync(req.file.path); } catch (e) {}
                return res.status(404).json({
                    success: false,
                    message: `Patient with ID ${cleanPatientId} not found in database.`
                });
            }

            const relativePath = `/uploads/${req.file.filename}`;

            const result = db.prepare(`
                INSERT INTO patient_documents (
                    patient_id,
                    document_name,
                    document_type,
                    file_name,
                    file_path,
                    file_size,
                    mime_type,
                    uploaded_by,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).run(
                cleanPatientId,
                cleanDocName,
                cleanDocType,
                req.file.filename,
                relativePath,
                req.file.size,
                req.file.mimetype,
                cleanUploadedBy,
                cleanNotes
            );

            try {
                db.prepare(`
                    INSERT INTO audit_logs (
                        action,
                        patient_id,
                        previous_status,
                        new_status,
                        department,
                        performed_by,
                        performed_role
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                `).run(
                    `Document Uploaded: ${cleanDocType} - ${cleanDocName}`,
                    cleanPatientId,
                    patient.status,
                    patient.status,
                    patient.department,
                    cleanUploadedBy,
                    "Staff"
                );
            } catch (auditErr) {
                console.error("Audit log error on document upload:", auditErr);
            }

            const newDoc = db.prepare("SELECT * FROM patient_documents WHERE id = ?").get(result.lastInsertRowid);

            return res.status(201).json({
                success: true,
                message: "Document uploaded and attached successfully.",
                document: newDoc
            });
        } catch (dbErr) {
            console.error("Document upload DB error:", dbErr);
            try { fs.unlinkSync(req.file.path); } catch (e) {}
            return res.status(500).json({ success: false, message: "Database error while saving document record." });
        }
    });
});

// ==========================================
// 2. GET ALL DOCUMENTS FOR A PATIENT
// ==========================================
router.get("/patient/:patientId", (req, res) => {
    try {
        const patientId = String(req.params.patientId || "").trim().toUpperCase();
        const patient = db.prepare("SELECT * FROM patients WHERE patient_id = ?").get(patientId);

        if (!patient) {
            return res.status(404).json({
                success: false,
                message: `Patient ${patientId} not found.`
            });
        }

        const documents = db.prepare(`
            SELECT * FROM patient_documents
            WHERE patient_id = ?
            ORDER BY id DESC
        `).all(patientId);

        return res.json({
            success: true,
            patient,
            count: documents.length,
            documents
        });
    } catch (err) {
        console.error("Get patient documents error:", err);
        return res.status(500).json({ success: false, message: "Unable to retrieve patient documents." });
    }
});

// ==========================================
// 3. GET ALL RECENT DOCUMENTS IN SYSTEM
// ==========================================
router.get("/recent", (req, res) => {
    try {
        const documents = db.prepare(`
            SELECT d.*, p.name AS patient_name, p.department, p.status AS patient_status
            FROM patient_documents d
            LEFT JOIN patients p ON d.patient_id = p.patient_id
            ORDER BY d.id DESC
            LIMIT 50
        `).all();

        return res.json({
            success: true,
            count: documents.length,
            documents
        });
    } catch (err) {
        console.error("Get recent documents error:", err);
        return res.status(500).json({ success: false, message: "Unable to load recent documents." });
    }
});

// ==========================================
// 4. DELETE DOCUMENT
// ==========================================
router.delete("/:id", (req, res) => {
    try {
        const docId = Number(req.params.id);
        const doc = db.prepare("SELECT * FROM patient_documents WHERE id = ?").get(docId);

        if (!doc) {
            return res.status(404).json({ success: false, message: "Document not found." });
        }

        const fullDiskPath = path.join(uploadDir, doc.file_name);
        if (fs.existsSync(fullDiskPath)) {
            try { fs.unlinkSync(fullDiskPath); } catch (e) {}
        }

        db.prepare("DELETE FROM patient_documents WHERE id = ?").run(docId);

        try {
            db.prepare(`
                INSERT INTO audit_logs (
                    action,
                    patient_id,
                    department,
                    performed_by,
                    performed_role
                ) VALUES (?, ?, ?, ?, ?)
            `).run(
                `Document Deleted: ${doc.document_name}`,
                doc.patient_id,
                "Records",
                "Staff",
                "Staff"
            );
        } catch (e) {}

        return res.json({
            success: true,
            message: "Document deleted successfully."
        });
    } catch (err) {
        console.error("Delete document error:", err);
        return res.status(500).json({ success: false, message: "Unable to delete document." });
    }
});

module.exports = router;
