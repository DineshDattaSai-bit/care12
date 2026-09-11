const express = require("express");
const path = require("path");
const Database = require("better-sqlite3");

const app = express();
const PORT = 3000;

// ===============================
// DATABASE
// ===============================
const dbPath = path.join(__dirname, "database", "careq.db");
const db = new Database(dbPath);

db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

// ===============================
// MIDDLEWARE
// ===============================
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static assets from public folder
app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static(path.join(__dirname, "public", "uploads")));

// ===============================
// API ROUTES
// ===============================
const authRoutes = require("./routes/authRoutes");
const patientRoutes = require("./routes/patientRoutes");
const dashboardRoutes = require("./routes/dashboardRoutes");
const bedRoutes = require("./routes/bedRoutes");
const departmentRoutes = require("./routes/departmentRoutes");
const auditRoutes = require("./routes/auditRoutes");
const documentRoutes = require("./routes/documentRoutes");

app.use("/api/auth", authRoutes);
app.use("/api/patients", patientRoutes);
app.use("/api/dashboard", dashboardRoutes);
app.use("/api/beds", bedRoutes);
app.use("/api/departments", departmentRoutes);
app.use("/api/audit", auditRoutes);
app.use("/api/documents", documentRoutes);

// ===============================
// PAGE ROUTES & CLEAN NAVIGATION
// ===============================

// Landing Page
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Authentication
app.get(["/login", "/login.html", "/pages/login.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "login.html"));
});

// Live Operations Dashboard
app.get(["/dashboard", "/dashboard.html", "/pages/dashboard.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "dashboard.html"));
});

// Patient Directory & Registration
app.get(["/patients", "/patient", "/patient.html", "/pages/patient.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "patient.html"));
});

// Live Queue Management
app.get(["/queue", "/queue.html", "/pages/queue.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "queue.html"));
});

// Beds Command Center
app.get(["/beds", "/beds.html", "/pages/beds.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "beds.html"));
});

// Department Operations
app.get(["/departments", "/departments.html", "/pages/departments.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "departments.html"));
});

// Audit History & Patient Journey
app.get(["/audit", "/audit.html", "/pages/audit.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "audit.html"));
});

// Clinical Reports & Document Management
app.get(["/reports", "/reports.html", "/pages/reports.html"], (req, res) => {
    res.sendFile(path.join(__dirname, "public", "pages", "reports.html"));
});

// ===============================
// HEALTH CHECK
// ===============================
app.get("/api/health", (req, res) => {
    res.json({
        success: true,
        message: "CareQ Smart Hospital Platform is online",
        timestamp: new Date().toISOString()
    });
});

// ===============================
// DATABASE TEST
// ===============================
app.get("/api/test", (req, res) => {
    try {
        const result = db.prepare("SELECT 1 AS test").get();
        res.json({
            success: true,
            database: "connected",
            result
        });
    } catch (error) {
        console.error("Database test error:", error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// ===============================
// API 404
// ===============================
app.use("/api", (req, res) => {
    res.status(404).json({
        success: false,
        error: "API endpoint not found",
        method: req.method,
        path: req.originalUrl
    });
});

// ===============================
// GLOBAL ERROR HANDLER
// ===============================
app.use((err, req, res, next) => {
    console.error("SERVER ERROR:", err);
    res.status(500).json({
        success: false,
        error: err.message || "Internal server error"
    });
});

// ===============================
// START SERVER
// ===============================
app.listen(PORT, () => {
    console.log("====================================================");
    console.log("           CAREQ SMART HOSPITAL PLATFORM            ");
    console.log("====================================================");
    console.log(`🌐 Landing Page:    http://localhost:${PORT}/`);
    console.log(`🔐 Login:           http://localhost:${PORT}/login`);
    console.log(`📊 Dashboard:       http://localhost:${PORT}/dashboard`);
    console.log(`👤 Patients:        http://localhost:${PORT}/patients`);
    console.log(`📋 Queue:           http://localhost:${PORT}/queue`);
    console.log(`🛏️ Beds:            http://localhost:${PORT}/beds`);
    console.log(`🏢 Departments:     http://localhost:${PORT}/departments`);
    console.log(`📜 Audit History:   http://localhost:${PORT}/audit`);
    console.log(`📑 Medical Reports: http://localhost:${PORT}/reports`);
    console.log("====================================================");
});