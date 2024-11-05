from dataclasses import dataclass

@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    name: str
    ops_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    total_ops: int
    duration_seconds: float
    error_rate: float