from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)


def plot_ship_latency():
    df = pd.read_csv(OUT_DIR / "comparison_ship_latency.csv")

    # Detection latency per ship vs constellation
    for metric, ylabel, fname in [
        ("detect_latency_min", "Detection latency (min)", "compare_detect_latency.png"),
        ("delivery_latency_min", "Delivery latency (min)", "compare_delivery_latency.png"),
    ]:
        plt.figure(figsize=(7, 4))

        # One group per ship, bars for 6 / 12 / 32 sats
        ships = sorted(df["ship_id"].unique())
        consts = ["6-sat", "12-sat", "32-sat"]
        x = range(len(ships))
        width = 0.25

        for i, c in enumerate(consts):
            vals = [
                df[(df["ship_id"] == s) & (df["constellation"] == c)][metric].iloc[0]
                for s in ships
            ]
            xs = [xx + (i - 1) * width for xx in x]
            bars = plt.bar(xs, vals, width=width, label=c)
            for bar, val in zip(bars, vals):
                plt.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height(),
                    f"{val:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        plt.xticks(x, ships)
        plt.ylabel(ylabel)
        plt.xlabel("Ships")
        plt.title(f"{ylabel} vs constellation size")
        plt.grid(axis="y", alpha=0.3)
        plt.legend(title="Constellation")
        plt.tight_layout()
        plt.savefig(OUT_DIR / fname, dpi=200)
        plt.close()


def plot_eez_revisit():
    df = pd.read_csv(OUT_DIR / "comparison_eez_revisit.csv")

    consts = ["6-sat", "12-sat", "32-sat"]

    # Line plots: x = number of sats, y = metric, separate line per EEZ
    sats_map = {"6-sat": 6, "12-sat": 12, "32-sat": 32}
    x_vals = [6, 12, 32]

    for metric, ylabel, fname in [
        ("mean_revisit_min", "Mean revisit gap (min)", "compare_revisit_mean.png"),
        ("p95_revisit_min", "95% revisit gap (min)", "compare_revisit_p95.png"),
        ("max_revisit_min", "Max revisit gap (min)", "compare_revisit_max.png"),
    ]:
        plt.figure(figsize=(6, 4))

        for eez in ["EEZ_West", "EEZ_East"]:
            y = [
                df[(df["eez"] == eez) & (df["constellation"] == c)][metric].iloc[0]
                for c in consts
            ]
            plt.plot(x_vals, y, marker="o", label=eez)
            for xv, yv in zip(x_vals, y):
                plt.text(xv, yv, f"{yv:.1f}", ha="center", va="bottom", fontsize=8)

        plt.xticks(x_vals, x_vals)
        plt.xlabel("Number of satellites")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} vs constellation size")
        plt.grid(True, alpha=0.3)
        plt.legend(title="EEZ")
        plt.tight_layout()
        plt.savefig(OUT_DIR / fname, dpi=200)
        plt.close()


def main():
    plot_ship_latency()
    plot_eez_revisit()
    print(f"Comparison plots saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
