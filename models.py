from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    name: str
    workload: float        # Units of compute required
    sensitivity: int       # 1-5 scale (5 = top secret)
    priority: int = 1      # 1-3 scale (3 = highest)
    task_type: str = "inference"  # inference | training | batch

    def __post_init__(self):
        assert 1 <= self.sensitivity <= 5, "Sensitivity must be 1-5"
        assert self.workload > 0, "Workload must be positive"
        assert 1 <= self.priority <= 3, "Priority must be 1-3"


@dataclass
class Server:
    name: str
    speed: float           # Compute units per time unit
    security: int          # 1-5 scale (5 = most secure)
    capacity: float        # Max total workload it can handle
    compromised: bool = False
    region: str = "us-east"
    current_load: float = 0.0

    def __post_init__(self):
        assert 1 <= self.security <= 5, "Security must be 1-5"
        assert self.speed > 0, "Speed must be positive"
        assert self.capacity > 0, "Capacity must be positive"

    @property
    def utilization(self) -> float:
        return self.current_load / self.capacity if self.capacity > 0 else 0.0

    @property
    def available_capacity(self) -> float:
        return self.capacity - self.current_load


@dataclass
class Assignment:
    task: Task
    server: Server
    cost: float
    time_cost: float
    risk_penalty: float
    load_penalty: float

    def to_dict(self) -> dict:
        return {
            "task_name": self.task.name,
            "task_workload": self.task.workload,
            "task_sensitivity": self.task.sensitivity,
            "task_type": self.task.task_type,
            "server_name": self.server.name,
            "server_speed": self.server.speed,
            "server_security": self.server.security,
            "server_compromised": self.server.compromised,
            "time_cost": round(self.time_cost, 4),
            "risk_penalty": round(self.risk_penalty, 4),
            "load_penalty": round(self.load_penalty, 4),
            "total_cost": round(self.cost, 4),
        }


@dataclass
class ScheduleResult:
    assignments: list
    total_cost: float
    solver_status: str
    method: str  # "optimized" | "naive"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "solver_status": self.solver_status,
            "total_cost": round(self.total_cost, 4),
            "assignments": [a.to_dict() for a in self.assignments],
            "metadata": self.metadata,
        }
