from benchmarks.queue.queue_benchmark import QueueBenchmark

def run_benchmarks():
    """Run all benchmarks and display results"""
    benchmark = QueueBenchmark()

    # run benchmarks
    results = [
        benchmark.benchmark_single_threaded_throughput(num_operations=100000),
        benchmark.benchmark_concurrent_throughput(num_operations=100000, num_threads=4),
        benchmark.benchmark_priority_ordering(num_tasks=10000)
    ]

    # print results
    print("\nQueue Performance Benchmark Results")
    print("=" * 80)

    for result in results:
        print(f"\n{result.name}")
        print("-" * 40)
        print(f"Operations per second: {result.ops_per_second:.2f}")
        print(f"Average latency: {result.avg_latency_ms:.3f}ms")
        print(f"95th percentile latency: {result.p95_latency_ms:.3f}ms")
        print(f"99th percentile latency: {result.p99_latency_ms:.3f}ms")
        print(f"Min latency: {result.min_latency_ms:.3f}ms")
        print(f"Max latency: {result.max_latency_ms:.3f}ms")
        print(f"Total operations: {result.total_ops}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Error rate: {result.error_rate * 100:.2f}%")

if __name__ == "__main__":
    run_benchmarks()