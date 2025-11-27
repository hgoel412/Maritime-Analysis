from pathlib import Path
import pandas as pd

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR_6 = BASE_DIR / "data"
DATA_DIR_12 = BASE_DIR / "12sat_data"
DATA_DIR_32 = BASE_DIR / "32sat_data"
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)


def build_ship_table():
    # 6-sat baseline
    lat6 = pd.read_csv(DATA_DIR_6 / "Baseline_Latencies.csv")
    lat6["constellation"] = "6-sat"

    # 12-sat
    lat12 = pd.read_csv(DATA_DIR_12 / "Latencies_12sat.csv")
    lat12["constellation"] = "12-sat"

    # 32-sat any-sat
    lat32 = pd.read_csv(DATA_DIR_32 / "Latencies_32sat_anysat.csv")
    lat32["constellation"] = "32-sat"

    cols = [
        "constellation",
        "ship_id",
        "detect_latency_s",
        "delivery_latency_s",
    ]
    df = pd.concat([lat6[cols], lat12[cols], lat32[cols]], ignore_index=True)
    df["detect_latency_min"] = df["detect_latency_s"] / 60.0
    df["delivery_latency_min"] = df["delivery_latency_s"] / 60.0

    out = OUT_DIR / "comparison_ship_latency.csv"
    df.to_csv(out, index=False)
    print(f"Ship comparison table saved to {out}")


def build_eez_table():
    # 6-sat baseline revisit already in minutes
    rev6 = pd.read_csv(OUT_DIR / "baseline_revisit_minutes.csv")
    rev6["constellation"] = "6-sat"

    # 12-sat revisit in seconds
    rev12 = pd.read_csv(DATA_DIR_12 / "Revisit_12sat.csv")
    rev12["constellation"] = "12-sat"

    # 32-sat revisit in seconds
    rev32 = pd.read_csv(DATA_DIR_32 / "Revisit_32sat.csv")
    rev32["constellation"] = "32-sat"

    # convert 12/32 to minutes to match baseline
    for df in [rev12, rev32]:
        for col in ["mean_revisit_s", "median_revisit_s", "p95_revisit_s", "max_revisit_s"]:
            df[col.replace("_s", "_min")] = df[col] / 60.0

    cols_min = [
        "constellation",
        "eez",
        "mean_revisit_min",
        "median_revisit_min",
        "p95_revisit_min",
        "max_revisit_min",
    ]

    df_all = pd.concat(
        [rev6[cols_min], rev12[cols_min], rev32[cols_min]], ignore_index=True
    )

    out = OUT_DIR / "comparison_eez_revisit.csv"
    df_all.to_csv(out, index=False)
    print(f"EEZ comparison table saved to {out}")


def main():
    build_ship_table()
    build_eez_table()


if __name__ == "__main__":
    main()
