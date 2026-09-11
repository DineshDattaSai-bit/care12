const http = require('http');

const endpoints = [
    '/',
    '/login',
    '/dashboard',
    '/patients',
    '/queue',
    '/beds',
    '/departments',
    '/audit',
    '/reports',
    '/api/health',
    '/api/dashboard',
    '/api/patients',
    '/api/beds/stats',
    '/api/documents/patient/CQ0001',
    '/api/documents/recent'
];

async function checkEndpoint(path) {
    return new Promise((resolve) => {
        http.get(`http://localhost:3000${path}`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                console.log(`[${res.statusCode}] GET ${path} (${data.length} bytes)`);
                resolve(res.statusCode >= 200 && res.statusCode < 400);
            });
        }).on('error', (err) => {
            console.log(`[ERR] GET ${path}: ${err.message}`);
            resolve(false);
        });
    });
}

async function runAll() {
    console.log('=== VERIFYING CAREQ SERVER ROUTES ===');
    let allPassed = true;
    for (const ep of endpoints) {
        const ok = await checkEndpoint(ep);
        if (!ok) allPassed = false;
    }
    console.log('====================================');
    console.log(allPassed ? '✅ ALL 15 ENDPOINTS PASSED SUCCESSFULLY!' : '❌ SOME ENDPOINTS FAILED');
}

runAll();
