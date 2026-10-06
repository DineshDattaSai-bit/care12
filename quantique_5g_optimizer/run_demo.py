"""
One-Click Launch Script for Quantique Hackathon 2026 Prototype
Starts the Flask backend server and automatically opens the browser.
"""
import sys
import os
import webbrowser
import threading
import time

# Ensure project path is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.app import app

def open_browser(port):
    time.sleep(1.2)
    url = f"http://localhost:{port}"
    print(f"[*] Opening browser to {url} ...")
    webbrowser.open(url)

if __name__ == "__main__":
    port = 5000
    print("=" * 75)
    print("  PLUS QISKIT FALL FEST 2026 - QUANTIQUE HACKATHON")
    print("  Team Quantum Nexus: Hybrid Quantum 5G/6G Resource Allocator")
    print("=" * 75)
    print(f"[*] Starting local server on http://localhost:{port} ...")
    print("[*] Prototype contains all 5 interactive modules:")
    print("    1. Network Simulator (Cells, Beams, Users, Co-Channel Interference)")
    print("    2. Quantum Engine (QUBO Matrix, QAOA Circuit, Tunneling vs Trap, Shot Histogram)")
    print("    3. Feasibility Guard (Power Limit, SINR Target, Interference, Orthogonality)")
    print("    4. Hardware-in-the-Loop Demonstrator (Phased Array, Polar Pattern, Servo, Serial)")
    print("    5. Results Dashboard (Side-by-side BEFORE vs AFTER with 14.2dB -> 22.8dB)")
    print("=" * 75)
    
    # Open browser in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Run server
    app.run(host="0.0.0.0", port=port, debug=False)
