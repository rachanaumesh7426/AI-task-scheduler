"""
app.py — Flask web interface for the Intelligent Cloud Task Scheduler.
"""
import os
import io
import json
import base64
import tempfile
import csv

from flask import Flask, render_template, request, jsonify, send_file, abort

from models import Task, Server
from scheduler import optimised_schedule, naive_schedule
from simulation import random_tasks, random_servers, run_comparison, run_batch_simulation
from utils import (
    plot_cost_breakdown, plot_server_utilisation,
    plot_total_cost_comparison, plot_risk_heatmap,
    export_json, export_csv, export_comparison_csv,
)

app = Flask(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fig_to_b64(plot_fn, results):
    """Run a plot function, save to a temp file, return base64 string."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name
    try:
        plot_fn(results, path)
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    finally:
        if os.path.exists(path):
            os.remove(path)


def _parse_tasks(task_list: list) -> list:
    tasks = []
    for t in task_list:
        tasks.append(Task(
            name=str(t["name"]),
            workload=float(t["workload"]),
            sensitivity=int(t["sensitivity"]),
            priority=int(t.get("priority", 1)),
            task_type=str(t.get("task_type", "inference")),
        ))
    return tasks


def _parse_servers(server_list: list) -> list:
    servers = []
    for s in server_list:
        servers.append(Server(
            name=str(s["name"]),
            speed=float(s["speed"]),
            security=int(s["security"]),
            capacity=float(s["capacity"]),
            compromised=bool(s.get("compromised", False)),
            region=str(s.get("region", "us-east")),
        ))
    return servers


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/schedule", methods=["POST"])
def api_schedule():
    """
    POST JSON body:
    {
      "tasks": [...],
      "servers": [...],
      "weights": {"w1": 1.0, "w2": 2.0, "w3": 0.5}   // optional
    }
    """
    try:
        data = request.get_json(force=True)
        tasks = _parse_tasks(data["tasks"])
        servers = _parse_servers(data["servers"])
        w = data.get("weights", {})
        w1 = float(w.get("w1", 1.0))
        w2 = float(w.get("w2", 2.0))
        w3 = float(w.get("w3", 0.5))

        results = run_comparison(tasks, servers, w1, w2, w3)

        charts = {
            "cost_breakdown":     _fig_to_b64(plot_cost_breakdown, results),
            "server_utilisation": _fig_to_b64(plot_server_utilisation, results),
            "total_cost":         _fig_to_b64(plot_total_cost_comparison, results),
            "risk_heatmap":       _fig_to_b64(plot_risk_heatmap, results),
        }

        return jsonify({
            "status": "ok",
            "naive":     results["naive"].to_dict(),
            "optimized": results["optimized"].to_dict(),
            "charts":    charts,
            "improvement_pct": round(
                (results["naive"].total_cost - results["optimized"].total_cost)
                / max(results["naive"].total_cost, 1e-9) * 100, 2
            ),
        })
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/random", methods=["GET"])
def api_random():
    """Return a random scenario (tasks + servers)."""
    import random
    seed = int(request.args.get("seed", random.randint(0, 9999)))
    n_tasks = int(request.args.get("tasks", 6))
    n_servers = int(request.args.get("servers", 3))

    tasks = random_tasks(n_tasks, seed=seed)
    servers = random_servers(n_servers, seed=seed)

    return jsonify({
        "tasks": [
            {
                "name": t.name, "workload": t.workload,
                "sensitivity": t.sensitivity, "priority": t.priority,
                "task_type": t.task_type,
            }
            for t in tasks
        ],
        "servers": [
            {
                "name": s.name, "speed": s.speed, "security": s.security,
                "capacity": s.capacity, "compromised": s.compromised, "region": s.region,
            }
            for s in servers
        ],
        "seed": seed,
    })


@app.route("/api/batch", methods=["GET"])
def api_batch():
    runs    = int(request.args.get("runs", 20))
    n_tasks = int(request.args.get("tasks", 8))
    n_srv   = int(request.args.get("servers", 4))
    stats = run_batch_simulation(num_runs=runs, num_tasks=n_tasks, num_servers=n_srv)
    return jsonify({"status": "ok", "stats": stats})


@app.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    try:
        data = request.get_json(force=True)
        tasks = _parse_tasks(data["tasks"])
        servers = _parse_servers(data["servers"])
        w = data.get("weights", {})
        results = run_comparison(tasks, servers,
                                 float(w.get("w1", 1.0)),
                                 float(w.get("w2", 2.0)),
                                 float(w.get("w3", 0.5)))

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="") as tmp:
            path = tmp.name
        export_comparison_csv(results, path)
        return send_file(path, as_attachment=True,
                         download_name="schedule_results.csv",
                         mimetype="text/csv")
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/api/export/json", methods=["POST"])
def api_export_json():
    try:
        data = request.get_json(force=True)
        tasks = _parse_tasks(data["tasks"])
        servers = _parse_servers(data["servers"])
        w = data.get("weights", {})
        results = run_comparison(tasks, servers,
                                 float(w.get("w1", 1.0)),
                                 float(w.get("w2", 2.0)),
                                 float(w.get("w3", 0.5)))

        export_data = {
            "naive": results["naive"].to_dict(),
            "optimized": results["optimized"].to_dict(),
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
            json.dump(export_data, tmp, indent=2)
            path = tmp.name
        return send_file(path, as_attachment=True,
                         download_name="schedule_results.json",
                         mimetype="application/json")
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400


# ─── Dev server ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
