"""
scheduler.py — Task assignment optimiser.

Uses scipy.optimize.milp (Mixed-Integer Linear Programming) which ships
with SciPy 1.7+.  The mathematical model is identical to a PuLP formulation:

  Minimise   Σ_{i,j}  cost[i,j] * x[i,j]
  subject to Σ_j x[i,j] = 1          for all tasks i
             Σ_i workload[i]*x[i,j] <= capacity[j]  for all servers j
             x[i,j] ∈ {0, 1}
"""
import copy
from typing import List, Tuple

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

from models import Task, Server, Assignment, ScheduleResult

W1 = 1.0
W2 = 2.0
W3 = 0.5
COMPROMISE_PENALTY = 50.0
RISK_SCALE = 10.0
LOAD_SCALE = 5.0


def compute_cost(task, server, projected_load, w1=W1, w2=W2, w3=W3):
    time_cost = task.workload / server.speed
    if server.compromised:
        risk_penalty = COMPROMISE_PENALTY * task.sensitivity
    elif task.sensitivity > server.security:
        risk_penalty = RISK_SCALE * (task.sensitivity - server.security)
    else:
        risk_penalty = 0.0
    utilisation = projected_load / server.capacity
    load_penalty = LOAD_SCALE * max(0.0, utilisation - 0.7) ** 2
    total = w1 * time_cost + w2 * risk_penalty + w3 * load_penalty
    return total, time_cost, risk_penalty, load_penalty


def optimised_schedule(tasks, servers, w1=W1, w2=W2, w3=W3):
    servers_copy = copy.deepcopy(servers)
    n = len(tasks)
    m = len(servers_copy)
    N = n * m

    c = np.zeros(N)
    cost_detail = {}
    for i, task in enumerate(tasks):
        for j, srv in enumerate(servers_copy):
            projected = srv.current_load + task.workload
            total, tc, rp, lp = compute_cost(task, srv, projected, w1, w2, w3)
            c[i * m + j] = total
            cost_detail[(i, j)] = (total, tc, rp, lp)

    A_rows, lb_list, ub_list = [], [], []
    for i in range(n):
        row = np.zeros(N)
        for j in range(m):
            row[i * m + j] = 1.0
        A_rows.append(row); lb_list.append(1.0); ub_list.append(1.0)
    for j, srv in enumerate(servers_copy):
        row = np.zeros(N)
        for i, task in enumerate(tasks):
            row[i * m + j] = task.workload
        A_rows.append(row); lb_list.append(-np.inf); ub_list.append(srv.capacity - srv.current_load)

    constraints = LinearConstraint(np.vstack(A_rows), np.array(lb_list), np.array(ub_list))
    result = milp(c, constraints=constraints, integrality=np.ones(N), bounds=Bounds(np.zeros(N), np.ones(N)))

    assignments, total_cost = [], 0.0
    if result.success:
        x = np.round(result.x).astype(int)
        for i, task in enumerate(tasks):
            for j, srv in enumerate(servers_copy):
                if x[i * m + j] == 1:
                    total, tc, rp, lp = cost_detail[(i, j)]
                    assignments.append(Assignment(task, srv, total, tc, rp, lp))
                    total_cost += total
                    srv.current_load += task.workload
                    break
        status = "Optimal"
    else:
        status = f"MILP fallback ({result.message})"
        for i, task in enumerate(tasks):
            best_j = min(range(m), key=lambda j: cost_detail[(i, j)][0])
            total, tc, rp, lp = cost_detail[(i, best_j)]
            assignments.append(Assignment(task, servers_copy[best_j], total, tc, rp, lp))
            total_cost += total

    return ScheduleResult(assignments=assignments, total_cost=total_cost,
                          solver_status=status, method="optimized",
                          metadata={"w1": w1, "w2": w2, "w3": w3, "solver": "scipy.milp"})


def naive_schedule(tasks, servers, w1=W1, w2=W2, w3=W3):
    servers_copy = copy.deepcopy(servers)
    assignments, total_cost, idx = [], 0.0, 0
    for task in tasks:
        placed = False
        for attempt in range(len(servers_copy)):
            srv = servers_copy[(idx + attempt) % len(servers_copy)]
            if srv.available_capacity >= task.workload:
                projected = srv.current_load + task.workload
                c, tc, rp, lp = compute_cost(task, srv, projected, w1, w2, w3)
                assignments.append(Assignment(task, srv, c, tc, rp, lp))
                total_cost += c; srv.current_load += task.workload
                placed = True; idx = (idx + 1) % len(servers_copy); break
        if not placed:
            srv = min(servers_copy, key=lambda s: s.current_load)
            projected = srv.current_load + task.workload
            c, tc, rp, lp = compute_cost(task, srv, projected, w1, w2, w3)
            assignments.append(Assignment(task, srv, c, tc, rp, lp))
            total_cost += c; srv.current_load += task.workload
    return ScheduleResult(assignments=assignments, total_cost=total_cost,
                          solver_status="Feasible (Naive)", method="naive",
                          metadata={"w1": w1, "w2": w2, "w3": w3})
