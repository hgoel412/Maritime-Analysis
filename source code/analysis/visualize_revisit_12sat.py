from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
DATA_DIR = BASE_DIR / "12sat_data"
OUT_DIR = BASE_DIR / "output"

OUT_DIR.mkdir(exist_ok=True)


def main():
    lat_path = DATA_DIR / "Latencies_12sat.csv"
    df = pd.read_csv(lat_path)

    # Convert to minutes for readability
    df["detect_latency_min"] = df["detect_latency_s"] / 60.0
    df["delivery_latency_min"] = df["delivery_latency_s"] / 60.0

    # ----- Detection latency -----
    plt.figure(figsize=(6, 4))
    bars = plt.bar(df["ship_id"], df["detect_latency_min"], color="steelblue")
    plt.ylabel("Detection latency (min)")
    plt.xlabel("Ships")
    plt.title("12-sat Walker: detection latency per ship")
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
    plt.savefig(OUT_DIR / "latency_12sat_detection_per_ship.png", dpi=200)
    plt.close()

    # ----- Delivery latency -----
    plt.figure(figsize=(6, 4))
    bars = plt.bar(df["ship_id"], df["delivery_latency_min"], color="seagreen")
    plt.ylabel("Delivery latency (min)")
    plt.xlabel("Ships")
    plt.title("12-sat Walker: delivery latency per ship")
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
    plt.savefig(OUT_DIR / "latency_12sat_delivery_per_ship.png", dpi=200)
    plt.close()

    print(f"12-sat latency plots saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
