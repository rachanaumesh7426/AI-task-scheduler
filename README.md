# Intelligent Cloud Task Scheduler
### Security-Aware ILP Optimisation for Distributed AI Workloads

---

## Setup

```bash
pip install -r requirements.txt
```

---

## CLI Usage

```bash
# Pre-built demo scenario (6 tasks, 4 servers, one compromised)
python main.py demo

# Random simulation (adjust size with flags)
python main.py simulate --tasks 10 --servers 5 --seed 99

# Batch statistics across many random runs
python main.py batch --runs 30 --tasks 8 --servers 4
```

All output (charts, JSON, CSV) is saved to the `output/` folder.

---

## Web Interface

```bash
python app.py
# Open http://localhost:5000
```

Features:
- Add / edit / remove tasks and servers visually
- Tune cost weights (w₁ w₂ w₃) with sliders
- Compare naive vs ILP-optimised assignment side-by-side
- 4 live matplotlib charts (embedded as base64)
- Export results to JSON or CSV
- Batch simulation statistics panel

---

## Cost Model

```
cost(task, server) = w1 * time_cost
                   + w2 * risk_penalty
                   + w3 * load_penalty

time_cost    = workload / speed
risk_penalty = 0                           if sensitivity <= security (and not compromised)
             = 10 * (sensitivity-security) if sensitivity > security
             = 50 * sensitivity            if server is compromised
load_penalty = 5 * max(0, utilisation - 0.7)²
```

Default weights: **w₁=1.0, w₂=2.0, w₃=0.5**

---

## Project Structure

```
project/
├── main.py          — CLI interface
├── app.py           — Flask web app
├── models.py        — Task, Server, Assignment, ScheduleResult dataclasses
├── scheduler.py     — ILP optimiser (PuLP) + naive scheduler
├── simulation.py    — Random scenario generation & batch stats
├── utils.py         — Matplotlib charts + CSV/JSON export
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```
