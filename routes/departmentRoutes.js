const express = require("express");
const Database = require("better-sqlite3");

const router = express.Router();

const db = new Database("database/careq.db");


// ===============================
// GET ALL DEPARTMENTS
// ===============================

router.get("/", (req, res) => {

    try {

        const departments = db.prepare(`
            SELECT
                d.id,
                d.name,
                COUNT(p.id) AS waiting
            FROM departments d
            LEFT JOIN patients p
                ON d.name = p.department
                AND p.status = 'Waiting'
            GROUP BY d.id
            ORDER BY d.name
        `).all();


        res.json({

            success: true,

            departments: departments

        });

    } catch (error) {

        console.error(error);

        res.status(500).json({

            success: false,

            message:
                "Unable to load departments"

        });

    }

});


// ===============================
// ADD DEPARTMENT
// ===============================

router.post("/", (req, res) => {

    const {
        name
    } = req.body;


    if (!name || !name.trim()) {

        return res.json({

            success: false,

            message:
                "Department name is required"

        });

    }


    try {

        db.prepare(`
            INSERT INTO departments
            (name)
            VALUES (?)
        `).run(
            name.trim()
        );


        res.json({

            success: true,

            message:
                "Department added successfully"

        });

    } catch (error) {

        console.error(error);

        res.json({

            success: false,

            message:
                "Department already exists"

        });

    }

});


// ===============================
// DELETE DEPARTMENT
// ===============================

router.delete("/:id", (req, res) => {

    const id =
        req.params.id;


    try {

        const department =
            db.prepare(`
                SELECT name
                FROM departments
                WHERE id = ?
            `).get(id);


        if (!department) {

            return res.json({

                success: false,

                message:
                    "Department not found"

            });

        }


        // Don't delete if patients
        // are using this department

        const patients =
            db.prepare(`
                SELECT COUNT(*) AS total
                FROM patients
                WHERE department = ?
            `).get(
                department.name
            ).total;


        if (patients > 0) {

            return res.json({

                success: false,

                message:
                    "Cannot delete department because patients are assigned to it"

            });

        }


        db.prepare(`
            DELETE FROM departments
            WHERE id = ?
        `).run(id);


        res.json({

            success: true,

            message:
                "Department deleted successfully"

        });

    } catch (error) {

        console.error(error);

        res.status(500).json({

            success: false,

            message:
                "Unable to delete department"

        });

    }

});


module.exports = router;