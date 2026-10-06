import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update AppState
app_state_old = """const AppState = {
    viewMode: 'unified',
    currentTab: 'tab-simulator',
    networkData: null,"""

app_state_new = """const AppState = {
    viewMode: 'unified',
    currentTab: 'tab-simulator',
    selectedItem: null,
    draggedObject: null,
    dragObjectType: null,
    towerDistanceMode: 'medium',
    networkData: null,"""

if app_state_old in js:
    js = js.replace(app_state_old, app_state_new, 1)
    print("AppState updated.")

# 2. Add flow-step listeners to initNavigation
flow_step_code = """    // Architecture Pipeline Steps
    const pipeSteps = document.querySelectorAll('.pipeline-step');
    pipeSteps.forEach(step => {
        step.addEventListener('click', () => {
            const targetId = step.getAttribute('data-target');
            if (AppState.viewMode === 'unified') {
                scrollToSubsystem(targetId);
            } else {
                switchTab(targetId);
            }
        });
    });

    // How It Works Flow Steps
    document.querySelectorAll('.flow-step').forEach(step => {
        step.addEventListener('click', () => {
            const targetId = step.getAttribute('data-target');
            if (AppState.viewMode === 'unified') {
                scrollToSubsystem(targetId);
            } else {
                switchTab(targetId);
            }
        });
    });"""

old_pipe_steps = """    // Architecture Pipeline Steps
    const pipeSteps = document.querySelectorAll('.pipeline-step');
    pipeSteps.forEach(step => {
        step.addEventListener('click', () => {
            const targetId = step.getAttribute('data-target');
            if (AppState.viewMode === 'unified') {
                scrollToSubsystem(targetId);
            } else {
                switchTab(targetId);
            }
        });
    });"""

if old_pipe_steps in js:
    js = js.replace(old_pipe_steps, flow_step_code, 1)
    print("Flow steps navigation updated.")

# 3. Add Event Listeners for interactive controls and accordions
extra_listeners = """    // Add Tower Button
    document.getElementById('btn-add-tower')?.addEventListener('click', () => {
        handleAddTower();
    });

    // Add User Button
    document.getElementById('btn-add-user')?.addEventListener('click', () => {
        handleAddUser();
    });

    // Preset Buttons (Dense Urban, Moderate Load, High Interference)
    document.querySelectorAll('.btn-preset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            const scen = e.currentTarget.getAttribute('data-scenario');
            const selectEl = document.getElementById('scenario-select');
            if (selectEl) selectEl.value = scen;
            changeScenario(scen);
        });
    });

    // Quick Tower Distance Buttons (Close, Medium, Far)
    document.querySelectorAll('.btn-dist-quick').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-dist-quick').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            const distMode = e.currentTarget.getAttribute('data-dist');
            setTowerDistance(distMode);
        });
    });

    // Advanced Simulation Controls Panel Toggle
    document.getElementById('btn-toggle-advanced-sim')?.addEventListener('click', () => {
        const p = document.getElementById('advanced-sim-panel');
        if (p) p.classList.toggle('hidden');
    });

    // Technical Accordions
    document.getElementById('btn-toggle-quantum-tech')?.addEventListener('click', () => {
        const p = document.getElementById('tech-details-quantum-panel');
        const arrow = document.getElementById('acc-arrow-quantum');
        p?.classList.toggle('hidden');
        arrow?.classList.toggle('rotated');
        if (!p?.classList.contains('hidden')) {
            renderQUBOGrid();
            renderCircuitSchematic();
            renderTunnelingChart();
            renderHistogramChart();
        }
    });

    document.getElementById('btn-toggle-oran-tech')?.addEventListener('click', () => {
        const p = document.getElementById('tech-details-oran-panel');
        const arrow = document.getElementById('acc-arrow-oran');
        p?.classList.toggle('hidden');
        arrow?.classList.toggle('rotated');
    });

    document.getElementById('btn-toggle-hil-tech')?.addEventListener('click', () => {
        const p = document.getElementById('tech-details-hil-panel');
        const arrow = document.getElementById('acc-arrow-hil');
        p?.classList.toggle('hidden');
        arrow?.classList.toggle('rotated');
    });"""

old_event_listeners_end = """    // Print Evaluation Dossier
    document.getElementById('btn-print-report')?.addEventListener('click', () => {
        window.print();
    });"""

new_event_listeners_end = old_event_listeners_end + "\n\n" + extra_listeners

if old_event_listeners_end in js:
    js = js.replace(old_event_listeners_end, new_event_listeners_end, 1)
    print("New event listeners added.")

# 4. Update WALKTHROUGH_STEPS with 5-step story
old_walkthrough = """const WALKTHROUGH_STEPS = [
    {
        step: 1,
        title: "Step 1/5: Classical 5G Baseline & Coverage Outages",
        desc: "Analyzing 3-cell 28 GHz mmWave deployment. Uncoordinated greedy beam allocation creates severe co-channel interference, resulting in 5 subscriber QoS outages.",
        target: "tab-simulator",
        action: async () => {
            await resetToGreedyBaseline();
        }
    },
    {
        step: 2,
        title: "Step 2/5: 12-Qubit QUBO Formulation & QAOA Solver",
        desc: "Channel states mapped to unified Cost Hamiltonian. QAOA variational circuit simulates quantum tunneling through non-convex energy barriers to isolate the global minimum.",
        target: "tab-quantum",
        action: async () => {
            await runQuantumOptimizationSequence();
        }
    },
    {
        step: 3,
        title: "Step 3/5: O-RAN Near-RT RIC Feasibility Guardrail",
        desc: "Deterministic safety guard evaluates candidate in <15ms. All 4 physical constraints verified: Power ceiling (73.3W <= 120W), SINR QoS (>=15dB), Leakage Floor, and Spectrum Orthogonality.",
        target: "tab-guard",
        action: async () => {
            updateGuardUI();
        }
    },
    {
        step: 4,
        title: "Step 4/5: Hardware-in-the-Loop Phased Array Twin",
        desc: "Progressive phase matrix Δϕ = -m·π·sin(θ) steers the 28 GHz far-field radiation lobe. Telemetry frame $HIL_TX is streamed over 115200 baud serial to the Arduino servo.",
        target: "tab-hil",
        action: async () => {
            updateHILUI();
            drawPolarDiagram();
        }
    },
    {
        step: 5,
        title: "Step 5/5: Quantitative Verification & Final Impact",
        desc: "Ground-truth benchmark confirmed: Mean SINR improved from 14.2 dB to 22.8 dB (+8.6 dB gain), Power cut to 67.2% (32.8% savings), and Outages completely eliminated (5 -> 0).",
        target: "tab-results",
        action: async () => {
            renderResultsCharts();
        }
    }
];"""

new_walkthrough = """const WALKTHROUGH_STEPS = [
    {
        step: 1,
        title: "Step 1/5: Network Problem Detected",
        desc: "Under heavy network load, traditional uncoordinated resource allocation creates severe co-channel interference, poor signal quality (< 15 dB), and 5 user service outages.",
        target: "tab-simulator",
        action: async () => {
            await resetToGreedyBaseline();
        }
    },
    {
        step: 2,
        title: "Step 2/5: Quantum Optimization Running",
        desc: "Mapping channel states to a 12-qubit QUBO on O-RAN Near-RT RIC. QAOA variational circuit simulates quantum tunneling through non-convex energy barriers to isolate the global minimum in <50ms.",
        target: "tab-quantum",
        action: async () => {
            await runQuantumOptimizationSequence();
        }
    },
    {
        step: 3,
        title: "Step 3/5: Safety Constraints Verified",
        desc: "Deterministic Near-RT RIC safety guard validates decoded bitstrings against 4 strict physical constraints: Power limit, SINR QoS, Interference leakage, and Spectrum orthogonality.",
        target: "tab-guard",
        action: async () => {
            updateGuardUI();
        }
    },
    {
        step: 4,
        title: "Step 4/5: Physical Beam Steering Demonstrated",
        desc: "Progressive phase matrix Δϕ = -m·π·sin(θ) steers the 28 GHz antenna array to target azimuth (+15°), streamed in real time over serial to the physical servo twin.",
        target: "tab-hil",
        action: async () => {
            updateHILUI();
            drawPolarDiagram();
        }
    },
    {
        step: 5,
        title: "Step 5/5: Optimization Results Achieved",
        desc: "Ground-truth benchmark confirmed: Signal quality improved +60.5% (14.2 dB -> 22.8 dB), Power cut by 32.8%, and Outages completely eliminated (5 -> 0).",
        target: "tab-results",
        action: async () => {
            renderResultsCharts();
        }
    }
];"""

if old_walkthrough in js:
    js = js.replace(old_walkthrough, new_walkthrough, 1)
    print("Walkthrough steps updated.")

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Part 1 of app.js updated successfully.")
