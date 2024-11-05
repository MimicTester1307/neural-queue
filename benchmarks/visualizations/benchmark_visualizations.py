import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List
from benchmarks.queue.queue_benchmark import QueueBenchmark
from benchmarks.benchmark_result import  BenchmarkResult

class BenchmarkVisualizer:
    def __init__(self, results: List[BenchmarkResult]):
        self.results: List[BenchmarkResult] = results

        # set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette('husl')

    def create_all_visualizations(self, base_save_path: str = None):
        """
        Create all visualizations and optionally save them.

        Args:
            base_save_path (str, optional): Base path to save images.
                If provided, '_<plot_type>.png' will be appended for each visualization.
                Defaults to None.
        """
        # Plot and save throughput
        plt.figure(figsize=(10, 6))
        self.plot_throughput()
        if base_save_path:
            plt.savefig(f"{base_save_path}_throughput.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot and save latency distribution
        plt.figure(figsize=(12, 6))
        self.plot_latency_distribution()
        if base_save_path:
            plt.savefig(f"{base_save_path}_latency_dist.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot and save error rates
        plt.figure(figsize=(8, 6))
        self.plot_error_rates()
        if base_save_path:
            plt.savefig(f"{base_save_path}_error_rates.png", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot and save latency percentiles
        plt.figure(figsize=(12, 6))
        self.plot_latency_percentiles()
        if base_save_path:
            plt.savefig(f"{base_save_path}_latency_percentiles.png", dpi=300, bbox_inches='tight')
        plt.close()

    def plot_throughput(self):
        """Plot operations per second for each benchmark."""
        plt.figure(figsize=(10, 6))

        data = {
            'Benchmark': [r.name for r in self.results],
            'Operations/Second': [r.ops_per_second for r in self.results],
        }

        ax = sns.barplot(data=pd.DataFrame(data), x='Benchmark', y='Operations/Second')

        # add value labels on top of each bar
        for i, bar in enumerate(ax.patches):
            ax.text(
                bar.get_x() + bar.get_width() / 2.,  # x position (center of bar)
                bar.get_height(),  # y position
                f'{int(bar.get_height()):,}',  # text (formatted with thousands separator)
                ha='center',  # horizontal alignment
                va='bottom',  # vertical alignment
                fontsize=10
            )

        # customize axes
        ax.set_xlabel('Benchmark Type', fontsize=12)
        ax.set_ylabel('Operations/Second', fontsize=12)

        # rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # add title with custom font size
        plt.title('Queue Throughput by Benchmark Type', fontsize=14, pad=20)

        # add grid for better readability
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

        # adjust layout to prevent label cutoff
        plt.tight_layout()

    def plot_latency_distribution(self):
        """Plot latency distribution for each benchmark."""
        plt.figure(figsize=(12, 6))

        data = []
        for result in self.results:
            data.append({
                'Benchmark': result.name,
                'Average Latency (ms)': result.avg_latency_ms,
                'P95 Latency (ms)': result.p95_latency_ms,
                'P99 Latency (ms)': result.p99_latency_ms,
            })

        df = pd.DataFrame(data)
        df_melted = df.melt(id_vars=['Benchmark'],
                            var_name='Metric',
                            value_name='Latency (ms)')

        sns.barplot(data=df_melted, x='Benchmark', y='Latency (ms)', hue='Metric')

        plt.xticks(rotation=45, ha='right')
        plt.title('Latency Distribution', fontsize=14, pad=20)
        plt.legend(title='Latency Metric')
        plt.tight_layout()

    def plot_error_rates(self):
        """Plot error rates for each benchmark."""
        plt.figure(figsize=(8, 6))

        data = {
            'Benchmark': [r.name for r in self.results],
            'Error Rate (%)': [r.error_rate * 100 for r in self.results],
        }

        ax = sns.barplot(data=pd.DataFrame(data),
                         x='Benchmark',
                         y='Error Rate (%)')

        plt.xticks(rotation=45, ha='right')
        plt.title('Error Rates by Benchmark Type', fontsize=14, pad=20)
        plt.tight_layout()

    def plot_latency_percentiles(self):
        """Plot min, max, and percentile latencies"""
        plt.figure(figsize=(12, 6))

        data = []
        for result in self.results:
            data.append({
                'Benchmark': result.name,
                'Min': result.min_latency_ms,
                'P95': result.p95_latency_ms,
                'P99': result.p99_latency_ms,
                'Max': result.max_latency_ms,
            })

        df = pd.DataFrame(data)
        df_melted = df.melt(id_vars=['Benchmark'],
                            var_name='Percentile',
                            value_name='Latency (ms)')

        sns.barplot(data=df_melted,
                    x='Benchmark',
                    y='Latency (ms)',
                    hue='Percentile')

        plt.xticks(rotation=45, ha='right')
        plt.title('Latency Percentiles by Benchmark Type', fontsize=14, pad=20)
        plt.legend(title='Percentile')
        plt.tight_layout()

def run_benchmarks_with_visualization(base_save_path: str = None):
    """
    Run all benchmarks and create visualizations.

    Args:
        base_save_path (str, optional): Base path to save images.
    """
    # Run benchmarks
    benchmark = QueueBenchmark()
    results = [
        benchmark.benchmark_single_threaded_throughput(num_operations=100000),
        benchmark.benchmark_concurrent_throughput(num_operations=100000, num_threads=4),
        benchmark.benchmark_priority_ordering(num_tasks=10000)
    ]

    # Create and show visualizations
    visualizer = BenchmarkVisualizer(results)
    visualizer.create_all_visualizations(base_save_path)

    return results

if __name__ == "__main__":
    results = run_benchmarks_with_visualization("benchmark_visualizations")
