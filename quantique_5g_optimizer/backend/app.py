"""
Flask Server & REST API for Quantum 5G/6G Resource Optimization Prototype
Provides APIs for all 5 subsystems and serves the interactive frontend application.
"""
import os
import sys
import gzip
from flask import Flask, jsonify, request, render_template, send_from_directory

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import NetworkEnvironment
from backend.qubo_engine import QUBOEngine
from backend.qaoa_solver import QAOASolver
from backend.feasibility_guard import FeasibilityGuard
from backend.hil_bridge import HILBridge
from backend.results_engine import ResultsEngine

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
)

# Initialize application singletons
network_env = NetworkEnvironment()
qubo_engine = QUBOEngine(network_env)
qaoa_solver = QAOASolver(qubo_engine)
feasibility_guard = FeasibilityGuard(network_env)
hil_bridge = HILBridge()
results_engine = ResultsEngine(network_env)

# Cache last optimization result
last_qaoa_solution = None

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    
    # High-speed Gzip compression for mobile performance
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if "gzip" in accept_encoding.lower() and response.status_code == 200 and not response.direct_passthrough:
        if response.mimetype in ["text/html", "text/css", "application/javascript", "application/json"]:
            response.data = gzip.compress(response.data)
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = len(response.data)
            
    return response

@app.route("/")
def index():
    return render_template("index.html")

# ----------------- Consolidated Bootstrap API (Ultra-Fast Single Roundtrip) -----------------
@app.route("/api/bootstrap", methods=["GET"])
def get_bootstrap_data():
    telemetry = network_env.compute_telemetry()
    qubo_data = qubo_engine.get_qubo_summary()
    guard_data = feasibility_guard.evaluate()
    
    active_bs0 = network_env.base_stations[0].active_config
    angle = active_bs0["angle"]
    phase_step, elements = hil_bridge.compute_phased_array_settings(angle)
    polar_pattern = hil_bridge.generate_polar_radiation_pattern(angle)
    hil_data = {
        "serial_port": hil_bridge.serial_port,
        "baud_rate": hil_bridge.baud_rate,
        "connected": hil_bridge.connected,
        "target_azimuth_deg": angle,
        "servo_motor_angle_deg": hil_bridge.servo_angle_deg,
        "phase_step_deg": round(phase_step, 1),
        "elements": elements,
        "polar_pattern": polar_pattern,
        "vswr": hil_bridge.vswr,
        "rf_temperature_c": hil_bridge.rf_temp_c,
        "pa_status": hil_bridge.pa_status,
        "serial_log": hil_bridge.serial_log[-20:]
    }
    
    allocations = last_qaoa_solution["decoded_allocations"] if last_qaoa_solution else {0: 0, 1: 2, 2: 1}
    results_data = results_engine.get_comparison(allocations)
    
    return jsonify({
        "status": "success",
        "network": telemetry,
        "qubo": qubo_data,
        "guard": guard_data,
        "hil": hil_data,
        "results": results_data
    })

# ----------------- Part 1: Network Simulator APIs -----------------
@app.route("/api/network/state", methods=["GET"])
def get_network_state():
    telemetry = network_env.compute_telemetry()
    return jsonify({
        "status": "success",
        "scenario": network_env.scenario,
        "carrier_freq_ghz": network_env.carrier_freq_ghz,
        "channel_bandwidth_mhz": network_env.channel_bandwidth_mhz,
        "thermal_noise_dbm": round(network_env.thermal_noise_dbm, 1),
        "telemetry": telemetry
    })

@app.route("/api/network/update_user", methods=["POST"])
def update_user():
    data = request.json or {}
    ue_id = data.get("ue_id")
    new_x = data.get("x")
    new_y = data.get("y")
    
    for u in network_env.users:
        if u.ue_id == ue_id:
            u.x = float(new_x)
            u.y = float(new_y)
            break
            
    telemetry = network_env.compute_telemetry()
    return jsonify({"status": "success", "telemetry": telemetry})

@app.route("/api/network/set_scenario", methods=["POST"])
def set_scenario():
    data = request.json or {}
    scenario = data.get("scenario", "dense_traffic")
    network_env.load_scenario(scenario)
    
    # Reinitialize solvers with new user distributions
    global qubo_engine, qaoa_solver
    qubo_engine = QUBOEngine(network_env)
    qaoa_solver = QAOASolver(qubo_engine)
    
    telemetry = network_env.compute_telemetry()
    return jsonify({"status": "success", "scenario": scenario, "telemetry": telemetry})

@app.route("/api/network/set_bs_config", methods=["POST"])
def set_bs_config():
    data = request.json or {}
    bs_id = int(data.get("bs_id", 0))
    cand_idx = int(data.get("cand_idx", 0))
    
    if 0 <= bs_id < len(network_env.base_stations):
        network_env.base_stations[bs_id].active_cand_idx = cand_idx
        
    telemetry = network_env.compute_telemetry()
    return jsonify({"status": "success", "telemetry": telemetry})

@app.route("/api/network/add_tower", methods=["POST"])
def add_tower():
    data = request.json or {}
    x = float(data.get("x", 650.0))
    y = float(data.get("y", 300.0))
    name = data.get("name")
    bs = network_env.add_tower(x, y, name)
    telemetry = network_env.compute_telemetry()
    return jsonify({"status": "success", "bs_id": bs.bs_id, "name": bs.name, "telemetry": telemetry})

@app.route("/api/network/add_user", methods=["POST"])
def add_user():
    data = request.json or {}
    x = float(data.get("x", 450.0))
    y = float(data.get("y", 280.0))
    name = data.get("name")
    s_bs = data.get("serving_bs_id")
    ue = network_env.add_user(x, y, name, s_bs)
    telemetry = network_env.compute_telemetry()
    return jsonify({"status": "success", "ue_id": ue.ue_id, "name": ue.name, "telemetry": telemetry})

@app.route("/api/network/update_tower", methods=["POST"])
def update_tower():
    data = request.json or {}
    bs_id = int(data.get("bs_id", 0))
    x = float(data.get("x", 400.0))
    y = float(data.get("y", 200.0))
    telemetry = network_env.update_tower(bs_id, x, y)
    return jsonify({"status": "success", "telemetry": telemetry})

@app.route("/api/network/set_tower_distance", methods=["POST"])
def set_tower_distance():
    data = request.json or {}
    mode = data.get("mode", "medium")
    telemetry = network_env.set_tower_separation(mode)
    return jsonify({"status": "success", "mode": mode, "telemetry": telemetry})

# ----------------- Part 2: Quantum Engine APIs -----------------
@app.route("/api/quantum/qubo", methods=["GET"])
def get_qubo():
    summary = qubo_engine.get_qubo_summary()
    return jsonify({"status": "success", "data": summary})

@app.route("/api/quantum/solve_qaoa", methods=["POST"])
def solve_qaoa():
    global last_qaoa_solution
    data = request.json or {}
    depth = int(data.get("depth", 1))
    max_iters = int(data.get("max_iters", 25))
    
    # Run QAOA statevector simulation
    solution = qaoa_solver.run_optimization(max_iters=max_iters, depth=depth)
    last_qaoa_solution = solution
    
    # Apply optimal configuration to network environment
    for bs_id, cand_idx in solution["decoded_allocations"].items():
        network_env.base_stations[bs_id].active_cand_idx = cand_idx
        
    # Also steer the HIL physical demonstrator to BS 0's chosen beam
    bs0_cand = network_env.base_stations[0].active_config
    hil_bridge.execute_hardware_steer(
        gnodeb_id=0,
        beam_angle_deg=bs0_cand["angle"],
        power_dbm=bs0_cand["power_dbm"],
        subband_id=bs0_cand["subband"]
    )
    
    return jsonify({"status": "success", "solution": solution})

# ----------------- Part 3: Feasibility Guard APIs -----------------
@app.route("/api/guard/validate", methods=["GET", "POST"])
def validate_guard():
    # Evaluate feasibility guard on current base station configurations
    verdict = feasibility_guard.evaluate()
    return jsonify({"status": "success", "guard_evaluation": verdict})

# ----------------- Part 4: Hardware-in-the-Loop APIs -----------------
@app.route("/api/hil/telemetry", methods=["GET"])
def get_hil_telemetry():
    active_bs0 = network_env.base_stations[0].active_config
    angle = active_bs0["angle"]
    phase_step, elements = hil_bridge.compute_phased_array_settings(angle)
    polar_pattern = hil_bridge.generate_polar_radiation_pattern(angle)
    
    return jsonify({
        "status": "success",
        "data": {
            "serial_port": hil_bridge.serial_port,
            "baud_rate": hil_bridge.baud_rate,
            "connected": hil_bridge.connected,
            "target_azimuth_deg": angle,
            "servo_motor_angle_deg": hil_bridge.servo_angle_deg,
            "phase_step_deg": round(phase_step, 1),
            "elements": elements,
            "polar_pattern": polar_pattern,
            "vswr": hil_bridge.vswr,
            "rf_temperature_c": hil_bridge.rf_temp_c,
            "pa_status": hil_bridge.pa_status,
            "serial_log": hil_bridge.serial_log[-20:]
        }
    })

@app.route("/api/hil/steer", methods=["POST"])
def steer_hil():
    data = request.json or {}
    gnodeb_id = int(data.get("gnodeb_id", 0))
    angle = float(data.get("angle", 15.0))
    pwr = float(data.get("power_dbm", 37.0))
    sub = int(data.get("subband", 0))
    
    result = hil_bridge.execute_hardware_steer(gnodeb_id, angle, pwr, sub)
    return jsonify({"status": "success", "data": result})

# ----------------- Part 5: Results Dashboard APIs -----------------
@app.route("/api/results/comparison", methods=["GET"])
def get_results_comparison():
    allocations = last_qaoa_solution["decoded_allocations"] if last_qaoa_solution else {0: 0, 1: 2, 2: 1}
    comparison = results_engine.get_comparison(allocations)
    return jsonify({"status": "success", "comparison": comparison})

if __name__ == "__main__":
    print("=" * 70)
    print("  QUANTIQUE HACKATHON 2026 - TEAM QUANTUM NEXUS")
    print("  Hybrid Quantum 5G/6G Resource Optimization Prototype")
    print("  Serving at: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5000, debug=False)
