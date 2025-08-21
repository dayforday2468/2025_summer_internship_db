import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3


def _merge_make_pct(original_path_df, simplified_path_df):
    key = ["ORIGZONENO", "DESTZONENO", "INDEX"]
    cols = key + ["LENGTH", "T0", "TCUR"]

    o = original_path_df[cols].copy()
    s = simplified_path_df[cols].copy()
    df = o.merge(s, on=key, suffixes=("_orig", "_simp"), how="inner")

    # 에러 퍼센트 계산
    df["pct_length"] = (df["LENGTH_simp"] - df["LENGTH_orig"]) / df["LENGTH_orig"]
    df["pct_t0"] = (df["T0_simp"] - df["T0_orig"]) / df["T0_orig"]
    df["pct_tcur"] = (df["TCUR_simp"] - df["TCUR_orig"]) / df["TCUR_orig"]

    return df


def path_statistic(original_path_df, simplified_path_df):
    df = _merge_make_pct(original_path_df, simplified_path_df)

    metrics = ["pct_length", "pct_t0", "pct_tcur"]
    rows = []
    for col in metrics:
        ser = df[col].to_numpy()
        n = ser.size

        mean = ser.mean()
        var = ser.var(ddof=1) if n > 1 else float("nan")
        std = ser.std(ddof=1) if n > 1 else float("nan")
        mean_abs = np.abs(ser).mean()
        median_abs = np.median(np.abs(ser))
        rmse = np.sqrt((ser**2).mean())
        q5, q50, q95 = np.quantile(ser, [0.05, 0.50, 0.95])
        minv, maxv = ser.min(), ser.max()
        frac_out = (np.abs(ser) > 1).mean()

        rows.append(
            {
                "metric": col,
                "n": n,
                "mean": mean,
                "var": var,
                "std": std,
                "mean_abs": mean_abs,
                "median_abs": median_abs,
                "rmse": rmse,
                "p5": q5,
                "p50": q50,
                "p95": q95,
                "min": minv,
                "max": maxv,
                "frac_|err|>1": frac_out,
            }
        )

    summary = pd.DataFrame(rows).set_index("metric")
    print("=== Error percentage summary (simp − orig, normalized by orig) ===")
    print(summary.to_string(float_format=lambda x: f"{x: .6f}"))


def plot_path_error(original_path_df, simplified_path_df):
    df = _merge_make_pct(original_path_df, simplified_path_df)

    pairs = [
        ("LENGTH_orig", "pct_length", "(LENGTH_sim-LENGTH_orig)/LENGTH_orig"),
        ("T0_orig", "pct_t0", "(T0_sim-T0_orig)/T0_orig"),
        ("TCUR_orig", "pct_tcur", "(TCUR_sim-TCUR_orig)/TCUR_orig"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    for ax, (xcol, ycol, title) in zip(axes, pairs):
        x = df[xcol].to_numpy()
        y = df[ycol].to_numpy()
        ax.scatter(x, y, s=8, alpha=0.25)
        ax.axhline(0, color="k", linewidth=1)
        ax.set_xlabel(xcol)
        ax.set_ylabel(title)
        ax.set_ylim(-1, 4)
        ax.grid(True, linestyle=":", linewidth=0.7)

    plt.tight_layout()
    plt.show()


def path_similiarity():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "pathdata")
    original_path = os.path.join(data_dir, "original_paths.csv")
    simplified_path = os.path.join(data_dir, "simplified_paths.csv")

    # CSV 로드
    original_path_df = pd.read_csv(original_path)
    simplified_path_df = pd.read_csv(simplified_path)

    plot_path_error(original_path_df, simplified_path_df)
    path_statistic(original_path_df, simplified_path_df)


if __name__ == "__main__":
    path_similiarity()
