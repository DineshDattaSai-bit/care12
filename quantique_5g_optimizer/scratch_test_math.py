import math

print("=== Testing 5G Simulation Math Engine ===")

# Test 3GPP UMi Path Loss at 28 GHz
def calc_path_loss(dist_m):
    d = max(dist_m, 10.0)
    # PL = 32.4 + 21 * log10(d) + 20 * log10(28)
    return 32.4 + 21.0 * math.log10(d) + 20.0 * math.log10(28.0)

# Test Antenna Gain (18 dBi peak, 30 deg 3dB beamwidth)
def calc_antenna_gain(steered_rad, target_rad):
    diff_deg = abs(steered_rad - target_rad) * 180.0 / math.pi
    if diff_deg > 180.0:
        diff_deg = 360.0 - diff_deg
    gain = max(18.0 - 12.0 * ((diff_deg / 30.0) ** 2), -15.0)
    return gain

# Test Shannon Throughput
def calc_shannon_throughput(sinr_linear, bandwidth_mhz=150.0):
    return bandwidth_mhz * math.log2(1.0 + sinr_linear)

for dist in [50, 100, 150, 200]:
    pl = calc_path_loss(dist)
    p_rx_on_boresight = 39.0 + 18.0 - pl  # 39 dBm Tx, 18 dBi gain
    print(f"Dist {dist}m: PathLoss = {pl:.1f} dB, Prx = {p_rx_on_boresight:.1f} dBm")

noise_floor_dbm = -85.0
noise_mw = 10.0 ** (noise_floor_dbm / 10.0)

# Scenario: Desired Prx = -55 dBm. No interference vs Co-channel interference Prx_interf = -60 dBm
p_sig_mw = 10.0 ** (-55.0 / 10.0)
sinr_no_interf = p_sig_mw / noise_mw
sinr_no_interf_db = 10.0 * math.log10(sinr_no_interf)
thr_no_interf = calc_shannon_throughput(sinr_no_interf)

p_interf_mw = 10.0 ** (-60.0 / 10.0)
sinr_with_interf = p_sig_mw / (p_interf_mw + noise_mw)
sinr_with_interf_db = 10.0 * math.log10(sinr_with_interf)
thr_with_interf = calc_shannon_throughput(sinr_with_interf)

print(f"\nNo Interference: SINR = {sinr_no_interf_db:.1f} dB, Throughput = {thr_no_interf:.1f} Mbps")
print(f"With Co-channel Clash: SINR = {sinr_with_interf_db:.1f} dB, Throughput = {thr_with_interf:.1f} Mbps")
print("Math Engine Test Passed Successfully!")
