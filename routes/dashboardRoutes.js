const express = require("express");
const Database = require("better-sqlite3");

const router = express.Router();

const db = new Database("database/careq.db");


// ===============================
// DASHBOARD DATA
// ===============================

router.get("/", (req, res) => {

    try {

        // ===============================
        // TOTAL PATIENTS
        // ===============================

        const totalPatients = db.prepare(`
            SELECT COUNT(*) AS total
            FROM patients
        `).get().total;


        // ===============================
        // WAITING PATIENTS
        // ===============================

        const waitingPatients = db.prepare(`
            SELECT COUNT(*) AS total
            FROM patients
            WHERE status = 'Waiting'
        `).get().total;


        // ===============================
        // AVAILABLE BEDS
        // ===============================

        const availableBeds = db.prepare(`
            SELECT COUNT(*) AS total
            FROM beds
            WHERE status = 'Available'
        `).get().total;


        // ===============================
        // DELAYED PATIENTS
        // Waiting for 30 minutes or more
        // ===============================

        const delayedPatients = db.prepare(`
            SELECT COUNT(*) AS total
            FROM patients
            WHERE status = 'Waiting'
            AND created_at <= datetime('now', '-30 minutes')
        `).get().total;


        // ===============================
        // PATIENT JOURNEY COUNTS
        // ===============================

        const journeyData = db.prepare(`
            SELECT
                status,
                COUNT(*) AS total
            FROM patients
            GROUP BY status
        `).all();


        // Default journey values

        let registered = 0;
        let waiting = 0;
        let consultation = 0;
        let diagnostics = 0;
        let treatment = 0;
        let discharge = 0;


        // Put database values into journey counters

        journeyData.forEach((item) => {

            if (item.status === "Registered") {
                registered = item.total;
            }

            if (item.status === "Waiting") {
                waiting = item.total;
            }

            if (item.status === "Consultation") {
                consultation = item.total;
            }

            if (item.status === "Diagnostics") {
                diagnostics = item.total;
            }

            if (
                item.status === "Treatment" ||
                item.status === "Treatment / Observation"
            ) {
                treatment += item.total;
            }

            if (item.status === "Discharge") {
                discharge = item.total;
            }

        });


        // ===============================
        // DEPARTMENT WAITING COUNTS
        // ===============================

        const departments = db.prepare(`
            SELECT
                department,
                COUNT(*) AS waiting
            FROM patients
            WHERE status = 'Waiting'
            GROUP BY department
        `).all();


        // ===============================
        // SEND DASHBOARD DATA
        // ===============================

        res.json({

            success: true,

            statistics: {

                totalPatients: totalPatients,

                waitingPatients: waitingPatients,

                availableBeds: availableBeds,

                delayedPatients: delayedPatients

            },

            journey: {

                registered: registered,

                waiting: waiting,

                consultation: consultation,

                diagnostics: diagnostics,

                treatment: treatment,

                discharge: discharge

            },

            departments: departments

        });

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

        res.status(500).json({

            success: false,

            message:
                "Unable to load dashboard data"

        });

    }

});


module.exports = router;