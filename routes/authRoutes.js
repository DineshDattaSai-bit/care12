const express = require("express");
const Database = require("better-sqlite3");
const path = require("path");
const crypto = require("crypto");
const bcrypt = require("bcrypt");

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

console.log("🔐 CareQ Authentication System Connected");

/* =========================================================
   ALLOWED ROLES
========================================================= */

const ALLOWED_ROLES = [
    "patient",
    "doctor",
    "nurse",
    "registration_staff",
    "department_user",
    "bed_manager",
    "operations_team",
    "administrator"
];

/* =========================================================
   BCRYPT CONFIGURATION
========================================================= */

const BCRYPT_ROUNDS = 12;

/* =========================================================
   CHECK WHETHER PASSWORD IS BCRYPT HASH
========================================================= */

function isBcryptHash(password) {

    if (!password || typeof password !== "string") {
        return false;
    }

    /*
       bcrypt hashes normally look like:

       $2b$12$.......................................................

       We support:
       $2a$
       $2b$
       $2y$
    */

    return /^\$2[aby]\$\d{2}\$/.test(password);
}

/* =========================================================
   PASSWORD HASHING
========================================================= */

async function hashPassword(password) {

    return await bcrypt.hash(
        password,
        BCRYPT_ROUNDS
    );
}

/* =========================================================
   BCRYPT PASSWORD VERIFICATION
========================================================= */

async function verifyPassword(
    password,
    storedPassword
) {

    try {

        return await bcrypt.compare(
            password,
            storedPassword
        );

    } catch (error) {

        console.error(
            "Password verification error:",
            error
        );

        return false;
    }
}

/* =========================================================
   SESSION STORAGE
========================================================= */

const activeSessions = new Map();

/* =========================================================
   ROLE NORMALIZATION
========================================================= */

function normalizeRole(role) {

    if (!role) {
        return null;
    }

    return role
        .toString()
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_");
}

/* =========================================================
   CREATE SESSION
========================================================= */

function createSession(user) {

    const token =
        crypto.randomBytes(32).toString("hex");

    activeSessions.set(
        token,
        {
            userId: user.id,
            username: user.username,
            role: user.role,
            createdAt: Date.now()
        }
    );

    return token;
}

/* =========================================================
   REGISTER
========================================================= */

router.post(
    "/register",
    async (req, res) => {

        const {
            name,
            username,
            password,
            role
        } = req.body;

        /* ---------- VALIDATION ---------- */

        if (
            !name ||
            !username ||
            !password ||
            !role
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Please fill all fields"

            });
        }

        if (
            typeof password !== "string" ||
            password.length < 6
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Password must contain at least 6 characters"

            });
        }

        const cleanName =
            name.trim();

        const cleanUsername =
            username
                .trim()
                .toLowerCase();

        const cleanRole =
            normalizeRole(role);

        /* ---------- ROLE CHECK ---------- */

        if (
            !ALLOWED_ROLES.includes(
                cleanRole
            )
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Invalid CareQ role"

            });
        }

        try {

            /* ---------- CHECK USER ---------- */

            const existingUser =
                db.prepare(`
                    SELECT id
                    FROM users
                    WHERE LOWER(username) = ?
                `).get(
                    cleanUsername
                );

            if (existingUser) {

                return res.status(409).json({

                    success: false,

                    message:
                        "Username already exists"

                });
            }

            /* ---------- HASH PASSWORD ---------- */

            const hashedPassword =
                await hashPassword(password);

            /* ---------- CREATE USER ---------- */

            const result =
                db.prepare(`
                    INSERT INTO users
                    (
                        name,
                        username,
                        password,
                        role
                    )
                    VALUES
                    (?, ?, ?, ?)
                `).run(
                    cleanName,
                    cleanUsername,
                    hashedPassword,
                    cleanRole
                );

            console.log(
                "✅ New user registered:",
                cleanUsername,
                "| Role:",
                cleanRole
            );

            return res.status(201).json({

                success: true,

                message:
                    "Registration successful",

                user: {

                    id:
                        result.lastInsertRowid,

                    name:
                        cleanName,

                    username:
                        cleanUsername,

                    role:
                        cleanRole

                }

            });

        } catch (error) {

            console.error(
                "❌ Registration error:",
                error
            );

            return res.status(500).json({

                success: false,

                message:
                    "Registration failed"

            });
        }
    }
);

/* =========================================================
   LOGIN
========================================================= */

router.post(
    "/login",
    async (req, res) => {

        const {
            username,
            password
        } = req.body;

        /* ---------- VALIDATION ---------- */

        if (
            !username ||
            !password
        ) {

            return res.status(400).json({

                success: false,

                message:
                    "Please enter username and password"

            });
        }

        const cleanUsername =
            username
                .trim()
                .toLowerCase();

        try {

            /* ---------- FIND USER ---------- */

            const user =
                db.prepare(`
                    SELECT
                        id,
                        name,
                        username,
                        password,
                        role
                    FROM users
                    WHERE LOWER(username) = ?
                `).get(
                    cleanUsername
                );

            if (!user) {

                return res.status(401).json({

                    success: false,

                    message:
                        "Invalid username or password"

                });
            }

            /* =================================================
               PASSWORD VERIFICATION

               NEW USERS:
               bcrypt hash -> bcrypt.compare()

               OLD USERS:
               plain text -> compare once -> upgrade to bcrypt
            ================================================= */

            let passwordValid = false;
            let passwordUpgraded = false;

            /* ---------- BCRYPT PASSWORD ---------- */

            if (
                isBcryptHash(
                    user.password
                )
            ) {

                passwordValid =
                    await verifyPassword(
                        password,
                        user.password
                    );

            }

            /* ---------- OLD PLAIN-TEXT PASSWORD ---------- */

            else {

                /*
                   This block exists only to migrate
                   old CareQ accounts.

                   The plain password is NEVER returned
                   to the frontend.
                */

                passwordValid =
                    password === user.password;

                if (passwordValid) {

                    const newHashedPassword =
                        await hashPassword(
                            password
                        );

                    db.prepare(`
                        UPDATE users
                        SET password = ?
                        WHERE id = ?
                    `).run(
                        newHashedPassword,
                        user.id
                    );

                    passwordUpgraded = true;

                    console.log(
                        "🔒 Password upgraded to bcrypt:",
                        user.username
                    );
                }
            }

            /* ---------- INVALID PASSWORD ---------- */

            if (!passwordValid) {

                return res.status(401).json({

                    success: false,

                    message:
                        "Invalid username or password"

                });
            }

            /* ---------- ROLE ---------- */

            const normalizedRole =
                normalizeRole(
                    user.role
                );

            if (
                !ALLOWED_ROLES.includes(
                    normalizedRole
                )
            ) {

                return res.status(403).json({

                    success: false,

                    message:
                        "User role is not supported by CareQ"

                });
            }

            /* =================================================
               SAFE USER OBJECT

               NEVER SEND PASSWORD TO FRONTEND
            ================================================= */

            const cleanUser = {

                id:
                    user.id,

                name:
                    user.name,

                username:
                    user.username,

                role:
                    normalizedRole

            };

            /* ---------- CREATE SESSION ---------- */

            const token =
                createSession(
                    cleanUser
                );

            console.log(
                "✅ User logged in:",
                user.username,
                "| Role:",
                normalizedRole
            );

            if (passwordUpgraded) {

                console.log(
                    "🔐 Existing plain-text password securely migrated."
                );
            }

            /* ---------- RESPONSE ---------- */

            return res.json({

                success: true,

                message:
                    "Login successful",

                token,

                user:
                    cleanUser

            });

        } catch (error) {

            console.error(
                "❌ Login error:",
                error
            );

            return res.status(500).json({

                success: false,

                message:
                    "Login failed"

            });
        }
    }
);

/* =========================================================
   VERIFY SESSION
========================================================= */

router.get(
    "/verify",
    (req, res) => {

        const authHeader =
            req.headers.authorization;

        if (!authHeader) {

            return res.status(401).json({

                success: false,

                message:
                    "Authentication token required"

            });
        }

        const token =
            authHeader.startsWith("Bearer ")
                ? authHeader.substring(7)
                : authHeader;

        const session =
            activeSessions.get(token);

        if (!session) {

            return res.status(401).json({

                success: false,

                message:
                    "Invalid or expired session"

            });
        }

        return res.json({

            success: true,

            authenticated: true,

            session

        });
    }
);

/* =========================================================
   LOGOUT
========================================================= */

router.post(
    "/logout",
    (req, res) => {

        const authHeader =
            req.headers.authorization;

        if (authHeader) {

            const token =
                authHeader.startsWith("Bearer ")
                    ? authHeader.substring(7)
                    : authHeader;

            activeSessions.delete(
                token
            );
        }

        return res.json({

            success: true,

            message:
                "Logged out successfully"

        });
    }
);

/* =========================================================
   AVAILABLE ROLES
========================================================= */

router.get(
    "/roles",
    (req, res) => {

        return res.json({

            success: true,

            roles:
                ALLOWED_ROLES

        });
    }
);

/* =========================================================
   EXPORT
========================================================= */

module.exports = router;