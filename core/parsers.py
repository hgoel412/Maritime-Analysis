import csv
from datetime import datetime
from pathlib import Path
from constants import SCEN_START, TIME_FMT


def _to_seconds(t_str: str) -> float:
    """Convert STK UTCG string to seconds from scenario start."""
    t = datetime.strptime(t_str.strip(), TIME_FMT)
    return (t - SCEN_START).total_seconds()


# ---------- SHIP–EEZ PARSERS ----------

def _parse_single_ship_file(path: Path, ship_id: str):
    """Generic parser for single-ship Access_ShipX_EEZ_*.csv."""
    path = Path(path)
    intervals = []

    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        in_header = False
        for row in reader:
            if not row:
                continue
            first = row[0].strip('"')

            if first == "Access" and "Start Time" in row[1]:
                in_header = True
                continue
            if first == "Statistics":
                in_header = False
                continue
            if in_header:
                start_s = _to_seconds(row[1])
                stop_s = _to_seconds(row[2])
                dur_s = float(row[3])
                intervals.append(
                    {
                        "ship_id": ship_id,
                        "start_s": start_s,
                        "stop_s": stop_s,
                        "duration_s": dur_s,
                    }
                )

    return intervals


def parse_ship1_eez_west(path):
    """Access_Ship1_EEZ_West.csv → Ship1 interval in EEZ_West."""
    return _parse_single_ship_file(Path(path), "Ship1")


def parse_ship2_eez_generic(path, ship_id="Ship2"):
    """Access_Ship2_EEZ_*.csv → Ship2 interval."""
    return _parse_single_ship_file(Path(path), ship_id)


def parse_ship1_ship3_eez_west(path):
    """
    Parse Access_Ship1_Ship3_EEZ_West.csv.

    Block 0: Ship1
    Block 1: Ship3
    """
    path = Path(path)
    intervals = []
    block_id = -1
    in_header = False

    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            first = row[0].strip('"')

            if first == "Access" and "Start Time" in row[1]:
                block_id += 1
                in_header = True
                continue

            if first == "Statistics":
                in_header = False
                continue

            if in_header:
                start_s = _to_seconds(row[1])
                stop_s = _to_seconds(row[2])
                dur_s = float(row[3])

                if block_id == 0:
                    ship_id = "Ship1"
                elif block_id == 1:
                    ship_id = "Ship3"
                else:
                    ship_id = f"Ship_block_{block_id}"

                intervals.append(
                    {
                        "ship_id": ship_id,
                        "start_s": start_s,
                        "stop_s": stop_s,
                        "duration_s": dur_s,
                    }
                )

    return intervals


# ---------- EEZ–SAT & GS–SAT PARSER ----------

def parse_blocked_access(path, n_blocks: int):
    """
    Parse EEZ–Satellite and GS–Satellite CSVs with stacked blocks.
    """
    path = Path(path)
    entries = []
    block_id = -1
    in_header = False

    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            first = row[0].strip('"')

            if first == "Access" and "Start Time" in row[1]:
                block_id += 1
                in_header = True
                continue

            if first == "Statistics":
                in_header = False
                continue

            if in_header and 0 <= block_id < n_blocks:
                start_s = _to_seconds(row[1])
                stop_s = _to_seconds(row[2])
                dur_s = float(row[3])
                entries.append(
                    {
                        "block_id": block_id,
                        "start_s": start_s,
                        "stop_s": stop_s,
                        "duration_s": dur_s,
                    }
                )

    return entries
