"""
simulation.py — generates random task/server sets and compares naive vs optimised.
"""
import random
import statistics
from typing import List, Tuple, Dict, Optional

from models import Task, Server, ScheduleResult
from scheduler import optimised_schedule, naive_schedule


TASK_TYPES = ["inference", "training", "batch"]
REGIONS = ["us-east", "us-west", "eu-central", "ap-south"]


def random_tasks(n: int = 8, seed: Optional[int] = None) -> List[Task]:
    if seed is not None:
        random.seed(seed)
    tasks = []
    for i in range(n):
        tasks.append(Task(
            name=f"Task-{i+1}",
            workload=round(random.uniform(2, 20), 1),
            sensitivity=random.randint(1, 5),
            priority=random.randint(1, 3),
            task_type=random.choice(TASK_TYPES),
        ))
    return tasks


def random_servers(m: int = 4, seed: Optional[int] = None) -> List[Server]:
    if seed is not None:
        random.seed(seed + 1000)
    servers = []
    for i in range(m):
        compromised = random.random() < 0.1   # 10 % chance
        servers.append(Server(
            name=f"Server-{chr(65+i)}",
            speed=round(random.uniform(1, 10), 1),
            security=random.randint(1, 5),
            capacity=round(random.uniform(30, 80), 0),
            compromised=compromised,
            region=random.choice(REGIONS),
        ))
    return servers


def run_comparison(
    tasks: List[Task],
    servers: List[Server],
    w1: float = 1.0,
    w2: float = 2.0,
    w3: float = 0.5,
) -> Dict[str, ScheduleResult]:
    naive = naive_schedule(tasks, servers, w1, w2, w3)
    optimised = optimised_schedule(tasks, servers, w1, w2, w3)
    return {"naive": naive, "optimized": optimised}


def run_batch_simulation(
    num_runs: int = 20,
    num_tasks: int = 8,
    num_servers: int = 4,
) -> dict:
    """Run multiple random scenarios and collect aggregate statistics."""
    improvements = []
    naive_costs = []
    opt_costs = []

    for run in range(num_runs):
        tasks = random_tasks(num_tasks, seed=run)
        servers = random_servers(num_servers, seed=run)
        results = run_comparison(tasks, servers)
        n_cost = results["naive"].total_cost
        o_cost = results["optimized"].total_cost
        naive_costs.append(n_cost)
        opt_costs.append(o_cost)
        if n_cost > 0:
            improvements.append((n_cost - o_cost) / n_cost * 100)

    return {
        "num_runs": num_runs,
        "avg_naive_cost": round(statistics.mean(naive_costs), 3),
        "avg_opt_cost": round(statistics.mean(opt_costs), 3),
        "avg_improvement_pct": round(statistics.mean(improvements), 2),
        "max_improvement_pct": round(max(improvements), 2),
        "min_improvement_pct": round(min(improvements), 2),
        "stddev_improvement": round(statistics.stdev(improvements), 2),
    }
