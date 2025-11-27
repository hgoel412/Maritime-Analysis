"""
Phase 4: Patrol vs Tracking Tasking Analysis
Compares operational surveillance modes (patrol vs tracking) for maritime SAR constellation.
"""

from pathlib import Path
import csv
from typing import List, Dict, Tuple, Optional
from parsers import (
    parse_ship1_eez_west,
    parse_ship2_eez_generic,
    parse_ship1_ship3_eez_west,
    parse_blocked_access,
)
from phase4_sensor_params import SARSensorParams, SHIP_ROUTES, DEFAULT_SENSOR

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "12sat_data"
PHASE4_DIR = BASE_DIR / "phase4_analysis"
PHASE4_DIR.mkdir(exist_ok=True)

N_SATS = 12

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_ship_intervals(ship_id: str, eez_name: str) -> List[Dict]:
    """Get ship EEZ entry/exit intervals."""
    if ship_id in ["Ship1", "Ship3"] and eez_name != "EEZ_West":
        raise ValueError(f"{ship_id} only in EEZ_West")
    if ship_id == "Ship2" and eez_name != "EEZ_East":
        raise ValueError("Ship2 only in EEZ_East")

    if ship_id == "Ship1":
        path = DATA_DIR / "Access_Ship1_EEZ_West.csv"
        return parse_ship1_eez_west(path)
    elif ship_id == "Ship3":
        path = DATA_DIR / "Access_Ship1_Ship3_EEZ_West.csv"
        all_ints = parse_ship1_ship3_eez_west(path)
        return [x for x in all_ints if x["ship_id"] == "Ship3"]
    elif ship_id == "Ship2":
        path = DATA_DIR / "Access_Ship2_EEZ_East.csv"
        return parse_ship2_eez_generic(path, ship_id="Ship2")

    raise ValueError(f"Unknown ship: {ship_id}")

def get_eez_sat_passes(eez_name: str) -> List[Dict]:
    """Get all satellite passes over an EEZ."""
    if eez_name == "EEZ_West":
        eez_file = DATA_DIR / "Acess_EEZ_West-To-Satellite-Walker12.csv"
    elif eez_name == "EEZ_East":
        eez_file = DATA_DIR / "Acess_EEZ_East-To-Satellite-Walker12.csv"
    else:
        raise ValueError(f"Unknown EEZ: {eez_name}")

    return parse_blocked_access(eez_file, n_blocks=N_SATS)

def ship_on_known_route(ship_id: str) -> bool:
    """Check if ship on known routes: commercial ships are, dark ships are not."""
    return ship_id in ["Ship1", "Ship2"]

# ============================================================================
# PATROL MODE: Wide-swath coverage
# ============================================================================

def detect_ship_patrol_mode(ship_id: str, eez_name: str, sensor: SARSensorParams) -> Optional[Tuple]:
    """PATROL MODE: Wide-swath coverage. Ship detected on first satellite pass."""
    ship_ints = get_ship_intervals(ship_id, eez_name)
    if not ship_ints:
        return None

    ship_int = ship_ints[0]
    t_in = ship_int["start_s"]
    t_out = ship_int["stop_s"]

    eez_passes = get_eez_sat_passes(eez_name)

    best_detection = None
    best_sat_id = None

    for sat_id in range(N_SATS):
        sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
        overlapping_passes = [
            p for p in sat_passes
            if p["start_s"] <= t_out and p["stop_s"] >= t_in
        ]

        if not overlapping_passes:
            continue

        first_pass = min(overlapping_passes, key=lambda x: x["start_s"])
        t_detect = max(first_pass["start_s"], t_in) + sensor.sar_processing_delay_s

        if best_detection is None or t_detect < best_detection:
            best_detection = t_detect
            best_sat_id = sat_id + 1

    if best_detection is None:
        return None

    detect_latency = best_detection - t_in
    return (ship_id, eez_name, t_in, best_detection, best_sat_id, detect_latency, "PATROL")

# ============================================================================
# TRACKING MODE: Focused coverage on known routes
# ============================================================================

def detect_ship_tracking_mode(ship_id: str, eez_name: str, sensor: SARSensorParams) -> Optional[Tuple]:
    """TRACKING MODE: Optimized for known routes. Dark ships may be missed."""
    ship_ints = get_ship_intervals(ship_id, eez_name)
    if not ship_ints:
        return None

    ship_int = ship_ints[0]
    t_in = ship_int["start_s"]
    t_out = ship_int["stop_s"]

    on_route = ship_on_known_route(ship_id)
    eez_passes = get_eez_sat_passes(eez_name)

    if on_route:
        best_detection = None
        best_sat_id = None

        for sat_id in range(N_SATS):
            sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
            overlapping_passes = [
                p for p in sat_passes
                if p["start_s"] <= t_out and p["stop_s"] >= t_in
            ]

            if not overlapping_passes:
                continue

            first_pass = min(overlapping_passes, key=lambda x: x["start_s"])
            processing_delay = sensor.sar_processing_delay_s * 0.8
            t_detect = max(first_pass["start_s"], t_in) + processing_delay

            if best_detection is None or t_detect < best_detection:
                best_detection = t_detect
                best_sat_id = sat_id + 1

        if best_detection is None:
            return None

        detect_latency = best_detection - t_in
        return (ship_id, eez_name, t_in, best_detection, best_sat_id, detect_latency, "TRACKING")

    else:
        best_detection = None
        best_sat_id = None

        for sat_id in range(N_SATS):
            sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
            overlapping_passes = [
                p for p in sat_passes
                if p["start_s"] <= t_out and p["stop_s"] >= t_in
            ]

            if not overlapping_passes:
                continue

            if (sat_id % 3) != 0:
                continue

            first_pass = overlapping_passes[0]
            t_detect = max(first_pass["start_s"], t_in) + sensor.sar_processing_delay_s

            if best_detection is None or t_detect < best_detection:
                best_detection = t_detect
                best_sat_id = sat_id + 1

        if best_detection is None:
            return None

        detect_latency = best_detection - t_in
        return (ship_id, eez_name, t_in, best_detection, best_sat_id, detect_latency, "TRACKING")

# ============================================================================
# DELIVERY LATENCY
# ============================================================================

def compute_delivery_latency(sat_id: int, t_detect: float) -> Optional[Tuple]:
    """Compute downlink latency for detected satellite."""
    amd_file = DATA_DIR / "Acess_GS_Ahmedabad-To-Satellite-Walker12.csv"
    sri_file = DATA_DIR / "Acess_GS_Sriharikota-To-Satellite-Walker12.csv"

    amd = parse_blocked_access(amd_file, n_blocks=N_SATS)
    sri = parse_blocked_access(sri_file, n_blocks=N_SATS)

    sat_block = sat_id - 1
    passes = [e for e in amd + sri if e["block_id"] == sat_block]
    candidates = [p for p in passes if p["start_s"] >= t_detect]

    if not candidates:
        return None

    first_dl = min(candidates, key=lambda x: x["start_s"])
    t_down = first_dl["start_s"]
    dl_latency = t_down - t_detect

    return sat_id, t_down, dl_latency

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_phase4_patrol_vs_tracking():
    """Run Phase 4 analysis comparing patrol vs tracking modes."""

    sensor = DEFAULT_SENSOR
    results = []

    ships = [("Ship1", "EEZ_West"), ("Ship3", "EEZ_West"), ("Ship2", "EEZ_East")]

    for ship_id, eez_name in ships:
        # PATROL MODE
        patrol_result = detect_ship_patrol_mode(ship_id, eez_name, sensor)

        if patrol_result:
            _, _, t_in, t_det_p, sat_p, lat_p, _ = patrol_result
            dl_info_p = compute_delivery_latency(sat_p, t_det_p)

            if dl_info_p:
                sat_dl_p, t_down_p, dl_lat_p = dl_info_p
                results.append({
                    'ship_id': ship_id,
                    'eez': eez_name,
                    'mode': 'PATROL',
                    't_entry_s': t_in,
                    't_detect_s': t_det_p,
                    'sat_detect': sat_p,
                    'sat_downlink': sat_dl_p,
                    'detect_latency_s': lat_p,
                    'delivery_latency_s': dl_lat_p,
                    'total_latency_s': lat_p + dl_lat_p,
                    'detected': 1,
                })
        else:
            results.append({
                'ship_id': ship_id,
                'eez': eez_name,
                'mode': 'PATROL',
                't_entry_s': 0,
                't_detect_s': None,
                'sat_detect': None,
                'sat_downlink': None,
                'detect_latency_s': None,
                'delivery_latency_s': None,
                'total_latency_s': None,
                'detected': 0,
            })

        # TRACKING MODE
        tracking_result = detect_ship_tracking_mode(ship_id, eez_name, sensor)

        if tracking_result:
            _, _, t_in, t_det_t, sat_t, lat_t, _ = tracking_result
            dl_info_t = compute_delivery_latency(sat_t, t_det_t)

            if dl_info_t:
                sat_dl_t, t_down_t, dl_lat_t = dl_info_t
                results.append({
                    'ship_id': ship_id,
                    'eez': eez_name,
                    'mode': 'TRACKING',
                    't_entry_s': t_in,
                    't_detect_s': t_det_t,
                    'sat_detect': sat_t,
                    'sat_downlink': sat_dl_t,
                    'detect_latency_s': lat_t,
                    'delivery_latency_s': dl_lat_t,
                    'total_latency_s': lat_t + dl_lat_t,
                    'detected': 1,
                })
        else:
            results.append({
                'ship_id': ship_id,
                'eez': eez_name,
                'mode': 'TRACKING',
                't_entry_s': 0,
                't_detect_s': None,
                'sat_detect': None,
                'sat_downlink': None,
                'detect_latency_s': None,
                'delivery_latency_s': None,
                'total_latency_s': None,
                'detected': 0,
            })

    # Save results
    out_path = PHASE4_DIR / "Phase4_Patrol_vs_Tracking_12sat.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            'ship_id', 'eez', 'mode', 't_entry_s', 't_detect_s',
            'sat_detect', 'sat_downlink', 'detect_latency_s',
            'delivery_latency_s', 'total_latency_s', 'detected'
        ])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return results

if __name__ == "__main__":
    results = run_phase4_patrol_vs_tracking()
