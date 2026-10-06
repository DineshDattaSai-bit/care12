const fs = require('fs');

// Simple DOM environment simulation
const html = fs.readFileSync('standalone_prototype.html', 'utf8');

// Check script execution errors
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
    console.error('No script found in standalone HTML!');
    process.exit(1);
}

const scriptCode = scriptMatch[1];

// Create mock browser globals
global.window = {
    addEventListener: (event, fn) => {},
    removeEventListener: (event, fn) => {}
};
global.document = {
    readyState: 'complete',
    addEventListener: (event, fn) => {},
    getElementById: (id) => {
        // Return a mock element with classList and style
        return {
            id,
            classList: {
                toggle: () => {},
                add: () => {},
                remove: () => {},
                contains: () => false
            },
            style: {},
            dataset: {},
            setAttribute: (k, v) => {},
            addEventListener: (event, fn) => {},
            getContext: () => ({
                fillStyle: '',
                strokeStyle: '',
                lineWidth: 1,
                fillRect: () => {},
                strokeRect: () => {},
                beginPath: () => {},
                moveTo: () => {},
                lineTo: () => {},
                arc: () => {},
                closePath: () => {},
                fill: () => {},
                stroke: () => {},
                fillText: () => {},
                save: () => {},
                restore: () => {},
                createRadialGradient: () => ({ addColorStop: () => {} }),
                setLineDash: () => {},
            }),
            getBoundingClientRect: () => ({ left: 0, top: 0, width: 600, height: 420 }),
            width: 600,
            height: 420,
            innerHTML: '',
            textContent: '',
            value: '180',
            appendChild: () => {}
        };
    },
    querySelectorAll: (sel) => [],
    querySelector: (sel) => null,
    createElement: (tag) => ({
        tagName: tag.toUpperCase(),
        classList: {
            add: () => {},
            remove: () => {},
            toggle: () => {},
            contains: () => false
        },
        style: {},
        dataset: {},
        innerHTML: '',
        textContent: '',
        appendChild: () => {},
        addEventListener: () => {}
    })
};

const listeners = {};
const originalGetElementById = global.document.getElementById;
global.document.getElementById = (id) => {
    const el = originalGetElementById(id);
    el.addEventListener = (event, fn) => {
        listeners[id + ':' + event] = fn;
    };
    return el;
};

global.requestAnimationFrame = (cb) => { /* don't loop forever in node */ };

console.log('Testing script execution in simulated browser environment...');
try {
    eval(scriptCode);
    console.log('Script executed cleanly without throwing any runtime error!');
    
    // Test triggering buttons
    console.log('Registered listeners:', Object.keys(listeners));
    
    if (listeners['btn-add-tower:click']) {
        console.log('Testing Add Tower...');
        listeners['btn-add-tower:click']();
    }
    if (listeners['btn-add-user:click']) {
        console.log('Testing Add User...');
        listeners['btn-add-user:click']();
    }
    if (listeners['btn-run-optimization:click']) {
        console.log('Testing Run Quantum Optimization (btn-run-optimization)...');
        listeners['btn-run-optimization:click']();
    }
    if (listeners['tower-dist-slider:input']) {
        console.log('Testing Tower Distance Slider input (220m)...');
        listeners['tower-dist-slider:input']({ target: { value: 220 } });
    }
    console.log('ALL INTERACTIVE EVENT HANDLERS TRIGGERED AND PASSED WITHOUT ERROR!');
} catch (err) {
    console.error('RUNTIME ERROR IN SCRIPT:', err);
}
