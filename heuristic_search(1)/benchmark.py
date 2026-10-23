"""Thực nghiệm so sánh 3 thuật toán (Chương 4).   python benchmark.py [số_mẫu]

Thiết kế thực nghiệm
- 3 họ đồ thị: knn (k-NN, trọng số Euclid), grid (lưới bỏ bớt cạnh, nhiều ngõ cụt),
  knn-rw (k-NN nhưng trọng số cạnh NGẪU NHIÊN, h không còn là cận dưới của chi phí).
- 4 cỡ: ~10, 20, 40, 80 nút. Mỗi (họ, cỡ) chạy TRIALS đồ thị khác nhau (seed 0..TRIALS-1),
  mỗi đồ thị chọn ngẫu nhiên một cặp (Start, Goal). Cả 3 thuật toán dùng CÙNG đồ thị/cặp.
- Chỉ số:
    success  tỷ lệ thành công + khoảng tin cậy 95% Wilson
    expanded số nút được xét ("Bước k"), trung bình ± độ lệch chuẩn
    time_ms  thời gian trung vị của 5 lần chạy lặp, trung bình ± độ lệch chuẩn
    ratio    chi phí / chi phí tối ưu (Dijkstra), CHỈ trên các lần thành công,
             trung bình ± khoảng tin cậy 95% (1.96*s/sqrt(n)); =1 là tối ưu
Xuất: benchmark_results.csv (UTF-8 BOM, mở được bằng Excel) và benchmark_chart.png.
"""
import csv
import math
import random
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model.algorithms import ALGORITHMS, run_to_end
from model.graph_model import Graph

SIZES = [10, 20, 40, 80]
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
FAMILIES = {
    "knn": lambda n, s: Graph.random_graph(n, seed=s),
    "grid": lambda n, s: Graph.grid_graph(n, seed=s),
    "knn-rw": lambda n, s: Graph.random_graph(n, seed=s, weights="random"),
}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h) * 100, min(1.0, c + h) * 100


def mean_sd(xs):
    if not xs:
        return float("nan"), float("nan")
    return st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)


def main():
    rows = []
    for fam, build in FAMILIES.items():
        for n in SIZES:
            agg = {a: dict(ok=0, t=[], exp=[], ratio=[]) for a in ALGORITHMS}
            for seed in range(TRIALS):
                g = build(n, seed)
                s, t = random.Random(seed).sample(g.nodes, 2)
                for a in ALGORITHMS:
                    _, r = run_to_end(g, a, s, t, reps=5, max_restarts=10, seed=seed)
                    d = agg[a]
                    d["t"].append(r.time_ms)
                    d["exp"].append(r.expanded)
                    if r.success:
                        d["ok"] += 1
                        d["ratio"].append(r.ratio)
            for a, d in agg.items():
                lo, hi = wilson(d["ok"], TRIALS)
                tm, ts = mean_sd(d["t"])
                em, es = mean_sd(d["exp"])
                rm, rs = mean_sd(d["ratio"])
                rci = 1.96 * rs / math.sqrt(len(d["ratio"])) if len(d["ratio"]) > 1 else float("nan")
                rows.append(dict(
                    family=fam, n=n, algo=a, trials=TRIALS,
                    success=round(100 * d["ok"] / TRIALS, 1),
                    success_ci_lo=round(lo, 1), success_ci_hi=round(hi, 1),
                    expanded_mean=round(em, 2), expanded_sd=round(es, 2),
                    time_ms_mean=round(tm, 4), time_ms_sd=round(ts, 4),
                    ratio_mean=round(rm, 3), ratio_sd=round(rs, 3), ratio_ci95=round(rci, 3),
                    n_success=len(d["ratio"])))
        print(f"xong họ đồ thị: {fam}", flush=True)

    with open("benchmark_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nTRIALS = {TRIALS} đồ thị / ô.  ratio = chi phí / tối ưu (chỉ các lần thành công)")
    print(f"{'họ':<7}{'N':>3} {'thuật toán':<29}{'succ% [CI95]':>20}{'nút xét':>16}"
          f"{'t(ms)':>16}{'ratio':>16}")
    for r in rows:
        print(f"{r['family']:<7}{r['n']:>3} {r['algo']:<29}"
              f"{r['success']:>7} [{r['success_ci_lo']:>5},{r['success_ci_hi']:>5}]"
              f"{r['expanded_mean']:>9}±{r['expanded_sd']:<6}"
              f"{r['time_ms_mean']:>9}±{r['time_ms_sd']:<6}"
              f"{r['ratio_mean']:>8}±{r['ratio_ci95']:<6}")

    fams = list(FAMILIES)
    fig, axs = plt.subplots(len(fams), 3, figsize=(16, 3.8 * len(fams)))
    colors = ["#1e88e5", "#ef5350", "#66bb6a"]
    width = 0.26
    for ri, fam in enumerate(fams):
        for ci, (key, title) in enumerate([("success", "Tỷ lệ thành công (%)"),
                                           ("expanded_mean", "Số nút xét (TB ± SD)"),
                                           ("ratio_mean", "Chi phí / tối ưu (TB ± CI95)")]):
            ax = axs[ri][ci]
            for i, a in enumerate(ALGORITHMS):
                sel = [next(r for r in rows if r["family"] == fam and r["n"] == n
                            and r["algo"] == a) for n in SIZES]
                vals = [r[key] for r in sel]
                if key == "success":
                    err = [[r["success"] - r["success_ci_lo"] for r in sel],
                           [r["success_ci_hi"] - r["success"] for r in sel]]
                elif key == "expanded_mean":
                    err = [r["expanded_sd"] for r in sel]
                else:
                    err = [0 if math.isnan(r["ratio_ci95"]) else r["ratio_ci95"] for r in sel]
                ax.bar([j + i * width for j in range(len(SIZES))], vals, width,
                       yerr=err, capsize=2, label=a, color=colors[i])
            ax.set_xticks([j + width for j in range(len(SIZES))])
            ax.set_xticklabels([f"N≈{n}" for n in SIZES])
            ax.set_title(f"[{fam}] {title}", fontsize=10)
            ax.grid(axis="y", alpha=0.3)
            if key == "ratio_mean":
                ax.axhline(1, color="k", lw=0.8, ls="--")
    h, l = axs[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, fontsize=9, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig("benchmark_chart.png", dpi=130)
    print("\nĐã lưu benchmark_results.csv và benchmark_chart.png")


if __name__ == "__main__":
    main()
