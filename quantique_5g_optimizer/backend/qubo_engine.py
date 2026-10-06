"""
QUBO (Quadratic Unconstrained Binary Optimization) Formulation Engine
Transforms 5G/6G Resource Allocation into an Ising Cost Hamiltonian for QAOA.
"""
import math
from .models import NetworkEnvironment

class QUBOEngine:
    def __init__(self, net_env: NetworkEnvironment):
        self.env = net_env
        self.num_bs = len(self.env.base_stations)  # 3 Base Stations
        self.cands_per_bs = 4                      # 4 candidate settings per BS
        self.num_qubits = self.num_bs * self.cands_per_bs  # 12 Qubits
        
        # Variable naming: BS{i}_C{k} -> x_0 to x_11
        self.var_names = []
        for i in range(self.num_bs):
            for k in range(self.cands_per_bs):
                cand = self.env.base_stations[i].candidates[k]
                self.var_names.append(f"x_{i}_{k} (BS{i}_B{cand['beam_idx']}_P{int(cand['power_dbm'])}_S{cand['subband']})")
                
        # Penalty multipliers (Slide 5 & Slide 8: Dynamic Penalty Tuning)
        self.lambda_power = 3.5
        self.lambda_interf = 8.0
        self.lambda_unique = 25.0  # Hard constraint penalty for sum(x_{i,k}) == 1
        
    def get_var_index(self, bs_idx, cand_idx):
        return bs_idx * self.cands_per_bs + cand_idx

    def build_qubo_matrix(self):
        """
        Builds the 12x12 QUBO matrix Q such that Cost(x) = x^T Q x
        Diagonal entries Q[i][i] contain linear weights (Power, SINR reward, Uniqueness linear part)
        Off-diagonal entries Q[i][j] (i < j) contain quadratic couplings (Interference, Uniqueness mutual exclusion)
        """
        n = self.num_qubits
        Q = [[0.0 for _ in range(n)] for _ in range(n)]
        
        # 1. Uniqueness Constraint: lambda_unique * (sum_{k} x_{i,k} - 1)^2
        # (sum x_k - 1)^2 = sum x_k^2 + 2 sum_{k<l} x_k x_l - 2 sum x_k + 1
        # Since x_k in {0,1}, x_k^2 = x_k.
        # Diagonal term: lambda_unique * (1 - 2) = -lambda_unique
        # Off-diagonal term (k < l for same BS): + 2 * lambda_unique
        for bs_idx in range(self.num_bs):
            for k in range(self.cands_per_bs):
                idx = self.get_var_index(bs_idx, k)
                Q[idx][idx] += -self.lambda_unique
                
            for k1 in range(self.cands_per_bs):
                for k2 in range(k1 + 1, self.cands_per_bs):
                    idx1 = self.get_var_index(bs_idx, k1)
                    idx2 = self.get_var_index(bs_idx, k2)
                    Q[idx1][idx2] += 2.0 * self.lambda_unique
                    
        # 2. Power Consumption Linear Cost: lambda_power * (Power_mw / Max_power_mw)
        max_p_mw = 10.0 ** (43.0 / 10.0)  # 20W max
        for bs_idx, bs in enumerate(self.env.base_stations):
            for k, cand in enumerate(bs.candidates):
                idx = self.get_var_index(bs_idx, k)
                p_mw = 10.0 ** (cand["power_dbm"] / 10.0)
                power_normalized = p_mw / max_p_mw
                Q[idx][idx] += self.lambda_power * power_normalized
                
        # 3. SINR Reward (Negative cost): - 1.0 * (Estimated Coverage Utility)
        # Evaluates how well this beam covers users intended for this base station
        for bs_idx, bs in enumerate(self.env.base_stations):
            assigned_users = [u for u in self.env.users if u.serving_bs_id == bs_idx]
            for k, cand in enumerate(bs.candidates):
                idx = self.get_var_index(bs_idx, k)
                total_gain = 0.0
                for u in assigned_users:
                    gain = self.env.calculate_antenna_gain_dbi(bs, cand["angle"], u.x, u.y)
                    dist = math.hypot(u.x - bs.x, u.y - bs.y)
                    pl = self.env.calculate_pathloss_3gpp(dist)
                    rsrp = cand["power_dbm"] + gain - pl
                    total_gain += max(rsrp + 110.0, 0.0)  # Normalized utility
                    
                # Normalize coverage utility
                util_score = total_gain / (len(assigned_users) * 40.0 + 1e-4)
                Q[idx][idx] += -12.0 * util_score  # Reward is negative cost
                
        # 4. Inter-cell Co-channel Interference Cross-Coupling (Off-diagonal)
        # Occurs when two different BS choose the SAME subband channel and beams intersect
        for bs1_idx in range(self.num_bs):
            bs1 = self.env.base_stations[bs1_idx]
            for bs2_idx in range(bs1_idx + 1, self.num_bs):
                bs2 = self.env.base_stations[bs2_idx]
                
                # Check user vulnerability between the two base stations
                users_bs1 = [u for u in self.env.users if u.serving_bs_id == bs1_idx]
                users_bs2 = [u for u in self.env.users if u.serving_bs_id == bs2_idx]
                
                for k1, cand1 in enumerate(bs1.candidates):
                    idx1 = self.get_var_index(bs1_idx, k1)
                    for k2, cand2 in enumerate(bs2.candidates):
                        idx2 = self.get_var_index(bs2_idx, k2)
                        
                        # Only co-channel interference occurs if subband is identical
                        if cand1["subband"] == cand2["subband"]:
                            interf_metric = 0.0
                            
                            # BS2 leaking into BS1's users
                            for u in users_bs1:
                                gain_leak = self.env.calculate_antenna_gain_dbi(bs2, cand2["angle"], u.x, u.y)
                                dist_leak = math.hypot(u.x - bs2.x, u.y - bs2.y)
                                pl_leak = self.env.calculate_pathloss_3gpp(dist_leak)
                                p_leak_mw = 10.0 ** ((cand2["power_dbm"] + gain_leak - pl_leak) / 10.0)
                                interf_metric += p_leak_mw
                                
                            # BS1 leaking into BS2's users
                            for u in users_bs2:
                                gain_leak = self.env.calculate_antenna_gain_dbi(bs1, cand1["angle"], u.x, u.y)
                                dist_leak = math.hypot(u.x - bs1.x, u.y - bs1.y)
                                pl_leak = self.env.calculate_pathloss_3gpp(dist_leak)
                                p_leak_mw = 10.0 ** ((cand1["power_dbm"] + gain_leak - pl_leak) / 10.0)
                                interf_metric += p_leak_mw
                                
                            # Scale penalty
                            scaled_interf = min(interf_metric * 1e8, 15.0)
                            Q[idx1][idx2] += self.lambda_interf * scaled_interf

        return Q

    def get_qubo_summary(self):
        Q = self.build_qubo_matrix()
        # Round entries for clean presentation
        rounded_q = [[round(Q[i][j], 2) for j in range(self.num_qubits)] for i in range(self.num_qubits)]
        
        return {
            "num_qubits": self.num_qubits,
            "variable_names": self.var_names,
            "lambda_multipliers": {
                "lambda_power": self.lambda_power,
                "lambda_interf": self.lambda_interf,
                "lambda_uniqueness": self.lambda_unique
            },
            "qubo_matrix": rounded_q,
            "hamiltonian_latex": r"H_C = H_{\text{SINR}} + \lambda_1 H_{\text{Power}} + \lambda_2 H_{\text{Interference}} + \lambda_3 H_{\text{Uniqueness}}",
            "qubo_formula": r"\min_{x \in \{0,1\}^{12}} x^T Q x"
        }
