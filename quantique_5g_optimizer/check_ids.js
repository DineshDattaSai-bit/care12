const fs = require('fs');
const html = fs.readFileSync('templates/index.html', 'utf8');
const js = fs.readFileSync('static/js/app.js', 'utf8');

const regex = /getElementById\(['"]([^'"]+)['"]\)/g;
let match;
const ids = new Set();
while ((match = regex.exec(js)) !== null) {
    ids.add(match[1]);
}

console.log('Total IDs found in JS:', ids.size);
for (const id of ids) {
    const hasDouble = html.includes('id="' + id + '"');
    const hasSingle = html.includes("id='" + id + "'");
    if (!hasDouble && !hasSingle) {
        console.log('CRITICAL: Element ID in JS is MISSING from HTML:', id);
    }
}
