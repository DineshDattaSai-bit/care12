import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace drawNetworkSimulation tower and user drawing + add inter-tower dimension lines
old_tower_and_ue = """    // 4. Draw gNodeB Towers
    t.bs_telemetry.forEach(bs => {
        ctx.save();
        ctx.beginPath();
        ctx.arc(bs.x, bs.y, 14, 0, Math.PI * 2);
        ctx.fillStyle = '#121828';
        ctx.fill();
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 2.5;
        ctx.stroke();
        
        ctx.fillStyle = '#00f0ff';
        ctx.fillRect(bs.x - 3, bs.y - 6, 6, 12);
        ctx.fillRect(bs.x - 8, bs.y - 7, 16, 3);
        
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText(bs.name, bs.x, bs.y - 18);
        
        const sub = bs.active_config.subband;
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.fillStyle = SUBBAND_PALETTE[sub].border;
        ctx.fillText(`Sub-${sub} (${bs.active_config.power_dbm} dBm)`, bs.x, bs.y + 26);
        ctx.restore();
    });
    
    // 5. Draw User Equipments (UEs) with Profile Distinction (Stationary 📍 vs Mobile 🚗)
    t.user_telemetry.forEach(u => {
        const sbs = t.bs_telemetry[u.serving_bs];
        const dist = sbs ? Math.hypot(u.x - sbs.x, u.y - sbs.y) : u.distance_m;
        const zone = getDistanceZone(dist);
        const isStat = (u.is_stationary !== undefined) ? u.is_stationary : (u.ue_id % 2 !== 0);
        const isNlos = u.is_nlos || false;

        ctx.save();
        
        // If Stationary (Fixed FWA / IoT): Draw Diamond Anchor Base Plate
        if (isStat) {
            ctx.save();
            ctx.translate(u.x, u.y);
            ctx.rotate(Math.PI / 4);
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 1.6;
            ctx.strokeRect(-12, -12, 24, 24);
            ctx.fillStyle = 'rgba(56, 189, 248, 0.12)';
            ctx.fillRect(-12, -12, 24, 24);
            ctx.restore();
        } else {
            // Mobile UE: Draw animated mobility ripple ring
            const waveR = 12 + Math.sin(now * 3 + u.ue_id) * 3;
            ctx.beginPath();
            ctx.arc(u.x, u.y, waveR, 0, Math.PI * 2);
            ctx.strokeStyle = isNlos ? 'rgba(244, 63, 94, 0.4)' : `${zone.color}55`;
            ctx.lineWidth = 1.4;
            ctx.stroke();
        }

        // Core UE Node
        ctx.beginPath();
        ctx.arc(u.x, u.y, isStat ? 6.5 : 7.5, 0, Math.PI * 2);
        
        if (u.is_outage) {
            ctx.fillStyle = '#f43f5e';
            ctx.shadowColor = '#f43f5e';
            ctx.shadowBlur = 12;
        } else if (isNlos) {
            ctx.fillStyle = '#fb7185';
            ctx.shadowColor = '#fb7185';
            ctx.shadowBlur = 10;
        } else {
            ctx.fillStyle = zone.color;
            ctx.shadowColor = zone.color;
            ctx.shadowBlur = 10;
        }
        ctx.fill();
        ctx.shadowBlur = 0;
        
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.6;
        ctx.stroke();
        
        // Subscriber Name + Profile tag
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#cbd5e1';
        ctx.textAlign = 'center';
        ctx.fillText(`${u.name.split(' ')[0]} [${isStat ? '📍' : '🚗'}]`, u.x, u.y - 14);
        
        // Telemetry tag: Power + SINR + Channel
        ctx.font = 'bold 9px JetBrains Mono, monospace';
        if (u.is_outage) {
            ctx.fillStyle = '#fda4af';
            ctx.fillText(`${u.sinr_db}dB (OUT)`, u.x, u.y + 20);
        } else if (isNlos) {
            ctx.fillStyle = '#fb7185';
            ctx.fillText(`🧱${u.sinr_db}dB NLOS`, u.x, u.y + 20);
        } else {
            ctx.fillStyle = zone.color;
            ctx.fillText(`${zone.powerDbm}dBm ${u.sinr_db}dB`, u.x, u.y + 20);
        }
        
        ctx.restore();
    });"""

new_tower_and_ue = """    // 3.5 Inter-Tower Dimension Lines & Distances
    for (let i = 0; i < t.bs_telemetry.length; i++) {
        for (let j = i + 1; j < t.bs_telemetry.length; j++) {
            const b1 = t.bs_telemetry[i];
            const b2 = t.bs_telemetry[j];
            const dM = Math.round(Math.hypot(b1.x - b2.x, b1.y - b2.y));
            
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(b1.x, b1.y);
            ctx.lineTo(b2.x, b2.y);
            ctx.strokeStyle = dM < 200 ? 'rgba(244, 63, 94, 0.45)' : 'rgba(56, 189, 248, 0.25)';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 6]);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Distance pill at midpoint
            const mx = (b1.x + b2.x) / 2;
            const my = (b1.y + b2.y) / 2;
            ctx.font = 'bold 9px JetBrains Mono, monospace';
            ctx.textAlign = 'center';
            if (dM < 200) {
                ctx.fillStyle = '#f43f5e';
                ctx.fillText(`↔ ${dM}m (⚠️ High Interf)`, mx, my - 4);
            } else {
                ctx.fillStyle = '#38bdf8';
                ctx.fillText(`↔ ${dM}m`, mx, my - 4);
            }
            ctx.restore();
        }
    }
    
    // 4. Draw 5G Cell Towers (Recognizable Antenna Mast with tripod lattice legs)
    t.bs_telemetry.forEach(bs => {
        const isSelected = AppState.selectedItem && AppState.selectedItem.type === 'tower' && AppState.selectedItem.data.bs_id === bs.bs_id;
        ctx.save();

        // Selection halo
        if (isSelected) {
            ctx.beginPath();
            ctx.arc(bs.x, bs.y, 24 + Math.sin(now * 4) * 3, 0, Math.PI * 2);
            ctx.strokeStyle = '#00f0ff';
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Tower Lattice Legs (A-frame tripod)
        ctx.beginPath();
        ctx.moveTo(bs.x - 12, bs.y + 18);
        ctx.lineTo(bs.x, bs.y - 4);
        ctx.lineTo(bs.x + 12, bs.y + 18);
        // Cross braces
        ctx.moveTo(bs.x - 8, bs.y + 12);
        ctx.lineTo(bs.x + 8, bs.y + 12);
        ctx.moveTo(bs.x - 5, bs.y + 6);
        ctx.lineTo(bs.x + 5, bs.y + 6);
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 1.6;
        ctx.stroke();

        // Antenna Crossbar Mount
        ctx.beginPath();
        ctx.moveTo(bs.x - 14, bs.y - 4);
        ctx.lineTo(bs.x + 14, bs.y - 4);
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // 3 Sector Antenna Array Elements
        const sub = bs.active_config.subband;
        const subCol = SUBBAND_PALETTE[sub].border;
        for (let off of [-10, 0, 10]) {
            ctx.fillStyle = subCol;
            ctx.fillRect(bs.x + off - 2, bs.y - 12, 4, 10);
        }

        // Apex Beacon (Flashing Red/Cyan Obstruction Light)
        const beaconPulse = 0.5 + 0.5 * Math.sin(now * 6 + bs.bs_id);
        ctx.beginPath();
        ctx.arc(bs.x, bs.y - 15, 3.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(244, 63, 94, ${beaconPulse})`;
        ctx.shadowColor = '#f43f5e';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Tower Name Label
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillStyle = isSelected ? '#00f0ff' : '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText(bs.name || `Tower ${bs.bs_id + 1}`, bs.x, bs.y - 20);

        // Subband & Power Label
        ctx.font = '9.5px JetBrains Mono, monospace';
        ctx.fillStyle = subCol;
        ctx.fillText(`Sub-${sub} (${bs.active_config.power_dbm} dBm)`, bs.x, bs.y + 30);
        ctx.restore();
    });
    
    // 5. Draw User Equipments (UEs) with Profile Distinction (Stationary 📍 vs Mobile 📱)
    t.user_telemetry.forEach(u => {
        const sbs = t.bs_telemetry[u.serving_bs];
        const dist = sbs ? Math.hypot(u.x - sbs.x, u.y - sbs.y) : u.distance_m;
        const zone = getDistanceZone(dist);
        const isStat = (u.is_stationary !== undefined) ? u.is_stationary : (u.ue_id % 2 !== 0);
        const isNlos = u.is_nlos || false;
        const isSelected = AppState.selectedItem && AppState.selectedItem.type === 'user' && AppState.selectedItem.data.ue_id === u.ue_id;

        ctx.save();

        // Selection halo
        if (isSelected) {
            ctx.beginPath();
            ctx.arc(u.x, u.y, 22 + Math.sin(now * 4) * 2, 0, Math.PI * 2);
            ctx.strokeStyle = '#fbbf24';
            ctx.lineWidth = 2;
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // If Stationary (Fixed FWA / IoT): Draw Diamond Anchor Base Plate
        if (isStat) {
            ctx.save();
            ctx.translate(u.x, u.y);
            ctx.rotate(Math.PI / 4);
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 1.6;
            ctx.strokeRect(-12, -12, 24, 24);
            ctx.fillStyle = 'rgba(56, 189, 248, 0.12)';
            ctx.fillRect(-12, -12, 24, 24);
            ctx.restore();

            // Core Sensor Node
            ctx.beginPath();
            ctx.arc(u.x, u.y, 6.5, 0, Math.PI * 2);
            ctx.fillStyle = u.is_outage ? '#f43f5e' : (isNlos ? '#fb7185' : zone.color);
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        } else {
            // Mobile UE: Draw Smartphone Body
            const phoneW = 14, phoneH = 22, phoneR = 3;
            const px = u.x - phoneW / 2;
            const py = u.y - phoneH / 2;

            // Animated mobility wave ripples
            const waveR = 14 + Math.sin(now * 3 + u.ue_id) * 3;
            ctx.beginPath();
            ctx.arc(u.x, u.y, waveR, 0, Math.PI * 2);
            ctx.strokeStyle = isNlos ? 'rgba(244, 63, 94, 0.4)' : `${zone.color}55`;
            ctx.lineWidth = 1.2;
            ctx.stroke();

            // Phone chassis
            ctx.fillStyle = '#0f172a';
            ctx.strokeStyle = isNlos ? '#f43f5e' : (u.is_outage ? '#f43f5e' : zone.color);
            ctx.lineWidth = 1.6;
            
            // Rounded rect
            ctx.beginPath();
            ctx.roundRect(px, py, phoneW, phoneH, phoneR);
            ctx.fill();
            ctx.stroke();

            // Phone screen
            ctx.fillStyle = isNlos ? 'rgba(244, 63, 94, 0.4)' : (u.is_outage ? 'rgba(244, 63, 94, 0.4)' : `${zone.color}44`);
            ctx.fillRect(px + 2, py + 3, phoneW - 4, phoneH - 7);

            // Speaker notch
            ctx.fillStyle = '#cbd5e1';
            ctx.fillRect(u.x - 2, py + 1.2, 4, 1);

            // Home bar
            ctx.fillRect(u.x - 2.5, py + phoneH - 2.5, 5, 1);
        }

        // Subscriber Name + Profile tag
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = isSelected ? '#fbbf24' : '#cbd5e1';
        ctx.textAlign = 'center';
        ctx.fillText(`${u.name.split(' ')[0]} [${isStat ? '📍' : '📱'}]`, u.x, u.y - 16);

        // Telemetry tag: Power + SINR + Channel
        ctx.font = 'bold 9px JetBrains Mono, monospace';
        if (u.is_outage) {
            ctx.fillStyle = '#fda4af';
            ctx.fillText(`${u.sinr_db}dB (OUT)`, u.x, u.y + 20);
        } else if (isNlos) {
            ctx.fillStyle = '#fb7185';
            ctx.fillText(`🧱${u.sinr_db}dB NLOS`, u.x, u.y + 20);
        } else {
            ctx.fillStyle = zone.color;
            ctx.fillText(`${zone.powerDbm}dBm ${u.sinr_db}dB`, u.x, u.y + 20);
        }

        ctx.restore();
    });"""

if old_tower_and_ue in js:
    js = js.replace(old_tower_and_ue, new_tower_and_ue, 1)
    print("Tower and user drawing upgraded.")

# Replace initCanvasEvents
old_init_canvas = """function initCanvasEvents() {
    const canvas = document.getElementById('network-canvas');
    if (!canvas) return;
    
    let isDragging = false;
    let dragTarget = null;
    let startPos = { x: 0, y: 0 };
    let didMove = false;
    
    function getPos(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches && e.touches.length > 0 ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches && e.touches.length > 0 ? e.touches[0].clientY : e.clientY;
        return {
            x: (clientX - rect.left) * (canvas.width / rect.width),
            y: (clientY - rect.top) * (canvas.height / rect.height)
        };
    }
    
    function onPointerDown(e) {
        if (!AppState.networkData) return;
        const pos = getPos(e);
        for (const u of AppState.networkData.user_telemetry) {
            if (Math.hypot(u.x - pos.x, u.y - pos.y) < 24) {
                isDragging = true;
                dragTarget = u;
                startPos = { x: pos.x, y: pos.y };
                didMove = false;
                if (e.cancelable && e.type && e.type.startsWith('touch')) e.preventDefault();
                break;
            }
        }
    }
    
    function onPointerMove(e) {
        if (!isDragging || !dragTarget) return;
        if (e.cancelable && e.type && e.type.startsWith('touch')) e.preventDefault();
        const pos = getPos(e);
        if (Math.hypot(pos.x - startPos.x, pos.y - startPos.y) > 4) {
            didMove = true;
        }
        dragTarget.x = Math.max(30, Math.min(canvas.width - 30, pos.x));
        dragTarget.y = Math.max(30, Math.min(canvas.height - 30, pos.y));
        recalculateClientMobilityTelemetry();
        drawNetworkSimulation();
    }
    
    const stopDrag = async () => {
        if (isDragging && dragTarget) {
            isDragging = false;
            const u = dragTarget;
            dragTarget = null;
            
            // If user simply clicked without dragging: toggle stationary vs mobile profile!
            if (!didMove) {
                u.is_stationary = !u.is_stationary;
                u.mobility_type = u.is_stationary ? 'Fixed FWA' : 'Mobile UE';
                recalculateClientMobilityTelemetry();
                updateNetworkUI();
                drawNetworkSimulation();
                return;
            }
            
            await fetch('/api/network/update_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ue_id: u.ue_id, x: u.x, y: u.y })
            }).catch(() => {});
            await refreshAfterStateChange();
        }
    };
    
    canvas.addEventListener('mousedown', onPointerDown);
    canvas.addEventListener('mousemove', onPointerMove);
    canvas.addEventListener('mouseup', stopDrag);
    canvas.addEventListener('mouseleave', stopDrag);

    // Full Mobile Touch Support (iPhone / Android)
    canvas.addEventListener('touchstart', onPointerDown, { passive: false });
    canvas.addEventListener('touchmove', onPointerMove, { passive: false });
    canvas.addEventListener('touchend', stopDrag, { passive: false });
    canvas.addEventListener('touchcancel', stopDrag, { passive: false });
}"""

new_init_canvas = """function initCanvasEvents() {
    const canvas = document.getElementById('network-canvas');
    if (!canvas) return;
    
    let isDragging = false;
    let dragTarget = null;
    let dragObjectType = null; // 'tower' or 'user'
    let startPos = { x: 0, y: 0 };
    let didMove = false;
    
    function getPos(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches && e.touches.length > 0 ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches && e.touches.length > 0 ? e.touches[0].clientY : e.clientY;
        return {
            x: (clientX - rect.left) * (canvas.width / rect.width),
            y: (clientY - rect.top) * (canvas.height / rect.height)
        };
    }
    
    function onPointerDown(e) {
        if (!AppState.networkData) return;
        const pos = getPos(e);
        
        // 1. Check if clicked near a Base Station Tower first
        for (const bs of AppState.networkData.bs_telemetry) {
            if (Math.hypot(bs.x - pos.x, bs.y - pos.y) < 28) {
                isDragging = true;
                dragTarget = bs;
                dragObjectType = 'tower';
                AppState.draggedObject = bs;
                AppState.dragObjectType = 'tower';
                AppState.selectedItem = { type: 'tower', data: bs };
                startPos = { x: pos.x, y: pos.y };
                didMove = false;
                updateInspectorUI();
                drawNetworkSimulation();
                if (e.cancelable && e.type && e.type.startsWith('touch')) e.preventDefault();
                return;
            }
        }
        
        // 2. Check if clicked near a User Equipment
        for (const u of AppState.networkData.user_telemetry) {
            if (Math.hypot(u.x - pos.x, u.y - pos.y) < 24) {
                isDragging = true;
                dragTarget = u;
                dragObjectType = 'user';
                AppState.draggedObject = u;
                AppState.dragObjectType = 'user';
                AppState.selectedItem = { type: 'user', data: u };
                startPos = { x: pos.x, y: pos.y };
                didMove = false;
                updateInspectorUI();
                drawNetworkSimulation();
                if (e.cancelable && e.type && e.type.startsWith('touch')) e.preventDefault();
                return;
            }
        }
    }
    
    function onPointerMove(e) {
        if (!isDragging || !dragTarget) return;
        if (e.cancelable && e.type && e.type.startsWith('touch')) e.preventDefault();
        const pos = getPos(e);
        if (Math.hypot(pos.x - startPos.x, pos.y - startPos.y) > 4) {
            didMove = true;
        }
        dragTarget.x = Math.max(30, Math.min(canvas.width - 30, pos.x));
        dragTarget.y = Math.max(30, Math.min(canvas.height - 30, pos.y));
        recalculateClientMobilityTelemetry();
        updateInspectorUI();
        drawNetworkSimulation();
    }
    
    const stopDrag = async () => {
        if (isDragging && dragTarget) {
            isDragging = false;
            const target = dragTarget;
            const objType = dragObjectType;
            dragTarget = null;
            dragObjectType = null;
            
            // If user simply clicked a UE without dragging: toggle stationary vs mobile profile!
            if (!didMove && objType === 'user') {
                target.is_stationary = !target.is_stationary;
                target.mobility_type = target.is_stationary ? 'Fixed FWA' : 'Mobile UE';
                recalculateClientMobilityTelemetry();
                updateNetworkUI();
                updateInspectorUI();
                drawNetworkSimulation();
                return;
            }
            
            if (didMove) {
                if (objType === 'tower') {
                    await fetch('/api/network/update_tower', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bs_id: target.bs_id, x: target.x, y: target.y })
                    }).catch(() => {});
                } else if (objType === 'user') {
                    await fetch('/api/network/update_user', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ue_id: target.ue_id, x: target.x, y: target.y })
                    }).catch(() => {});
                }
                await refreshAfterStateChange();
            }
        }
    };
    
    canvas.addEventListener('mousedown', onPointerDown);
    canvas.addEventListener('mousemove', onPointerMove);
    canvas.addEventListener('mouseup', stopDrag);
    canvas.addEventListener('mouseleave', stopDrag);

    // Full Mobile Touch Support (iPhone / Android)
    canvas.addEventListener('touchstart', onPointerDown, { passive: false });
    canvas.addEventListener('touchmove', onPointerMove, { passive: false });
    canvas.addEventListener('touchend', stopDrag, { passive: false });
    canvas.addEventListener('touchcancel', stopDrag, { passive: false });
}"""

if old_init_canvas in js:
    js = js.replace(old_init_canvas, new_init_canvas, 1)
    print("initCanvasEvents updated with tower + user dragging and inspector selection.")

# Add updateInspectorUI, handleAddTower, handleAddUser, and setTowerDistance
extra_functions = """
// ----------------- Dynamic Tower & User Management & Inspector UI -----------------
function updateInspectorUI() {
    const inspectorEl = document.getElementById('inspector-body');
    if (!inspectorEl) return;
    
    if (!AppState.selectedItem || !AppState.networkData) {
        inspectorEl.innerHTML = '<div class="inspector-placeholder"><i class="fa-solid fa-arrow-pointer"></i> Click any Tower or User on the canvas to inspect its real-time channel state and parameters.</div>';
        return;
    }
    
    const sel = AppState.selectedItem;
    if (sel.type === 'tower') {
        const bs = sel.data;
        const t = AppState.networkData;
        const sub = bs.active_config.subband;
        const subInfo = SUBBAND_PALETTE[sub];
        const connectedUsers = t.user_telemetry.filter(u => u.serving_bs === bs.bs_id);
        
        let nearestDist = 9999;
        t.bs_telemetry.forEach(other => {
            if (other.bs_id !== bs.bs_id) {
                const d = Math.round(Math.hypot(bs.x - other.x, bs.y - other.y));
                if (d < nearestDist) nearestDist = d;
            }
        });
        if (nearestDist === 9999) nearestDist = 360;
        
        inspectorEl.innerHTML = `
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Identifer:</span>
                <span class="inspector-prop-val text-cyan">📡 ${bs.name}</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Carrier Band:</span>
                <span class="inspector-prop-val">28.00 GHz mmWave FR2</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Active Subband:</span>
                <span class="inspector-prop-val" style="color:${subInfo.border};">Sub-${sub} (${subInfo.label.split(' ')[0]})</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Beam Direction:</span>
                <span class="inspector-prop-val">${bs.active_config.angle >= 0 ? '+' : ''}${bs.active_config.angle}° Azimuth</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Sector Tx Power:</span>
                <span class="inspector-prop-val">${bs.active_config.power_dbm} dBm (${Math.round(Math.pow(10, bs.active_config.power_dbm/10)/100)/10} W)</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Connected UEs:</span>
                <span class="inspector-prop-val">${connectedUsers.length} Subscribers</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Nearest Tower Dist:</span>
                <span class="inspector-prop-val ${nearestDist < 200 ? 'text-red' : 'text-green'}">${nearestDist} m ${nearestDist < 200 ? '(⚠️ High Interf)' : '(Nominal)'}</span>
            </div>
        `;
    } else if (sel.type === 'user') {
        const u = sel.data;
        const sbs = AppState.networkData.bs_telemetry[u.serving_bs] || { name: `Tower ${u.serving_bs + 1}` };
        const isStat = u.is_stationary;
        const isNlos = u.is_nlos;
        
        inspectorEl.innerHTML = `
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Subscriber:</span>
                <span class="inspector-prop-val ${isStat ? 'text-cyan' : 'text-yellow'}">${isStat ? '📍 Fixed' : '📱 Mobile'} ${u.name}</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Serving Tower:</span>
                <span class="inspector-prop-val">Tower ${u.serving_bs + 1} (${sbs.name})</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Distance & Zone:</span>
                <span class="inspector-prop-val" style="color:${u.zone_color || '#10b981'};">${u.distance_m} m (${u.distance_zone || 'Nominal'})</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Propagation Path:</span>
                <span class="inspector-prop-val ${isNlos ? 'text-red' : 'text-green'}">${isNlos ? '🧱 NLOS (-18 dB Wall Loss)' : '🟢 LOS Clear'}</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Allocated Tx Power:</span>
                <span class="inspector-prop-val" style="color:${u.zone_color || '#10b981'};">⚡ ${u.allocated_power_dbm || 40} dBm</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Signal (RSRP):</span>
                <span class="inspector-prop-val">${u.rsrp_dbm} dBm</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">SINR Quality:</span>
                <span class="inspector-prop-val" style="color:${u.is_outage ? '#f43f5e' : '#10b981'}; font-weight:800;">${u.sinr_db} dB</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">Throughput Rate:</span>
                <span class="inspector-prop-val">${u.achievable_rate_mbps || u.rate_mbps || 850} Mbps</span>
            </div>
            <div class="inspector-prop-row">
                <span class="inspector-prop-key">QoS Status:</span>
                <span class="inspector-prop-val">${u.is_outage ? '<span class="badge-outage">OUTAGE (&lt;15dB)</span>' : '<span class="badge-ok">QoS COMPLIANT</span>'}</span>
            </div>
        `;
    }
}

function handleAddTower() {
    if (!AppState.networkData) return;
    const t = AppState.networkData;
    const newId = t.bs_telemetry.length;
    const name = `Tower ${newId + 1}`;
    const x = Math.min(800, 640 + ((newId - 3) * 50) % 150);
    const y = Math.min(460, 280 + ((newId - 3) * 60) % 140);
    
    const newBs = {
        bs_id: newId,
        name: name,
        x: x,
        y: y,
        boresight: 180.0,
        active_cand: 0,
        active_config: { cand_id: 0, beam_idx: 0, angle: 0.0, power_dbm: 34.0, subband: (newId % 3), label: `B0: 0° | 34 dBm | Sub-${newId % 3}` },
        candidates: [
            { cand_id: 0, beam_idx: 0, angle: 0.0, power_dbm: 34.0, subband: (newId % 3), label: `B0: 0° | 34 dBm | Sub-${newId % 3}` },
            { cand_id: 1, beam_idx: 1, angle: -20.0, power_dbm: 38.0, subband: ((newId + 1) % 3), label: `B1: -20° | 38 dBm | Sub-${(newId + 1) % 3}` },
            { cand_id: 2, beam_idx: 2, angle: 20.0, power_dbm: 36.0, subband: ((newId + 2) % 3), label: `B2: +20° | 36 dBm | Sub-${(newId + 2) % 3}` },
            { cand_id: 3, beam_idx: 3, angle: 0.0, power_dbm: 35.0, subband: (newId % 3), label: `B3: 0° | 35 dBm | Sub-${newId % 3}` }
        ]
    };
    t.bs_telemetry.push(newBs);
    AppState.selectedItem = { type: 'tower', data: newBs };
    
    fetch('/api/network/add_tower', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: x, y: y, name: name })
    }).catch(() => {});
    
    recalculateClientMobilityTelemetry();
    updateNetworkUI();
    updateInspectorUI();
    drawNetworkSimulation();
}

function handleAddUser() {
    if (!AppState.networkData) return;
    const t = AppState.networkData;
    const newId = t.user_telemetry.length;
    const name = `UE-${newId < 9 ? '0' : ''}${newId + 1}`;
    const x = Math.round(400 + (Math.random() - 0.5) * 220);
    const y = Math.round(230 + (Math.random() - 0.5) * 160);
    
    // Find closest tower
    let bestBs = 0;
    let minDist = 99999;
    t.bs_telemetry.forEach(bs => {
        const d = Math.hypot(x - bs.x, y - bs.y);
        if (d < minDist) {
            minDist = d;
            bestBs = bs.bs_id;
        }
    });
    
    const isStat = (newId % 2 !== 0);
    const zone = getDistanceZone(minDist);
    const newUe = {
        ue_id: newId,
        name: name,
        x: x,
        y: y,
        serving_bs: bestBs,
        distance_m: Math.round(minDist),
        distance_zone: zone.name,
        zone_color: zone.color,
        allocated_power_dbm: zone.powerDbm,
        is_stationary: isStat,
        mobility_type: isStat ? 'Fixed FWA' : 'Mobile UE',
        is_nlos: false,
        rsrp_dbm: -75,
        sinr_db: 18.2,
        is_outage: false
    };
    t.user_telemetry.push(newUe);
    AppState.selectedItem = { type: 'user', data: newUe };
    
    fetch('/api/network/add_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x: x, y: y, name: name, serving_bs_id: bestBs })
    }).catch(() => {});
    
    recalculateClientMobilityTelemetry();
    updateNetworkUI();
    updateInspectorUI();
    drawNetworkSimulation();
}

function setTowerDistance(mode) {
    if (!AppState.networkData) return;
    AppState.towerDistanceMode = mode;
    const t = AppState.networkData;
    const cx = 400, cy = 233;
    let scale = 1.0;
    if (mode === 'close') scale = 0.58;
    else if (mode === 'far') scale = 1.38;
    else scale = 1.0;
    
    const nominal = [
        { x: 220, y: 140 },
        { x: 580, y: 140 },
        { x: 400, y: 420 }
    ];
    
    nominal.forEach((pos, idx) => {
        if (idx < t.bs_telemetry.length) {
            t.bs_telemetry[idx].x = Math.round(cx + (pos.x - cx) * scale);
            t.bs_telemetry[idx].y = Math.round(cy + (pos.y - cy) * scale);
        }
    });
    
    fetch('/api/network/set_tower_distance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode })
    }).catch(() => {});
    
    recalculateClientMobilityTelemetry();
    updateNetworkUI();
    updateInspectorUI();
    drawNetworkSimulation();
}
"""

js += extra_functions

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Part 2 of app.js updated successfully.")
