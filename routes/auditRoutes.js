const express = require("express");
const Database = require("better-sqlite3");
const path = require("path");

const router = express.Router();

const db = new Database(
    path.join(__dirname, "..", "database", "careq.db")
);

// GET patient audit history
// GET /api/audit/patient/:patientId
router.get("/patient/:patientId", (req, res) => {
    try {
        const patientId = String(req.params.patientId || "").trim();

        if (!patientId) {
            return res.status(400).json({
                success: false,
                message: "Patient ID is required"
            });
        }

        const logs = db.prepare(`
            SELECT
                id,
                user_id,
                action,
                patient_id,
                previous_status,
                new_status,
                department,
                performed_by,
                performed_role,
                created_at
            FROM audit_logs
            WHERE patient_id = ?
            ORDER BY datetime(created_at) ASC, id ASC
        `).all(patientId);

        return res.json({
            success: true,
            patient_id: patientId,
            logs
        });
    } catch (error) {
        console.error("Audit history error:", error);

        return res.status(500).json({
            success: false,
            message: "Unable to load patient history"
        });
    }
});

module.exports = router;
