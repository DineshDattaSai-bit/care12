const express = require("express");
const path = require("path");
const Database = require("better-sqlite3");

const router = express.Router();

const db = new Database(
    path.join(__dirname, "..", "database", "careq.db")
);

db.pragma("foreign_keys = ON");

/*
==========================================================
CARE Q — BED MANAGEMENT BACKEND

Departments
Beds
Admission
Discharge
Cleaning
Reservation
Maintenance
Occupancy
Waiting patients
Bed statistics
==========================================================
*/


/* ======================================================
   DEPARTMENTS
====================================================== */

const DEPARTMENTS = [
    {
        name: "Emergency",
        code: "E",
        icon: "🚨"
    },
    {
        name: "Cardiology",
        code: "C",
        icon: "❤️"
    },
    {
        name: "General Ward",
        code: "G",
        icon: "🏥"
    },
    {
        name: "Neurology",
        code: "N",
        icon: "🧠"
    },
    {
        name: "Orthopedics",
        code: "O",
        icon: "🦴"
    },
    {
        name: "Pediatrics",
        code: "P",
        icon: "👶"
    },
    {
        name: "Maternity",
        code: "M",
        icon: "🤰"
    }
];


/* ======================================================
   BED STATUSES
====================================================== */

const BED_STATUSES = [
    "Available",
    "Occupied",
    "Cleaning",
    "Reserved",
    "Maintenance"
];


/* ======================================================
   CREATE BED TABLE IF IT DOES NOT EXIST
====================================================== */

function ensureBedTable() {

    db.prepare(`
        CREATE TABLE IF NOT EXISTS beds (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            bed_number TEXT UNIQUE NOT NULL,

            department TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Available',

            patient_id TEXT,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP

        )
    `).run();

}

ensureBedTable();


/* ======================================================
   INITIALIZE DEPARTMENT BEDS
====================================================== */

function initializeBeds() {

    const insert =
        db.prepare(`
            INSERT INTO beds
            (
                bed_number,
                department,
                status
            )
            VALUES
            (
                ?,
                ?,
                'Available'
            )
        `);

    const transaction =
        db.transaction(() => {

            for (const department of DEPARTMENTS) {

                const count =
                    db.prepare(`
                        SELECT COUNT(*) AS count
                        FROM beds
                        WHERE department = ?
                    `)
                    .get(department.name)
                    .count;

                for (
                    let number = count + 1;
                    number <= 50;
                    number++
                ) {

                    const bedNumber =
                        `${department.code}-${String(number).padStart(3, "0")}`;

                    const existing =
                        db.prepare(`
                            SELECT id
                            FROM beds
                            WHERE bed_number = ?
                        `)
                        .get(bedNumber);

                    if (!existing) {

                        insert.run(
                            bedNumber,
                            department.name
                        );

                    }

                }

            }

        });

    transaction();

}

initializeBeds();


/* ======================================================
   HELPER — FIND DEPARTMENT
====================================================== */

function getDepartment(departmentName) {

    return DEPARTMENTS.find(
        department =>
            department.name.toLowerCase() ===
            String(departmentName).toLowerCase()
    );

}


/* ======================================================
   GET BED STATISTICS
====================================================== */

router.get(
    "/stats",
    (req, res) => {

        try {

            const totalBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                `)
                .get()
                .count;


            const availableBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                    WHERE status = 'Available'
                `)
                .get()
                .count;


            const occupiedBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                    WHERE status = 'Occupied'
                `)
                .get()
                .count;


            const cleaningBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                    WHERE status = 'Cleaning'
                `)
                .get()
                .count;


            const reservedBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                    WHERE status = 'Reserved'
                `)
                .get()
                .count;


            const maintenanceBeds =
                db.prepare(`
                    SELECT COUNT(*) AS count
                    FROM beds
                    WHERE status = 'Maintenance'
                `)
                .get()
                .count;


            const occupancyRate =
                totalBeds === 0
                    ? 0
                    : Math.round(
                        (
                            occupiedBeds /
                            totalBeds
                        ) * 100
                    );


            res.json({

                success: true,

                totalBeds,

                availableBeds,

                occupiedBeds,

                cleaningBeds,

                reservedBeds,

                maintenanceBeds,

                occupancyRate

            });

        } catch (error) {

            console.error(
                "❌ Bed statistics error:",
                error
            );

            res.status(500).json({

                success: false,

                message:
                    "Unable to load bed statistics"

            });

        }

    }
);


/* ======================================================
   GET DEPARTMENTS
====================================================== */

router.get(
    "/departments",
    (req, res) => {

        try {

            const result =
                DEPARTMENTS.map(
                    department => ({

                        name:
                            department.name,

                        code:
                            department.code,

                        icon:
                            department.icon

                    })
                );

            res.json(result);

        } catch (error) {

            console.error(
                "Department error:",
                error
            );

            res.status(500).json({
                message:
                    "Unable to load departments"
            });

        }

    }
);


/* ======================================================
   GET DEPARTMENT BED DASHBOARD
====================================================== */

router.get(
    "/department/:department",
    (req, res) => {

        try {

            const department =
                decodeURIComponent(
                    req.params.department
                );

            const departmentInfo =
                getDepartment(department);

            if (!departmentInfo) {

                return res.status(404).json({
                    message:
                        "Department not found"
                });

            }

            const beds =
                db.prepare(`
                    SELECT
                        id,
                        bed_number,
                        department,
                        status,
                        patient_id,
                        created_at,
                        updated_at
                    FROM beds
                    WHERE department = ?
                    ORDER BY bed_number ASC
                `)
                .all(
                    departmentInfo.name
                );

            const totalBeds =
                beds.length;

            const availableBeds =
                beds.filter(
                    bed =>
                        bed.status === "Available"
                ).length;

            const filledBeds =
                beds.filter(
                    bed =>
                        bed.status === "Occupied"
                ).length;

            const cleaningBeds =
                beds.filter(
                    bed =>
                        bed.status === "Cleaning"
                ).length;

            const reservedBeds =
                beds.filter(
                    bed =>
                        bed.status === "Reserved"
                ).length;

            const maintenanceBeds =
                beds.filter(
                    bed =>
                        bed.status === "Maintenance"
                ).length;

            let waitingPatients = 0;

            try {

                const result =
                    db.prepare(`
                        SELECT COUNT(*) AS count
                        FROM patients
                        WHERE status = 'Waiting'
                        AND department = ?
                    `)
                    .get(
                        departmentInfo.name
                    );

                waitingPatients =
                    result.count || 0;

            } catch (error) {

                waitingPatients = 0;

            }

            const occupancyRate =
                totalBeds === 0
                    ? 0
                    : Math.round(
                        (
                            filledBeds /
                            totalBeds
                        ) * 100
                    );

            let availabilityMessage =
                `${availableBeds} beds available`;

            if (totalBeds === 0) {

                availabilityMessage =
                    "NO BEDS ASSIGNED TO THIS DEPARTMENT";

            } else if (
                filledBeds >= totalBeds
            ) {

                availabilityMessage =
                    `ALL ${totalBeds} BEDS ARE FILLED`;

            } else if (
                availableBeds === 0
            ) {

                availabilityMessage =
                    "NO BEDS ARE CURRENTLY AVAILABLE";

            } else if (
                availableBeds <= 5
            ) {

                availabilityMessage =
                    `LOW CAPACITY — ONLY ${availableBeds} BEDS AVAILABLE`;

            }

            res.json({

                department:
                    departmentInfo.name,

                code:
                    departmentInfo.code,

                icon:
                    departmentInfo.icon,

                totalBeds,

                assignedBeds:
                    totalBeds,

                availableBeds,

                emptyBeds:
                    availableBeds,

                filledBeds,

                waitingPatients,

                cleaningBeds,

                reservedBeds,

                maintenanceBeds,

                occupancyRate,

                availabilityMessage,

                beds

            });

        } catch (error) {

            console.error(
                "Department bed error:",
                error
            );

            res.status(500).json({
                message:
                    "Unable to load department bed information"
            });

        }

    }
);


/* ======================================================
   GET ALL BEDS
====================================================== */

router.get(
    "/",
    (req, res) => {

        try {

            const beds =
                db.prepare(`
                    SELECT *
                    FROM beds
                    ORDER BY department, bed_number
                `)
                .all();

            res.json(beds);

        } catch (error) {

            console.error(
                "Get beds error:",
                error
            );

            res.status(500).json({
                message:
                    "Unable to load beds"
            });

        }

    }
);


/* ======================================================
   GET SINGLE BED
====================================================== */

router.get(
    "/:bedId",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            res.json(bed);

        } catch (error) {

            console.error(
                "Single bed error:",
                error
            );

            res.status(500).json({
                message:
                    "Unable to load bed"
            });

        }

    }
);


/* ======================================================
   UPDATE BED HELPER
====================================================== */

function changeStatus(
    bedId,
    newStatus,
    patientId = null
) {

    const bed =
        db.prepare(`
            SELECT *
            FROM beds
            WHERE id = ?
        `)
        .get(bedId);

    if (!bed) {

        throw new Error(
            "Bed not found"
        );

    }

    if (
        !BED_STATUSES.includes(
            newStatus
        )
    ) {

        throw new Error(
            "Invalid bed status"
        );

    }

    db.prepare(`
        UPDATE beds

        SET
            status = ?,
            patient_id = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
    `)
    .run(
        newStatus,
        patientId,
        bedId
    );

    return db.prepare(`
        SELECT *
        FROM beds
        WHERE id = ?
    `)
    .get(bedId);

}


/* ======================================================
   ADMIT PATIENT
====================================================== */

router.put(
    "/:bedId/admit",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const patientId =
                req.body.patientId;

            if (!patientId) {

                return res.status(400).json({
                    message:
                        "Patient ID is required"
                });

            }

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Available" &&
                bed.status !== "Reserved"
            ) {

                return res.status(400).json({
                    message:
                        `Bed ${bed.bed_number} is not available for admission`
                });

            }

            const existingPatientBed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE patient_id = ?
                    AND status = 'Occupied'
                `)
                .get(
                    String(patientId)
                );

            if (existingPatientBed) {

                return res.status(400).json({
                    message:
                        `Patient is already admitted in bed ${existingPatientBed.bed_number}`
                });

            }

            const transaction =
                db.transaction(() => {

                    const updatedBed =
                        changeStatus(
                            bedId,
                            "Occupied",
                            String(patientId)
                        );

                    try {

                        db.prepare(`
                            UPDATE patients
                            SET status = ?
                            WHERE id = ?
                        `)
                        .run(
                            "Treatment / Observation",
                            patientId
                        );

                    } catch (error) {

                        console.log(
                            "Patient status update skipped:",
                            error.message
                        );

                    }

                    try {

                        db.prepare(`
                            INSERT INTO patient_journey
                            (
                                patient_id,
                                status
                            )
                            VALUES
                            (?, ?)
                        `)
                        .run(
                            patientId,
                            "Treatment / Observation"
                        );

                    } catch (error) {

                        console.log(
                            "Journey update skipped:",
                            error.message
                        );

                    }

                    try {

                        db.prepare(`
                            INSERT INTO audit_logs
                            (
                                action,
                                patient_id,
                                new_status,
                                performed_by,
                                performed_role
                            )
                            VALUES
                            (?, ?, ?, ?, ?)
                        `)
                        .run(
                            "BED_ADMISSION",
                            patientId,
                            "Treatment / Observation",
                            "Bed Management",
                            "Administrator"
                        );

                    } catch (error) {

                        console.log(
                            "Audit update skipped:",
                            error.message
                        );

                    }

                    return updatedBed;

                });

            const updatedBed =
                transaction();

            res.json({

                message:
                    `Patient ${patientId} admitted to ${updatedBed.bed_number}`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Admission error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to admit patient"
            });

        }

    }
);


/* ======================================================
   DISCHARGE
====================================================== */

router.put(
    "/:bedId/discharge",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Occupied"
            ) {

                return res.status(400).json({
                    message:
                        "Only occupied beds can be discharged"
                });

            }

            const patientId =
                bed.patient_id;

            const transaction =
                db.transaction(() => {

                    const updatedBed =
                        changeStatus(
                            bedId,
                            "Cleaning",
                            null
                        );

                    if (patientId) {

                        try {

                            db.prepare(`
                                UPDATE patients
                                SET status = ?
                                WHERE id = ?
                            `)
                            .run(
                                "Discharge",
                                patientId
                            );

                        } catch (error) {

                            console.log(
                                "Patient discharge update skipped:",
                                error.message
                            );

                        }

                        try {

                            db.prepare(`
                                INSERT INTO patient_journey
                                (
                                    patient_id,
                                    status
                                )
                                VALUES
                                (?, ?)
                            `)
                            .run(
                                patientId,
                                "Discharge"
                            );

                        } catch (error) {

                            console.log(
                                "Journey discharge skipped:",
                                error.message
                            );

                        }

                    }

                    try {

                        db.prepare(`
                            INSERT INTO audit_logs
                            (
                                action,
                                patient_id,
                                new_status,
                                performed_by,
                                performed_role
                            )
                            VALUES
                            (?, ?, ?, ?, ?)
                        `)
                        .run(
                            "BED_DISCHARGE",
                            patientId,
                            "Discharge",
                            "Bed Management",
                            "Administrator"
                        );

                    } catch (error) {

                        console.log(
                            "Audit discharge skipped:",
                            error.message
                        );

                    }

                    return updatedBed;

                });

            const updatedBed =
                transaction();

            res.json({

                message:
                    `Bed ${updatedBed.bed_number} moved to Cleaning`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Discharge error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to discharge bed"
            });

        }

    }
);


/* ======================================================
   CLEANING → AVAILABLE
====================================================== */

router.put(
    "/:bedId/clean",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Cleaning"
            ) {

                return res.status(400).json({
                    message:
                        "Only cleaning beds can be marked available"
                });

            }

            const updatedBed =
                changeStatus(
                    bedId,
                    "Available",
                    null
                );

            res.json({

                message:
                    `Bed ${updatedBed.bed_number} is now Available`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Cleaning error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to complete cleaning"
            });

        }

    }
);


/* ======================================================
   RESERVE
====================================================== */

router.put(
    "/:bedId/reserve",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Available"
            ) {

                return res.status(400).json({
                    message:
                        "Only available beds can be reserved"
                });

            }

            const updatedBed =
                changeStatus(
                    bedId,
                    "Reserved",
                    null
                );

            res.json({

                message:
                    `Bed ${updatedBed.bed_number} reserved`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Reserve error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to reserve bed"
            });

        }

    }
);


/* ======================================================
   RELEASE RESERVED BED
====================================================== */

router.put(
    "/:bedId/release",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Reserved"
            ) {

                return res.status(400).json({
                    message:
                        "Only reserved beds can be released"
                });

            }

            const updatedBed =
                changeStatus(
                    bedId,
                    "Available",
                    null
                );

            res.json({

                message:
                    `Bed ${updatedBed.bed_number} released and available`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Release error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to release bed"
            });

        }

    }
);


/* ======================================================
   MAINTENANCE
====================================================== */

router.put(
    "/:bedId/maintenance",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Available"
            ) {

                return res.status(400).json({
                    message:
                        "Only available beds can be sent to maintenance"
                });

            }

            const updatedBed =
                changeStatus(
                    bedId,
                    "Maintenance",
                    null
                );

            res.json({

                message:
                    `Bed ${updatedBed.bed_number} moved to Maintenance`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Maintenance error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to move bed to maintenance"
            });

        }

    }
);


/* ======================================================
   COMPLETE MAINTENANCE
====================================================== */

router.put(
    "/:bedId/maintenance/complete",
    (req, res) => {

        try {

            const bedId =
                Number(
                    req.params.bedId
                );

            const bed =
                db.prepare(`
                    SELECT *
                    FROM beds
                    WHERE id = ?
                `)
                .get(bedId);

            if (!bed) {

                return res.status(404).json({
                    message:
                        "Bed not found"
                });

            }

            if (
                bed.status !== "Maintenance"
            ) {

                return res.status(400).json({
                    message:
                        "Bed is not in maintenance"
                });

            }

            const updatedBed =
                changeStatus(
                    bedId,
                    "Available",
                    null
                );

            res.json({

                message:
                    `Maintenance completed. ${updatedBed.bed_number} is Available`,

                bed:
                    updatedBed

            });

        } catch (error) {

            console.error(
                "Maintenance completion error:",
                error
            );

            res.status(500).json({
                message:
                    error.message ||
                    "Unable to complete maintenance"
            });

        }

    }
);


/* ======================================================
   EXPORT
====================================================== */

module.exports = router;