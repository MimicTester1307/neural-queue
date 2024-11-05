import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.neural_queue.core.queue.queue import Queue
from src.neural_queue.core.task.task import Task
from src.neural_queue.core.task.task_priority import TaskPriority
from benchmarks.benchmark_result import BenchmarkResult

class QueueBenchmark:
    def __init__(self, maxsize: int = 0):
        self.queue = Queue(maxsize=maxsize)
        self.mock_func = lambda: time.sleep(0.0001) # simulate small work

    def _create_task(self, priority: TaskPriority = TaskPriority.NORMAL) -> Task:
        return Task(func=self.mock_func, priority=priority)

    def benchmark_single_threaded_throughput(self, num_operations: int = 100000) -> BenchmarkResult:
        """Measure single threaded put/get throughput"""
        latencies = []
        errors = 0
        start_time = time.perf_counter()

        for _ in range(num_operations):
            # measure put latency
            task = self._create_task()
            put_start = time.perf_counter()
            success = self.queue.put(task, timeout=1)
            put_end = time.perf_counter()

            if not success:
                errors += 1
            latencies.append((put_end - put_start) * 1000) # convert to ms

            # measure get latency
            get_start = time.perf_counter()
            task = self.queue.get(timeout=1)
            get_end = time.perf_counter()

            if task is None:
                errors += 1
            latencies.append((get_end - get_start) * 1000)

        end_time = time.perf_counter()
        duration = end_time - start_time

        return BenchmarkResult(
            name="Single threaded throughput",
            ops_per_second=num_operations * 2 / duration, # *2 because each iteration is put+get
            avg_latency_ms=statistics.mean(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=20)[-1],
            p99_latency_ms=statistics.quantiles(latencies, n=100)[-1],
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            total_ops=num_operations * 2,
            duration_seconds=duration,
            error_rate=errors / (num_operations * 2),
        )

    def benchmark_concurrent_throughput(self, num_operations: int = 100000, num_threads: int = 4) -> BenchmarkResult:
        """Measure concurrent put/get throughput"""
        latencies = []
        errors = 0
        latencies_lock = threading.Lock()
        errors_lock = threading.Lock()
        ops_per_thread = num_operations // num_threads

        def worker():
            local_latencies = []
            local_errors = 0

            for _ in range(ops_per_thread):
                # Put operations
                task = self._create_task()
                put_start = time.perf_counter()
                success = self.queue.put(task, timeout=1)
                put_end = time.perf_counter()

                if not success:
                    local_errors += 1
                local_latencies.append((put_end - put_start) * 1000)

                # Get operations
                get_start = time.perf_counter()
                task = self.queue.get(timeout=1)
                get_end = time.perf_counter()

                if task is None:
                    local_errors += 1
                local_latencies.append((get_end - get_start) * 1000)

            # merge thread-local results
            with latencies_lock:
                latencies.extend(local_latencies)
            with errors_lock:
                nonlocal errors
                errors += local_errors

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in as_completed(futures):
                future.result() # propagate any exceptions

        end_time = time.perf_counter()
        duration = end_time - start_time

        return BenchmarkResult(
            name=f"Concurrent throughput ({num_threads} threads)",
            ops_per_second=num_operations * 2 / duration,
            avg_latency_ms=statistics.mean(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=20)[-1],
            p99_latency_ms=statistics.quantiles(latencies, n=100)[-1],
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            total_ops=num_operations * 2,
            duration_seconds=duration,
            error_rate=errors / (num_threads * 2),
        )

    def benchmark_priority_ordering(self, num_tasks: int = 10000) -> BenchmarkResult:
        """Measure priority queue ordering correctness and performance"""
        latencies = []
        errors = 0
        priorities = list(TaskPriority)
        start_time = time.perf_counter()

        # put tasks with random priorities
        for _ in range(num_tasks):
            priority = random.choice(priorities)
            task = self._create_task(priority=priority)

            put_start = time.perf_counter()
            success = self.queue.put(task, timeout=1)
            put_end = time.perf_counter()

            if not success:
                errors += 1
            latencies.append((put_end - put_start) * 1000)

        # verify tasks come out in priority order
        last_priority = TaskPriority.CRITICAL
        for _ in range(num_tasks):
            get_start = time.perf_counter()
            task = self.queue.get(timeout=1)
            get_end = time.perf_counter()

            if task is None:
                errors += 1
            elif task.priority.value > last_priority.value:
                errors += 1
            last_priority = task.priority

            latencies.append((get_end - get_start) * 1000)

        end_time = time.perf_counter()
        duration = end_time - start_time

        return BenchmarkResult(
            name="Priority Ordering Correctness and Performance",
            ops_per_second=num_tasks * 2 / duration,
            avg_latency_ms=statistics.mean(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=20)[-1],
            p99_latency_ms=statistics.quantiles(latencies, n=100)[-1],
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            total_ops=num_tasks * 2,
            duration_seconds=duration,
            error_rate=errors / (num_tasks * 2),
        )
