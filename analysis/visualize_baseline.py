from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output"

OUT_DIR.mkdir(exist_ok=True)


def load_data():
    lat_path = DATA_DIR / "Baseline_Latencies.csv"
    rev_path = DATA_DIR / "Baseline_Revisit.csv"

    df_lat = pd.read_csv(lat_path)
    df_rev = pd.read_csv(rev_path)

    return df_lat, df_rev


def make_latency_barplots(df_lat):
    """
    Bar plots for detection and delivery latency per ship (minutes),
    with numeric labels on each bar.
    """
    df = df_lat.copy()
    df["detect_latency_min"] = df["detect_latency_s"] / 60.0
    df["delivery_latency_min"] = df["delivery_latency_s"] / 60.0

    # ----- Detection latency -----
    plt.figure(figsize=(6, 4))
    bars = plt.bar(df["ship_id"], df["detect_latency_min"], color="steelblue")
    plt.ylabel("Detection latency (min)")
    plt.xlabel("Ships")
    plt.title("Baseline detection latency per ship")
    plt.grid(axis="y", alpha=0.3)

    for bar, val in zip(bars, df["detect_latency_min"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val:.1f} min",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(OUT_DIR / "baseline_detection_latency_per_ship.png", dpi=200)
    plt.close()

    # ----- Delivery latency -----
    plt.figure(figsize=(6, 4))
    bars = plt.bar(df["ship_id"], df["delivery_latency_min"], color="seagreen")
    plt.ylabel("Delivery latency (min)")
    plt.xlabel("Ships")
    plt.title("Baseline delivery latency per ship (no ISL, both GS)")
    plt.grid(axis="y", alpha=0.3)

    for bar, val in zip(bars, df["delivery_latency_min"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height(),
            f"{val:.1f} min",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(OUT_DIR / "baseline_delivery_latency_per_ship.png", dpi=200)
    plt.close()


def make_revisit_table(df_rev):
    """
    Convert revisit stats from seconds to minutes, save to CSV,
    and print a markdown table.
    """
    df = df_rev.copy()
    for col in ["mean_revisit_s", "median_revisit_s", "p95_revisit_s", "max_revisit_s"]:
        df[col.replace("_s", "_min")] = df[col] / 60.0

    out_csv = OUT_DIR / "baseline_revisit_minutes.csv"
    df.to_csv(out_csv, index=False)

    print("\nRevisit stats (minutes):")
    print(
        df[
            [
                "eez",
                "mean_revisit_min",
                "median_revisit_min",
                "p95_revisit_min",
                "max_revisit_min",
            ]
        ].to_markdown(index=False)
    )


def main():
    df_lat, df_rev = load_data()

    print("Baseline latencies (s):")
    print(df_lat.to_markdown(index=False))

    make_latency_barplots(df_lat)
    make_revisit_table(df_rev)

    print(f"\nPlots and tables saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
