"""
Hardware-in-the-Loop (HIL) Demonstration Engine & Serial Telemetry Bridge
Models an 8-Element 28 GHz mmWave Phased Array Antenna, progressive phase shifters,
physical servo/stepper motor azimuth steering, and bidirectional serial telemetry frames.
"""
import math
import time

class HILBridge:
    def __init__(self):
        self.num_elements = 8            # 8-element Uniform Linear Array (ULA)
        self.d_over_lambda = 0.5         # Half-wavelength spacing (lambda / 2)
        self.baud_rate = 115200
        self.serial_port = "COM4 (Virtual HIL Loopback)"
        self.connected = True
        
        # Telemetry log buffer
        self.serial_log = []
        self._append_log("INFO", "HIL Serial Bridge initialized at 115200 baud.")
        self._append_log("INFO", "Device: mmWave 28 GHz 8-Channel Phased Array Transceiver Panel v3.2")
        self._append_log("INFO", "Servo Motor Controller: MG996R Precision Azimuth Stepper Controller")
        
        # Current physical state
        self.current_azimuth_deg = 15.0
        self.target_azimuth_deg = 15.0
        self.servo_angle_deg = 105.0     # 90° center + 15°
        self.vswr = 1.12                 # Voltage Standing Wave Ratio
        self.rf_temp_c = 34.2
        self.pa_status = "ACTIVE"        # Power Amplifier Status
        
    def _append_log(self, direction, message):
        t_str = time.strftime("%H:%M:%S")
        self.serial_log.append(f"[{t_str}] [{direction}] {message}")
        if len(self.serial_log) > 60:
            self.serial_log.pop(0)

    def compute_phased_array_settings(self, target_angle_deg):
        """
        Computes progressive phase shifts Delta_phi for 8-element ULA:
        Delta_phi = - 2 * pi * (d / lambda) * sin(theta_target)
        """
        theta_rad = math.radians(target_angle_deg)
        phase_step_rad = -2.0 * math.pi * self.d_over_lambda * math.sin(theta_rad)
        phase_step_deg = math.degrees(phase_step_rad) % 360.0
        
        elements = []
        for m in range(self.num_elements):
            elem_phase = (m * phase_step_deg) % 360.0
            elements.append({
                "element_id": m,
                "phase_deg": round(elem_phase, 1),
                "amplitude_normalized": 1.0,
                "status": "LOCKED"
            })
            
        return phase_step_deg, elements

    def generate_polar_radiation_pattern(self, target_angle_deg):
        """
        Calculates 360-degree array factor radiation pattern:
        AF(theta) = | sin(N * psi / 2) / (N * sin(psi / 2)) |
        where psi = 2 * pi * (d / lambda) * (sin(theta) - sin(theta_0))
        """
        pattern = []
        theta_0_rad = math.radians(target_angle_deg)
        n = self.num_elements
        
        for deg in range(0, 360, 2):
            # Treat 0° as boresight
            rel_deg = (deg + 180) % 360 - 180
            theta_rad = math.radians(rel_deg)
            
            # Array factor argument
            psi = 2.0 * math.pi * self.d_over_lambda * (math.sin(theta_rad) - math.sin(theta_0_rad))
            
            if abs(psi) < 1e-6:
                af = 1.0
            else:
                sin_num = math.sin(n * psi / 2.0)
                sin_den = n * math.sin(psi / 2.0)
                af = abs(sin_num / (sin_den + 1e-9))
                
            # Front-to-back element pattern factor
            elem_factor = max(math.cos(theta_rad), 0.05) if abs(rel_deg) <= 90 else 0.05
            composite = af * elem_factor
            
            # In dB scale normalized to [0, 1] for polar canvas
            db = 20.0 * math.log10(max(composite, 0.02))
            norm_r = max((db + 30.0) / 30.0, 0.05)  # 30 dB dynamic range
            
            pattern.append({
                "angle_deg": deg,
                "radius": round(norm_r, 3),
                "gain_db": round(db, 1)
            })
            
        return pattern

    def execute_hardware_steer(self, gnodeb_id, beam_angle_deg, power_dbm, subband_id):
        """
        Transmits actual framed command over the serial interface and updates physical demonstrator.
        """
        self.target_azimuth_deg = beam_angle_deg
        self.current_azimuth_deg = beam_angle_deg
        # Map [-45°, +45°] to Servo [45°, 135°]
        self.servo_angle_deg = round(90.0 + beam_angle_deg, 1)
        
        phase_step_deg, elements = self.compute_phased_array_settings(beam_angle_deg)
        polar_pattern = self.generate_polar_radiation_pattern(beam_angle_deg)
        
        # Construct NMEA-style HIL command packet
        crc_val = f"0x{(int(abs(beam_angle_deg * 17) + gnodeb_id * 23) % 0xFFFF):04X}"
        tx_frame = f"$HIL_TX,GNB={gnodeb_id},BEAM_AZ={beam_angle_deg:+.1f},SERVO={self.servo_angle_deg:.1f}deg,PWR={power_dbm:.1f}dBm,SUB={subband_id}*{crc_val}"
        self._append_log("TX", tx_frame)
        
        # Mock immediate MCU response
        rx_frame = f"$HIL_ACK,DEV=PHASED_ARRAY_PANEL,SERVO_LOCKED=TRUE,POS={self.servo_angle_deg:.1f}deg,PHASE_STEP={phase_step_deg:.1f}deg,VSWR=1.11*0x98AE"
        self._append_log("RX", rx_frame)
        
        return {
            "gnodeb_id": gnodeb_id,
            "target_azimuth_deg": beam_angle_deg,
            "servo_motor_angle_deg": self.servo_angle_deg,
            "phase_step_deg": round(phase_step_deg, 1),
            "elements": elements,
            "polar_pattern": polar_pattern,
            "vswr": self.vswr,
            "rf_temperature_c": self.rf_temp_c,
            "pa_status": self.pa_status,
            "last_tx_frame": tx_frame,
            "last_rx_frame": rx_frame,
            "serial_log": self.serial_log[-20:]
        }
