from pathlib import Path
import csv
from parsers import (
    parse_ship1_eez_west,
    parse_ship2_eez_generic,
    parse_ship1_ship3_eez_west,
    parse_blocked_access,
)

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "32sat_data"

N_SATS = 32  # 32-satellite Walker constellation


def get_ship_intervals(ship_id: str, eez_name: str):
    """
    Map ships to EEZs and CSVs:

      - Ship1 & Ship3 → EEZ_West
      - Ship2         → EEZ_East
    """
    if ship_id in ["Ship1", "Ship3"] and eez_name != "EEZ_West":
        raise ValueError(f"{ship_id} only defined for EEZ_West")

    if ship_id == "Ship2" and eez_name != "EEZ_East":
        raise ValueError("Ship2 only defined for EEZ_East")

    if ship_id == "Ship1":
        path = DATA_DIR / "Access_Ship1_EEZ_West.csv"
        return parse_ship1_eez_west(path)

    if ship_id == "Ship3":
        path = DATA_DIR / "Access_Ship1_Ship3_EEZ_West.csv"
        all_ints = parse_ship1_ship3_eez_west(path)
        return [x for x in all_ints if x["ship_id"] == "Ship3"]

    if ship_id == "Ship2":
        path = DATA_DIR / "Access_Ship2_EEZ_East.csv"
        return parse_ship2_eez_generic(path, ship_id="Ship2")

    raise ValueError(f"Unknown ship_id: {ship_id}")


def compute_ship_detection_latency(ship_id: str, eez_name: str):
    """
    Detection latency for a given ship and EEZ in 32-sat case.

    Returns:
        (ship_id, eez_name, t_entry_s, t_detect_s, sat_id_detect, detect_latency_s)
    """
    ship_intervals = get_ship_intervals(ship_id, eez_name)
    if not ship_intervals:
        print(f"No {ship_id} intervals found for {eez_name}.")
        return None

    ship_int = ship_intervals[0]
    t_in = ship_int["start_s"]
    t_out = ship_int["stop_s"]

    if eez_name == "EEZ_West":
        eez_file = DATA_DIR / "Acess_EEZ_West-To-Satellite-Walker32.csv"
    elif eez_name == "EEZ_East":
        eez_file = DATA_DIR / "Acess_EEZ_East-To-Satellite-Walker32.csv"
    else:
        raise ValueError(f"Unknown EEZ {eez_name}")

    eez_sat = parse_blocked_access(eez_file, n_blocks=N_SATS)

    best_t = None
    best_sat = None

    for sat_block in range(N_SATS):
        sat_passes = [
            e
            for e in eez_sat
            if e["block_id"] == sat_block and t_in <= e["start_s"] <= t_out
        ]
        if not sat_passes:
            continue
        first_pass = min(sat_passes, key=lambda x: x["start_s"])
        if best_t is None or first_pass["start_s"] < best_t:
            best_t = first_pass["start_s"]
            best_sat = sat_block + 1

    if best_t is None:
        print(f"{ship_id} in {eez_name}: no detection by any satellite.")
        return None

    det_latency = best_t - t_in
    print(f"=== {ship_id} detection in {eez_name} (32-sat) ===")
    print(f"Entry time  (s since start): {t_in:.1f}")
    print(f"Detect time (s since start): {best_t:.1f}")
    print(f"Detecting satellite index : {best_sat}")
    print(f"Detection latency (s)     : {det_latency:.1f}")

    return ship_id, eez_name, t_in, best_t, best_sat, det_latency


def compute_delivery_latency_any_sat(t_detect: float):
    """
    Earliest GS downlink on ANY satellite after detection time t_detect.
    """
    amd_file = DATA_DIR / "Acess_GS_Ahmedabad-To-Satellite-Walker32.csv"
    sri_file = DATA_DIR / "Acess_GS_Sriharikota-To-Satellite-Walker32.csv"

    amd = parse_blocked_access(amd_file, n_blocks=N_SATS)
    sri = parse_blocked_access(sri_file, n_blocks=N_SATS)

    passes = amd + sri

    candidates = [p for p in passes if p["start_s"] >= t_detect]
    if not candidates:
        print(f"No downlink after detection time {t_detect:.1f}.")
        return None

    first_dl = min(candidates, key=lambda x: x["start_s"])
    t_down = first_dl["start_s"]
    dl_latency = t_down - t_detect
    sat_dl_id = first_dl["block_id"] + 1

    print("=== Delivery latency (any satellite, 32-sat) ===")
    print(f"Chosen downlink satellite : {sat_dl_id}")
    print(f"Detection time (s)        : {t_detect:.1f}")
    print(f"Downlink start (s)        : {t_down:.1f}")
    print(f"Delivery latency (s)      : {dl_latency:.1f}")

    return sat_dl_id, t_down, dl_latency


def run_32sat():
    """
    Ship1, Ship3 in EEZ_West; Ship2 in EEZ_East, 32-sat constellation.
    Detection on one satellite, delivery via earliest downlink on any satellite.
    """
    results = []

    for ship_id, eez_name in [
        ("Ship1", "EEZ_West"),
        ("Ship3", "EEZ_West"),
        ("Ship2", "EEZ_East"),
    ]:
        det_info = compute_ship_detection_latency(ship_id, eez_name)
        if det_info is None:
            continue
        ship_id, eez_name, t_in, t_det, sat_id_detect, det_lat = det_info

        dl_info = compute_delivery_latency_any_sat(t_det)
        if dl_info is None:
            continue
        sat_id_down, t_down, dl_lat = dl_info

        results.append(
            {
                "ship_id": ship_id,
                "eez": eez_name,
                "t_entry_s": t_in,
                "t_detect_s": t_det,
                "sat_id_detect": sat_id_detect,
                "sat_id_downlink": sat_id_down,
                "detect_latency_s": det_lat,
                "t_downlink_s": t_down,
                "delivery_latency_s": dl_lat,
            }
        )

    out_path = DATA_DIR / "Latencies_32sat_anysat.csv"
