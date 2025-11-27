from pathlib import Path
import csv
from parsers import (
    parse_ship1_eez_west,
    parse_ship2_eez_generic,
    parse_ship1_ship3_eez_west,
    parse_blocked_access,
)

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "data"

N_SATS = 6  # 6-satellite baseline constellation


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
        # simple one-ship file
        path = DATA_DIR / "Access_Ship1_EEZ_West.csv"
        return parse_ship1_eez_west(path)

    if ship_id == "Ship3":
        # second block in the combined file
        path = DATA_DIR / "Access_Ship1_Ship3_EEZ_West.csv"
        all_ints = parse_ship1_ship3_eez_west(path)
        return [x for x in all_ints if x["ship_id"] == "Ship3"]

    if ship_id == "Ship2":
        # Ship2 in EEZ_East; reuse generic single-ship parser
        path = DATA_DIR / "Access_Ship2_EEZ_East.csv"
        return parse_ship2_eez_generic(path, ship_id="Ship2")

    raise ValueError(f"Unknown ship_id: {ship_id}")


def compute_ship_detection_latency(ship_id: str, eez_name: str):
    """
    Compute detection latency for a given ship and EEZ.

    Returns:
        (ship_id, eez_name, t_entry_s, t_detect_s, sat_id, detect_latency_s)
        or None if no detection occurs.
    """
    ship_intervals = get_ship_intervals(ship_id, eez_name)
    if not ship_intervals:
        print(f"No {ship_id} intervals found for {eez_name}.")
        return None

    # assume one interval per ship/EEZ
    ship_int = ship_intervals[0]
    t_in = ship_int["start_s"]
    t_out = ship_int["stop_s"]

    # choose correct EEZ–satellite file
    if eez_name == "EEZ_West":
        eez_file = DATA_DIR / "Acces_EEZ_West_All Satellite.csv"
    elif eez_name == "EEZ_East":
        eez_file = DATA_DIR / "Acces_EEZ_East_All Satellite.csv"
    else:
        raise ValueError(f"Unknown EEZ {eez_name}")

    eez_sat = parse_blocked_access(eez_file, n_blocks=N_SATS)

    best_t = None
    best_sat = None

    # For each satellite, find first pass while ship is inside EEZ
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
            best_sat = sat_block + 1  # 1..N_SATS

    if best_t is None:
        print(f"{ship_id} in {eez_name}: no detection by any satellite.")
        return None

    det_latency = best_t - t_in
    print(f"=== {ship_id} detection in {eez_name} ===")
    print(f"Entry time  (s since start): {t_in:.1f}")
    print(f"Detect time (s since start): {best_t:.1f}")
    print(f"Satellite index           : {best_sat}")
    print(f"Detection latency (s)     : {det_latency:.1f}")

    return ship_id, eez_name, t_in, best_t, best_sat, det_latency


def compute_delivery_latency_no_isl(sat_id: int, t_detect: float):
    """
    Earliest downlink after detection time t_detect for given satellite.
    Uses both GS_Ahmedabad and GS_Sriharikota access files.
    """
    amd_file = DATA_DIR / "Acces_GS_Ahmedabad_All Satellite.csv"
    sri_file = DATA_DIR / "Acces_GS_Sriharikota_All Satellite.csv"

    amd = parse_blocked_access(amd_file, n_blocks=N_SATS)
    sri = parse_blocked_access(sri_file, n_blocks=N_SATS)

    sat_block = sat_id - 1
    passes = [e for e in amd + sri if e["block_id"] == sat_block]

    candidates = [p for p in passes if p["start_s"] >= t_detect]
    if not candidates:
        print(f"No downlink after detection for sat {sat_id}.")
        return None

    first_dl = min(candidates, key=lambda x: x["start_s"])
    t_down = first_dl["start_s"]
    dl_latency = t_down - t_detect

    print("=== Delivery latency (no ISL) ===")
    print(f"Satellite index       : {sat_id}")
    print(f"Detection time (s)    : {t_detect:.1f}")
    print(f"Downlink start (s)    : {t_down:.1f}")
    print(f"Delivery latency (s)  : {dl_latency:.1f}")

    return t_down, dl_latency


def run_baseline():
    """
    Compute detection + delivery latency for:
      - Ship1, Ship3 in EEZ_West
      - Ship2 in EEZ_East
    and save summary to Baseline_Latencies.csv.
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
        ship_id, eez_name, t_in, t_det, sat_id, det_lat = det_info

        dl_info = compute_delivery_latency_no_isl(sat_id, t_det)
        if dl_info is None:
            continue
        t_down, dl_lat = dl_info

        results.append(
            {
                "ship_id": ship_id,
                "eez": eez_name,
                "t_entry_s": t_in,
                "t_detect_s": t_det,
                "sat_id": sat_id,
                "detect_latency_s": det_lat,
                "t_downlink_s": t_down,
                "delivery_latency_s": dl_lat,
            }
        )

    out_path = DATA_DIR / "Baseline_Latencies.csv"
    if results:
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ship_id",
                    "eez",
                    "t_entry_s",
                    "t_detect_s",
                    "sat_id",
                    "detect_latency_s",
                    "t_downlink_s",
                    "delivery_latency_s",
                ],
            )
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"\nBaseline latencies saved to: {out_path}")
    else:
        print("No results computed; Baseline_Latencies.csv not written.")


if __name__ == "__main__":
    run_baseline()
