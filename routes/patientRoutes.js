const express = require("express");
const Database = require("better-sqlite3");
const path = require("path");

const router = express.Router();


/* =========================================================
   DATABASE
========================================================= */

const db = new Database(
    path.join(
        __dirname,
        "..",
        "database",
        "careq.db"
    )
);

console.log("👤 CareQ Patient System Connected");


/* =========================================================
   ALLOWED PATIENT STATUSES
========================================================= */

const ALLOWED_STATUSES = [

    "Registered",

    "Waiting",

    "Consultation",

    "Diagnostics",

    "Treatment / Observation",

    "Discharge"

];


/* =========================================================
   REGISTER PATIENT
========================================================= */

router.post(
    "/register",
    (req, res) => {

        const {
            name,
            age,
            gender,
            department
        } = req.body;


        /* ---------- VALIDATION ---------- */

        if (
            !name ||
            !age ||
            !gender ||
            !department
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Please fill all patient fields"

            });

        }


        const cleanName =
            name.toString().trim();

        const cleanGender =
            gender.toString().trim();

        const cleanDepartment =
            department.toString().trim();

        const numericAge =
            Number(age);


        if (
            !cleanName ||
            !cleanGender ||
            !cleanDepartment
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Invalid patient information"

            });

        }


        if (
            !Number.isInteger(numericAge) ||
            numericAge < 0 ||
            numericAge > 120
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Please enter a valid age"

            });

        }


        try {

            /* ---------- GENERATE PATIENT ID ---------- */

            const latestPatient =
                db.prepare(`
                    SELECT patient_id
                    FROM patients
                    WHERE patient_id LIKE 'CQ%'
                    ORDER BY id DESC
                    LIMIT 1
                `).get();


            let nextNumber = 1;


            if (latestPatient) {

                const number =
                    parseInt(
                        latestPatient.patient_id
                            .replace("CQ", ""),
                        10
                    );

                if (!isNaN(number)) {

                    nextNumber =
                        number + 1;

                }

            }


            const patientId =
                "CQ" +
                String(nextNumber)
                    .padStart(4, "0");


            /* =================================================
               TRANSACTION
            ================================================= */

            const registerPatient =
                db.transaction(() => {

                    /* ---------- PATIENT ---------- */

                    db.prepare(`
                        INSERT INTO patients
                        (
                            patient_id,
                            name,
                            age,
                            gender,
                            department,
                            status
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?)
                    `).run(

                        patientId,

                        cleanName,

                        numericAge,

                        cleanGender,

                        cleanDepartment,

                        "Registered"

                    );


                    /* ---------- JOURNEY ---------- */

                    db.prepare(`
                        INSERT INTO patient_journey
                        (
                            patient_id,
                            status,
                            updated_by
                        )
                        VALUES
                        (?, ?, ?)
                    `).run(

                        patientId,

                        "Registered",

                        "Registration Staff"

                    );


                    /* ---------- AUDIT ---------- */

                    db.prepare(`
                        INSERT INTO audit_logs
                        (
                            action,
                            patient_id,
                            previous_status,
                            new_status,
                            department,
                            performed_by,
                            performed_role
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                    `).run(

                        "Patient Registered",

                        patientId,

                        null,

                        "Registered",

                        cleanDepartment,

                        "Registration Staff",

                        "Registration Staff"

                    );

                });


            registerPatient();


            console.log(
                "✅ Patient registered:",
                patientId,
                "|",
                cleanName
            );


            res.status(201).json({

                success: true,

                message:
                    "Patient registered successfully",

                patientId,

                patient: {

                    patient_id:
                        patientId,

                    name:
                        cleanName,

                    age:
                        numericAge,

                    gender:
                        cleanGender,

                    department:
                        cleanDepartment,

                    status:
                        "Registered"

                }

            });

        } catch (error) {

            console.error(
                "❌ Patient registration error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to register patient"

            });

        }

    }
);


/* =========================================================
   PATIENT DASHBOARD STATISTICS
=========================================================

   ACTIVE QUEUE
   ----------------
   Waiting patients

   ACTIVE OPERATIONS
   ----------------
   Consultation
   Diagnostics
   Treatment / Observation

   INACTIVE OPERATIONS
   ------------------
   Discharge

========================================================= */

router.get(
    "/stats",
    (req, res) => {

        try {

            /* ---------- REGISTERED PATIENTS ---------- */

            const registeredPatients =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                `).get().count;


            /* ---------- ACTIVE QUEUE ---------- */

            const activeQueue =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                    WHERE status = ?
                `).get(
                    "Waiting"
                ).count;


            /* ---------- ACTIVE OPERATIONS ---------- */

            const activeOperations =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                    WHERE status IN (
                        ?,
                        ?,
                        ?
                    )
                `).get(

                    "Consultation",

                    "Diagnostics",

                    "Treatment / Observation"

                ).count;


            /* ---------- INACTIVE OPERATIONS ---------- */

            const inactiveOperations =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                    WHERE status = ?
                `).get(
                    "Discharge"
                ).count;


            /* ---------- REGISTERED / NOT YET STARTED ---------- */

            const registeredWaiting =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                    WHERE status = ?
                `).get(
                    "Registered"
                ).count;


            /* ---------- TOTAL CURRENTLY ACTIVE ---------- */

            const activePatients =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM patients
                    WHERE status != ?
                `).get(
                    "Discharge"
                ).count;


            res.json({

                success: true,

                registeredPatients,

                activePatients,

                activeQueue,

                activeOperations,

                inactiveOperations,

                registeredWaiting

            });


        } catch (error) {

            console.error(
                "❌ Patient statistics error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to load patient statistics"

            });

        }

    }
);


/* =========================================================
   GET ALL PATIENTS
========================================================= */

router.get(
    "/",
    (req, res) => {

        try {

            const patients =
                db.prepare(`
                    SELECT *
                    FROM patients
                    ORDER BY id DESC
                `).all();


            res.json({

                success: true,

                count:
                    patients.length,

                patients

            });

        } catch (error) {

            console.error(
                "❌ Patient loading error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to load patients"

            });

        }

    }
);


/* =========================================================
   GET SINGLE PATIENT
========================================================= */

router.get(
    "/:patientId",
    (req, res) => {

        const patientId =
            req.params.patientId;


        try {

            const patient =
                db.prepare(`
                    SELECT *
                    FROM patients
                    WHERE patient_id = ?
                `).get(
                    patientId
                );


            if (!patient) {

                return res.status(404).json({

                    success: false,

                    message:
                        "Patient not found"

                });

            }


            res.json({

                success: true,

                patient

            });

        } catch (error) {

            console.error(
                "❌ Patient details error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to load patient details"

            });

        }

    }
);


/* =========================================================
   GET PATIENT JOURNEY
========================================================= */

router.get(
    "/:patientId/journey",
    (req, res) => {

        const patientId =
            req.params.patientId;


        try {

            const patient =
                db.prepare(`
                    SELECT
                        patient_id,
                        name,
                        department,
                        status
                    FROM patients
                    WHERE patient_id = ?
                `).get(
                    patientId
                );


            if (!patient) {

                return res.status(404).json({

                    success: false,

                    message:
                        "Patient not found"

                });

            }


            const journey =
                db.prepare(`
                    SELECT
                        id,
                        patient_id,
                        status,
                        updated_by,
                        created_at
                    FROM patient_journey
                    WHERE patient_id = ?
                    ORDER BY id ASC
                `).all(
                    patientId
                );


            res.json({

                success: true,

                patient,

                journey

            });

        } catch (error) {

            console.error(
                "❌ Patient journey error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to load patient journey"

            });

        }

    }
);


/* =========================================================
   GET PATIENT AUDIT HISTORY
========================================================= */

router.get(
    "/:patientId/audit",
    (req, res) => {

        const patientId =
            req.params.patientId;


        try {

            const patient =
                db.prepare(`
                    SELECT
                        patient_id,
                        name
                    FROM patients
                    WHERE patient_id = ?
                `).get(
                    patientId
                );


            if (!patient) {

                return res.status(404).json({

                    success: false,

                    message:
                        "Patient not found"

                });

            }


            const auditLogs =
                db.prepare(`
                    SELECT *
                    FROM audit_logs
                    WHERE patient_id = ?
                    ORDER BY id DESC
                `).all(
                    patientId
                );


            res.json({

                success: true,

                patient,

                auditLogs

            });

        } catch (error) {

            console.error(
                "❌ Patient audit error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to load patient audit history"

            });

        }

    }
);


/* =========================================================
   UPDATE PATIENT STATUS
========================================================= */

router.put(
    "/:patientId/status",
    (req, res) => {

        const patientId =
            req.params.patientId;

        const {
            status,
            updatedBy,
            updatedRole
        } = req.body;


        /* ---------- STATUS VALIDATION ---------- */

        if (
            !ALLOWED_STATUSES.includes(status)
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Invalid patient status",

                allowedStatuses:
                    ALLOWED_STATUSES

            });

        }


        try {

            /* ---------- FIND PATIENT ---------- */

            const patient =
                db.prepare(`
                    SELECT *
                    FROM patients
                    WHERE patient_id = ?
                `).get(
                    patientId
                );


            if (!patient) {

                return res.status(404).json({

                    success: false,

                    message:
                        "Patient not found"

                });

            }


            const previousStatus =
                patient.status;


            /*
             * Don't create unnecessary history
             * if status is already the same.
             */

            if (
                previousStatus === status
            ) {

                return res.json({

                    success: true,

                    message:
                        "Patient is already in this status",

                    patientId,

                    status

                });

            }


            const performedBy =
                updatedBy ||
                "Staff";

            const performedRole =
                updatedRole ||
                "Staff";


            /* =================================================
               TRANSACTION
            ================================================= */

            const updatePatient =
                db.transaction(() => {

                    /* ---------- UPDATE PATIENT ---------- */

                    db.prepare(`
                        UPDATE patients
                        SET status = ?
                        WHERE patient_id = ?
                    `).run(

                        status,

                        patientId

                    );


                    /* ---------- JOURNEY ---------- */

                    db.prepare(`
                        INSERT INTO patient_journey
                        (
                            patient_id,
                            status,
                            updated_by
                        )
                        VALUES
                        (?, ?, ?)
                    `).run(

                        patientId,

                        status,

                        performedBy

                    );


                    /* ---------- AUDIT ---------- */

                    db.prepare(`
                        INSERT INTO audit_logs
                        (
                            action,
                            patient_id,
                            previous_status,
                            new_status,
                            department,
                            performed_by,
                            performed_role
                        )
                        VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                    `).run(

                        `Patient status changed: ${previousStatus} → ${status}`,

                        patientId,

                        previousStatus,

                        status,

                        patient.department,

                        performedBy,

                        performedRole

                    );

                });


            updatePatient();


            console.log(
                "🔄 Patient status:",
                patientId,
                "|",
                previousStatus,
                "→",
                status
            );


            res.json({

                success: true,

                message:
                    "Patient status updated successfully",

                patientId,

                previousStatus,

                newStatus:
                    status

            });

        } catch (error) {

            console.error(
                "❌ Patient status error:",
                error
            );


            res.status(500).json({

                success: false,

                message:
                    "Unable to update patient status"

            });

        }

    }
);


/* =========================================================
   EXPORT ROUTER
========================================================= */

module.exports = router;