#!/usr/bin/env python3
"""
main.py — CLI interface for the Intelligent Cloud Task Scheduler.

Usage examples:
  python main.py demo
  python main.py simulate --tasks 10 --servers 5
  python main.py batch --runs 30
"""
import argparse
import os
import sys

from models import Task, Server
from scheduler import optimised_schedule, naive_schedule
from simulation import random_tasks, random_servers, run_comparison, run_batch_simulation
from utils import (
    export_json, export_csv, export_comparison_csv,
    plot_cost_breakdown, plot_server_utilisation,
    plot_total_cost_comparison, plot_risk_heatmap,
    print_result,
)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Demo scenario (hand-crafted) ────────────────────────────────────────────

def demo_tasks():
    return [
        Task("GPT-Infer-1",  workload=10, sensitivity=5, priority=3, task_type="inference"),
        Task("BatchJob-2",   workload=15, sensitivity=2, priority=1, task_type="batch"),
        Task("Train-ResNet", workload=25, sensitivity=3, priority=2, task_type="training"),
        Task("API-Request",  workload=5,  sensitivity=4, priority=3, task_type="inference"),
        Task("DataPipeline", workload=18, sensitivity=1, priority=1, task_type="batch"),
        Task("SecureInfer",  workload=8,  sensitivity=5, priority=3, task_type="inference"),
    ]


def demo_servers():
    return [
        Server("Alpha",   speed=8,  security=5, capacity=50, compromised=False, region="us-east"),
        Server("Beta",    speed=12, security=2, capacity=60, compromised=False, region="us-west"),
        Server("Gamma",   speed=5,  security=4, capacity=40, compromised=True,  region="eu-central"),
        Server("Delta",   speed=10, security=3, capacity=55, compromised=False, region="ap-south"),
    ]


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_demo(args):
    tasks = demo_tasks()
    servers = demo_servers()

    print("\n📋 TASKS")
    for t in tasks:
        print(f"  {t.name:<16} workload={t.workload:<5} sensitivity={t.sensitivity}  type={t.task_type}")

    print("\n🖥  SERVERS")
    for s in servers:
        comp = "  ⚠ COMPROMISED" if s.compromised else ""
        print(f"  {s.name:<10} speed={s.speed:<5} security={s.security}  cap={s.capacity}{comp}")

    results = run_comparison(tasks, servers)
    for method, result in results.items():
        print_result(result)

    _save_outputs(results, prefix="demo")


def cmd_simulate(args):
    print(f"\n🔀  Generating {args.tasks} random tasks on {args.servers} servers …")
    tasks = random_tasks(args.tasks, seed=args.seed)
    servers = random_servers(args.servers, seed=args.seed)

    results = run_comparison(tasks, servers)
    for method, result in results.items():
        print_result(result)

    improvement = 0.0
    n = results["naive"].total_cost
    o = results["optimized"].total_cost
    if n > 0:
        improvement = (n - o) / n * 100
    print(f"\n✅  Cost improvement: {improvement:.1f}%  (naive={n:.2f}  optimised={o:.2f})\n")

    _save_outputs(results, prefix="simulate")


def cmd_batch(args):
    print(f"\n📊  Running {args.runs} batch simulations …")
    stats = run_batch_simulation(num_runs=args.runs, num_tasks=args.tasks, num_servers=args.servers)
    print("\nBatch Simulation Statistics")
    print("─" * 40)
    for k, v in stats.items():
        print(f"  {k:<28} {v}")
    print()

    import json, os
    path = os.path.join(OUTPUT_DIR, "batch_stats.json")
    with open(path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  Saved → {path}\n")


def _save_outputs(results, prefix="run"):
    # JSON
    for method, result in results.items():
        p = os.path.join(OUTPUT_DIR, f"{prefix}_{method}.json")
        export_json(result, p)
        print(f"  JSON  → {p}")

    # CSV comparison
    p = os.path.join(OUTPUT_DIR, f"{prefix}_comparison.csv")
    export_comparison_csv(results, p)
    print(f"  CSV   → {p}")

    # Charts
    for fn, label in [
        (plot_cost_breakdown,        "cost_breakdown"),
        (plot_server_utilisation,    "server_utilisation"),
        (plot_total_cost_comparison, "total_cost"),
        (plot_risk_heatmap,          "risk_heatmap"),
    ]:
        p = os.path.join(OUTPUT_DIR, f"{prefix}_{label}.png")
        fn(results, p)
        print(f"  Chart → {p}")


# ─── Entry point ──────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        description="Intelligent Cloud Task Scheduler — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # demo
    sub.add_parser("demo", help="Run with a pre-defined scenario")

    # simulate
    sim = sub.add_parser("simulate", help="Random simulation")
    sim.add_argument("--tasks",   type=int, default=8,  help="Number of tasks (default 8)")
    sim.add_argument("--servers", type=int, default=4,  help="Number of servers (default 4)")
    sim.add_argument("--seed",    type=int, default=42, help="Random seed")

    # batch
    bat = sub.add_parser("batch", help="Batch statistics over many runs")
    bat.add_argument("--runs",    type=int, default=20, help="Number of runs (default 20)")
    bat.add_argument("--tasks",   type=int, default=8)
    bat.add_argument("--servers", type=int, default=4)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {"demo": cmd_demo, "simulate": cmd_simulate, "batch": cmd_batch}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
