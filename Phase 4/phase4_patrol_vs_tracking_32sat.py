"""Phase 4: 32-sat Patrol vs Tracking Analysis"""
from pathlib import Path
import csv
from typing import List, Dict, Tuple, Optional
from parsers import (
    parse_ship1_eez_west,
    parse_ship2_eez_generic,
    parse_ship1_ship3_eez_west,
    parse_blocked_access,
)
from phase4_sensor_params import DEFAULT_SENSOR

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR_32 = BASE_DIR / "32sat_data"
PHASE4_DIR = BASE_DIR / "phase4_analysis"
PHASE4_DIR.mkdir(exist_ok=True)

N_SATS = 32

def get_ship_intervals(ship_id: str, eez_name: str) -> List[Dict]:
    """Get ship EEZ intervals."""
    if ship_id in ["Ship1", "Ship3"] and eez_name != "EEZ_West":
        raise ValueError(f"{ship_id} only in EEZ_West")
    if ship_id == "Ship2" and eez_name != "EEZ_East":
        raise ValueError("Ship2 only in EEZ_East")

    if ship_id == "Ship1":
        path = DATA_DIR_32 / "Access_Ship1_EEZ_West.csv"
        return parse_ship1_eez_west(path)
    elif ship_id == "Ship3":
        path = DATA_DIR_32 / "Access_Ship1_Ship3_EEZ_West.csv"
        all_ints = parse_ship1_ship3_eez_west(path)
        return [x for x in all_ints if x["ship_id"] == "Ship3"]
    elif ship_id == "Ship2":
        path = DATA_DIR_32 / "Access_Ship2_EEZ_East.csv"
        return parse_ship2_eez_generic(path, ship_id="Ship2")

    raise ValueError(f"Unknown ship: {ship_id}")

def get_eez_sat_passes(eez_name: str) -> List[Dict]:
    """Get satellite passes over EEZ."""
    if eez_name == "EEZ_West":
        eez_file = DATA_DIR_32 / "Acess_EEZ_West-To-Satellite-Walker32.csv"
    elif eez_name == "EEZ_East":
        eez_file = DATA_DIR_32 / "Acess_EEZ_East-To-Satellite-Walker32.csv"
    else:
        raise ValueError(f"Unknown EEZ: {eez_name}")
    return parse_blocked_access(eez_file, n_blocks=N_SATS)

def ship_on_known_route(ship_id: str) -> bool:
    return ship_id in ["Ship1", "Ship2"]

def detect_ship_patrol_mode(ship_id: str, eez_name: str, sensor) -> Optional[Tuple]:
    """PATROL MODE for 32-sat."""
    ship_ints = get_ship_intervals(ship_id, eez_name)
    if not ship_ints:
        return None

    ship_int = ship_ints[0]
    t_in, t_out = ship_int["start_s"], ship_int["stop_s"]
    eez_passes = get_eez_sat_passes(eez_name)

    best_detection, best_sat_id = None, None
    for sat_id in range(N_SATS):
        sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
        overlapping = [p for p in sat_passes if p["start_s"] <= t_out and p["stop_s"] >= t_in]

        if not overlapping:
            continue

        first_pass = min(overlapping, key=lambda x: x["start_s"])
        t_detect = max(first_pass["start_s"], t_in) + sensor.sar_processing_delay_s

        if best_detection is None or t_detect < best_detection:
            best_detection = t_detect
            best_sat_id = sat_id + 1

    if best_detection is None:
        return None
    return (ship_id, eez_name, t_in, best_detection, best_sat_id, best_detection - t_in, "PATROL")

def detect_ship_tracking_mode(ship_id: str, eez_name: str, sensor) -> Optional[Tuple]:
    """TRACKING MODE for 32-sat."""
    ship_ints = get_ship_intervals(ship_id, eez_name)
    if not ship_ints:
        return None

    ship_int = ship_ints[0]
    t_in, t_out = ship_int["start_s"], ship_int["stop_s"]
    on_route = ship_on_known_route(ship_id)
    eez_passes = get_eez_sat_passes(eez_name)

    if on_route:
        best_detection, best_sat_id = None, None
        for sat_id in range(N_SATS):
            sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
            overlapping = [p for p in sat_passes if p["start_s"] <= t_out and p["stop_s"] >= t_in]

            if not overlapping:
                continue

            first_pass = min(overlapping, key=lambda x: x["start_s"])
            processing_delay = sensor.sar_processing_delay_s * 0.8
            t_detect = max(first_pass["start_s"], t_in) + processing_delay

            if best_detection is None or t_detect < best_detection:
                best_detection = t_detect
                best_sat_id = sat_id + 1

        if best_detection is None:
            return None
        return (ship_id, eez_name, t_in, best_detection, best_sat_id, best_detection - t_in, "TRACKING")
    else:
        best_detection, best_sat_id = None, None
        for sat_id in range(N_SATS):
            sat_passes = [e for e in eez_passes if e["block_id"] == sat_id]
            overlapping = [p for p in sat_passes if p["start_s"] <= t_out and p["stop_s"] >= t_in]

            if not overlapping or (sat_id % 3) != 0:
                continue

            first_pass = overlapping[0]
            t_detect = max(first_pass["start_s"], t_in) + sensor.sar_processing_delay_s

            if best_detection is None or t_detect < best_detection:
                best_detection = t_detect
                best_sat_id = sat_id + 1

        if best_detection is None:
            return None
        return (ship_id, eez_name, t_in, best_detection, best_sat_id, best_detection - t_in, "TRACKING")

def compute_delivery_latency_any_sat(t_detect: float) -> Optional[Tuple]:
    """Earliest downlink on ANY satellite (32-sat networked delivery)."""
    amd_file = DATA_DIR_32 / "Acess_GS_Ahmedabad-To-Satellite-Walker32.csv"
    sri_file = DATA_DIR_32 / "Acess_GS_Sriharikota-To-Satellite-Walker32.csv"

    amd = parse_blocked_access(amd_file, n_blocks=N_SATS)
    sri = parse_blocked_access(sri_file, n_blocks=N_SATS)
    passes = amd + sri

    candidates = [p for p in passes if p["start_s"] >= t_detect]
    if not candidates:
        return None

    first_dl = min(candidates, key=lambda x: x["start_s"])
    return first_dl["block_id"] + 1, first_dl["start_s"], first_dl["start_s"] - t_detect

def run_phase4_32sat():
    """Run Phase 4 for 32-sat constellation."""
    sensor = DEFAULT_SENSOR
    results = []

    ships = [("Ship1", "EEZ_West"), ("Ship3", "EEZ_West"), ("Ship2", "EEZ_East")]

    for ship_id, eez_name in ships:
        for mode_func, mode_name in [
            (detect_ship_patrol_mode, "PATROL"),
            (detect_ship_tracking_mode, "TRACKING")
        ]:
            result = mode_func(ship_id, eez_name, sensor)

            if result:
                _, _, t_in, t_det, sat_detect, lat, _ = result
                dl_info = compute_delivery_latency_any_sat(t_det)

                if dl_info:
                    sat_dl, t_down, dl_lat = dl_info
                    results.append({
                        'ship_id': ship_id,
                        'eez': eez_name,
                        'mode': mode_name,
                        't_entry_s': t_in,
                        't_detect_s': t_det,
                        'sat_detect': sat_detect,
                        'sat_downlink': sat_dl,
                        'detect_latency_s': lat,
                        'delivery_latency_s': dl_lat,
                        'total_latency_s': lat + dl_lat,
                        'detected': 1,
                    })
            else:
                results.append({
                    'ship_id': ship_id,
                    'eez': eez_name,
                    'mode': mode_name,
                    't_entry_s': 0,
                    't_detect_s': None,
                    'sat_detect': None,
                    'sat_downlink': None,
                    'detect_latency_s': None,
                    'delivery_latency_s': None,
                    'total_latency_s': None,
                    'detected': 0,
                })

    out_path = PHASE4_DIR / "Phase4_Patrol_vs_Tracking_32sat.csv"
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
    results = run_phase4_32sat()
