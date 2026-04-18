"""
utils.py — export, visualisation, and pretty-print helpers.
"""
import json
import csv
import os
from datetime import datetime
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")   # headless — safe for Flask and CLI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from models import ScheduleResult, Assignment


# ─── Export ──────────────────────────────────────────────────────────────────

def export_json(result: ScheduleResult, path: str) -> str:
    with open(path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    return path


def export_csv(result: ScheduleResult, path: str) -> str:
    rows = [a.to_dict() for a in result.assignments]
    if not rows:
        return path
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def export_comparison_csv(results: Dict[str, ScheduleResult], path: str) -> str:
    rows = []
    for method, result in results.items():
        for a in result.assignments:
            row = a.to_dict()
            row["method"] = method
            rows.append(row)
    if not rows:
        return path
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


# ─── Visualisation ───────────────────────────────────────────────────────────

PALETTE = {
    "optimized": "#00c9a7",
    "naive": "#ff6b6b",
    "bg": "#0d1117",
    "fg": "#e6edf3",
    "grid": "#21262d",
    "accent": "#58a6ff",
}


def _apply_dark_style():
    plt.rcParams.update({
        "figure.facecolor": PALETTE["bg"],
        "axes.facecolor": PALETTE["bg"],
        "axes.edgecolor": PALETTE["grid"],
        "axes.labelcolor": PALETTE["fg"],
        "xtick.color": PALETTE["fg"],
        "ytick.color": PALETTE["fg"],
        "text.color": PALETTE["fg"],
        "grid.color": PALETTE["grid"],
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "font.family": "monospace",
    })


def plot_cost_breakdown(results: Dict[str, ScheduleResult], save_path: str) -> str:
    """Bar chart: cost component breakdown per method."""
    _apply_dark_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Cost Breakdown: Naive vs Optimised", fontsize=14, color=PALETTE["fg"], y=1.01)

    for ax, (method, result) in zip(axes, results.items()):
        if not result.assignments:
            continue
        task_names = [a.task.name for a in result.assignments]
        time_costs = [a.time_cost for a in result.assignments]
        risk_penalties = [a.risk_penalty for a in result.assignments]
        load_penalties = [a.load_penalty for a in result.assignments]

        x = np.arange(len(task_names))
        w = 0.6
        bars1 = ax.bar(x, time_costs, w, label="Time Cost", color=PALETTE["accent"], alpha=0.85)
        bars2 = ax.bar(x, risk_penalties, w, bottom=time_costs, label="Risk Penalty", color="#f78166", alpha=0.85)
        bottom2 = [t + r for t, r in zip(time_costs, risk_penalties)]
        bars3 = ax.bar(x, load_penalties, w, bottom=bottom2, label="Load Penalty", color="#d2a8ff", alpha=0.85)

        ax.set_xticks(x)
        ax.set_xticklabels(task_names, rotation=45, ha="right", fontsize=8)
        ax.set_title(f"{method.upper()}  (Total: {result.total_cost:.2f})", color=PALETTE["fg"])
        ax.set_ylabel("Cost")
        ax.legend(facecolor=PALETTE["bg"], edgecolor=PALETTE["grid"], labelcolor=PALETTE["fg"])
        ax.grid(axis="y")

    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=PALETTE["bg"])
    plt.close()
    return save_path


def plot_server_utilisation(results: Dict[str, ScheduleResult], save_path: str) -> str:
    """Grouped bar chart of per-server utilisation."""
    _apply_dark_style()

    def server_loads(result: ScheduleResult):
        loads: dict = {}
        for a in result.assignments:
            loads[a.server.name] = loads.get(a.server.name, 0) + a.task.workload
        return loads

    naive_loads = server_loads(results.get("naive", ScheduleResult([], 0, "", "naive")))
    opt_loads = server_loads(results.get("optimized", ScheduleResult([], 0, "", "optimized")))
    server_names = sorted(set(list(naive_loads.keys()) + list(opt_loads.keys())))

    x = np.arange(len(server_names))
    w = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w / 2, [naive_loads.get(s, 0) for s in server_names], w,
           label="Naive", color=PALETTE["naive"], alpha=0.85)
    ax.bar(x + w / 2, [opt_loads.get(s, 0) for s in server_names], w,
           label="Optimised", color=PALETTE["optimized"], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(server_names)
    ax.set_ylabel("Total Workload Assigned")
    ax.set_title("Server Load Distribution", color=PALETTE["fg"])
    ax.legend(facecolor=PALETTE["bg"], edgecolor=PALETTE["grid"], labelcolor=PALETTE["fg"])
    ax.grid(axis="y")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=PALETTE["bg"])
    plt.close()
    return save_path


def plot_total_cost_comparison(results: Dict[str, ScheduleResult], save_path: str) -> str:
    """Simple comparison bar of total costs."""
    _apply_dark_style()
    methods = list(results.keys())
    costs = [results[m].total_cost for m in methods]
    colors = [PALETTE.get(m, PALETTE["accent"]) for m in methods]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(methods, costs, color=colors, alpha=0.9, width=0.4)
    for bar, cost in zip(bars, costs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{cost:.2f}", ha="center", va="bottom", color=PALETTE["fg"], fontsize=10)
    ax.set_ylabel("Total Cost")
    ax.set_title("Total Cost: Naive vs Optimised", color=PALETTE["fg"])
    ax.grid(axis="y")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=PALETTE["bg"])
    plt.close()
    return save_path


def plot_risk_heatmap(results: Dict[str, ScheduleResult], save_path: str) -> str:
    """Heatmap of risk penalty per task × server combination."""
    _apply_dark_style()
    result = results.get("optimized") or list(results.values())[0]
    if not result.assignments:
        return save_path

    task_names = [a.task.name for a in result.assignments]
    server_names = list({a.server.name for a in result.assignments})
    matrix = np.zeros((len(task_names), len(server_names)))

    for row_i, a in enumerate(result.assignments):
        col_j = server_names.index(a.server.name)
        matrix[row_i, col_j] = a.risk_penalty

    fig, ax = plt.subplots(figsize=(max(6, len(server_names) * 1.5), max(4, len(task_names) * 0.7)))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(len(server_names)))
    ax.set_xticklabels(server_names, rotation=45, ha="right")
    ax.set_yticks(range(len(task_names)))
    ax.set_yticklabels(task_names)
    ax.set_title("Risk Penalty Heatmap (Optimised Assignments)", color=PALETTE["fg"])
    plt.colorbar(im, ax=ax, label="Risk Penalty")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight", facecolor=PALETTE["bg"])
    plt.close()
    return save_path


# ─── Pretty-print helpers ─────────────────────────────────────────────────────

def print_result(result: ScheduleResult):
    method_label = result.method.upper()
    print(f"\n{'='*60}")
    print(f"  {method_label} SCHEDULE  |  Status: {result.solver_status}")
    print(f"  Total Cost: {result.total_cost:.4f}")
    print(f"{'='*60}")
    header = f"{'Task':<14} {'Server':<12} {'Time':>7} {'Risk':>8} {'Load':>8} {'Total':>8}"
    print(header)
    print("-" * len(header))
    for a in result.assignments:
        flag = " ⚠ COMPROMISED" if a.server.compromised else ""
        print(
            f"{a.task.name:<14} {a.server.name:<12} "
            f"{a.time_cost:>7.3f} {a.risk_penalty:>8.3f} "
            f"{a.load_penalty:>8.3f} {a.cost:>8.3f}{flag}"
        )
    print()
