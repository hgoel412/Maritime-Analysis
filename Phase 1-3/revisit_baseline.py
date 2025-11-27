from pathlib import Path
import csv
from parsers import parse_blocked_access

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "data"

N_SATS = 6


def compute_revisit_from_csv(eez_name: str, csv_file: Path):
    """
    Compute revisit statistics for an EEZ from its EEZ–All Satellite CSV.

    Approach:
      - Parse all access intervals for all 6 satellites.
      - Merge into a single list sorted by start time.
      - Gaps between successive intervals (prev.stop -> next.start) are revisit times.
    Returns dict with mean, median, p95, max gap (seconds).
    """
    entries = parse_blocked_access(csv_file, n_blocks=N_SATS)

    if not entries:
        print(f"No entries found in {csv_file}")
        return None

    # Sort by start time
    entries_sorted = sorted(entries, key=lambda x: x["start_s"])

    # Compute gaps between consecutive intervals (only positive gaps)
    gaps = []
    prev_stop = entries_sorted[0]["stop_s"]
    for e in entries_sorted[1:]:
        gap = e["start_s"] - prev_stop
        if gap > 0:
            gaps.append(gap)
        # update prev_stop to the later of the two stops to handle overlaps
        prev_stop = max(prev_stop, e["stop_s"])

    if not gaps:
        print(f"No positive gaps (continuous coverage) for {eez_name}")
        return {
            "eez": eez_name,
            "mean_revisit_s": 0.0,
            "median_revisit_s": 0.0,
            "p95_revisit_s": 0.0,
            "max_revisit_s": 0.0,
        }

    gaps_sorted = sorted(gaps)
    n = len(gaps_sorted)

    def percentile(p):
        idx = int(round((p / 100.0) * (n - 1)))
        return gaps_sorted[idx]

    mean_gap = sum(gaps_sorted) / n
    median_gap = percentile(50)
    p95_gap = percentile(95)
    max_gap = max(gaps_sorted)

    print(f"=== {eez_name} revisit stats (6-sat baseline) ===")
    print(f"Mean gap   (s): {mean_gap:.1f}")
    print(f"Median gap (s): {median_gap:.1f}")
    print(f"95% gap    (s): {p95_gap:.1f}")
    print(f"Max gap    (s): {max_gap:.1f}")

    return {
        "eez": eez_name,
        "mean_revisit_s": mean_gap,
        "median_revisit_s": median_gap,
        "p95_revisit_s": p95_gap,
        "max_revisit_s": max_gap,
    }


def run_revisit_baseline():
    """
    Compute revisit statistics for EEZ_West and EEZ_East
    and save to Baseline_Revisit.csv
    """
    results = []

    west_file = DATA_DIR / "Acces_EEZ_West_All Satellite.csv"
    east_file = DATA_DIR / "Acces_EEZ_East_All Satellite.csv"

    west_stats = compute_revisit_from_csv("EEZ_West", west_file)
    if west_stats:
        results.append(west_stats)

    east_stats = compute_revisit_from_csv("EEZ_East", east_file)
    if east_stats:
        results.append(east_stats)

    out_path = DATA_DIR / "Baseline_Revisit.csv"
    if results:
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "eez",
                    "mean_revisit_s",
                    "median_revisit_s",
                    "p95_revisit_s",
                    "max_revisit_s",
                ],
            )
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"\nBaseline revisit stats saved to: {out_path}")
    else:
        print("No revisit stats computed; Baseline_Revisit.csv not written.")


if __name__ == "__main__":
    run_revisit_baseline()
