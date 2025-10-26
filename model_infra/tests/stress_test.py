#!/usr/bin/env python3
"""
Sustained Load Testing Pipeline for Modal DeepSeek-OCR Implementations

This script compares the performance of modal_base.py vs modal_app.py
by running sustained load tests with ~32 concurrent requests for 30 seconds,
measuring:
- Latency (response time)
- Throughput (requests per second)
- GPU Memory Usage
- GPU Utilization
"""

import asyncio
import time
import statistics
import json
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import numpy as np

@dataclass
class TestResult:
    """Container for test results"""
    implementation: str
    concurrency: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float
    gpu_memory_peak: float
    gpu_utilization_avg: float
    test_duration: float

class StressTester:
    """Stress testing framework for Modal OCR implementations"""

    def __init__(self, base_url: str = "https://alphaxiv--deepseek-ocr-modal-serve-dev.modal.run"):
        self.base_url = base_url
        # Use the tests directory for existing PDF files
        self.test_data_dir = Path(__file__).parent  # tests/ directory
        self.results_dir = Path("stress_test_results")
        self.results_dir.mkdir(exist_ok=True)

        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("husl")

    def get_test_pdfs(self):
        """Get all available test PDF files"""
        pdf_files = list(self.test_data_dir.glob("*.pdf"))
        
        if not pdf_files:
            raise FileNotFoundError("No PDF files found in tests directory")
        
        return pdf_files

    async def run_single_request(self, session: aiohttp.ClientSession, pdf_path: str, implementation: str) -> Dict[str, Any]:
        """Run a single OCR request"""
        start_time = time.time()

        try:
            # Read file bytes into memory first to avoid the file object being
            # closed while aiohttp is still sending data. Use FormData to send a
            # proper multipart/form-data request that mirrors a browser/file upload.
            url = f"{self.base_url}/run/app/pdf"
            file_bytes = None
            with open(pdf_path, 'rb') as f:
                file_bytes = f.read()

            data = aiohttp.FormData()
            data.add_field('file', file_bytes,
                           filename=Path(pdf_path).name,
                           content_type='application/pdf')

            async with session.post(url, data=data) as response:
                end_time = time.time()
                latency = end_time - start_time

                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'latency': latency,
                        'pages_processed': result.get('num_successful', 0),
                        'total_pages': result.get('num_pages', 0)
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'latency': latency,
                        'error': f"HTTP {response.status}: {error_text}"
                    }

        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            return {
                'success': False,
                'latency': latency,
                'error': str(e)
            }

    async def run_sustained_load_test(self, implementation: str, target_concurrency: int = 32, duration_seconds: int = 30) -> TestResult:
        """Run a sustained load test for a specific duration"""
        print(f"🧪 Running sustained load test for {implementation}...")
        print(f"   Target concurrency: {target_concurrency}")
        print(f"   Duration: {duration_seconds} seconds")

        latencies = []
        successful = 0
        failed = 0
        start_time = time.time()
        end_time = start_time + duration_seconds

        async with aiohttp.ClientSession() as session:
            # Get all available test PDFs for random selection
            pdf_files = self.get_test_pdfs()

            print(f"   Using {len(pdf_files)} available PDFs for random selection")

            # We'll keep a master list of all tasks we create so we can await
            # every single one at the end. This avoids any race where tasks
            # might be created and not be awaited later.
            active_tasks = set()
            all_tasks = []
            request_count = 0

            import random

            while time.time() < end_time:
                # Maintain target concurrency by adding new requests
                while len(active_tasks) < target_concurrency and time.time() < end_time:
                    request_count += 1
                    # Randomly select a PDF for this request
                    random_pdf = random.choice(pdf_files)
                    task = asyncio.create_task(self.run_single_request(session, str(random_pdf), implementation))
                    active_tasks.add(task)
                    all_tasks.append(task)

                # Wait for at least one task to complete
                if active_tasks:
                    done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)

                    # Remove finished tasks from active_tasks and process them
                    for task in done:
                        active_tasks.discard(task)
                        try:
                            result = task.result()
                            if result['success']:
                                successful += 1
                                latencies.append(result['latency'])
                            else:
                                failed += 1
                                print(f"❌ Request failed: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            failed += 1
                            print(f"❌ Task exception: {e}")

                # Small delay to prevent overwhelming the event loop
                await asyncio.sleep(0.01)

            # Wait for all created tasks to complete (this guarantees nothing was
            # left running in the background). We use return_exceptions to
            # capture any thrown exceptions and count them as failures below.
            if all_tasks:
                remaining_results = await asyncio.gather(*all_tasks, return_exceptions=True)
                # We already counted successful/failed for tasks we saw earlier,
                # but gathering here ensures every task has finished. To avoid
                # double-counting, only increment counts for tasks not already
                # included (we can detect that because their latencies wouldn't
                # be in our `latencies` list). Simpler approach: recompute
                # summary from scratch from remaining_results for correctness.

                # Reset counters and reconstruct from remaining_results to avoid
                # subtle double-counting issues.
                successful = 0
                failed = 0
                latencies = []

                for result in remaining_results:
                    if isinstance(result, Exception):
                        failed += 1
                        print(f"❌ Final task exception: {result}")
                    elif isinstance(result, dict) and result.get('success'):
                        successful += 1
                        latencies.append(result['latency'])
                    else:
                        failed += 1

        test_duration = time.time() - start_time
        # Total requests equals the number of tasks we created
        total_requests = len(all_tasks)

        # Safety: if no tasks were created, keep totals consistent
        if total_requests == 0:
            successful = 0
            failed = 0

        # Calculate statistics
        if latencies:
            avg_latency = statistics.mean(latencies)
            p50_latency = statistics.median(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        else:
            avg_latency = p50_latency = p95_latency = p99_latency = 0

        throughput = successful / test_duration if test_duration > 0 else 0

        print(f"   Completed {total_requests} requests in {test_duration:.1f}s")
        print(f"   Throughput: {throughput:.2f} req/sec")
        print(f"   Success rate: {successful}/{total_requests} ({successful/total_requests*100:.1f}%)")

        return TestResult(
            implementation=implementation,
            concurrency=target_concurrency,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_latency=avg_latency,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            throughput=throughput,
            gpu_memory_peak=0.0,  # Will be collected separately
            gpu_utilization_avg=0.0,  # Will be collected separately
            test_duration=test_duration
        )

    def create_comparison_visualizations(self, results: List[TestResult]):
        """Create comprehensive visualizations comparing the implementations"""
        df = pd.DataFrame([{
            'implementation': r.implementation,
            'concurrency': r.concurrency,
            'throughput': r.throughput,
            'avg_latency': r.avg_latency,
            'p95_latency': r.p95_latency,
            'success_rate': r.successful_requests / r.total_requests * 100
        } for r in results])

        # Set up the plotting area
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Modal DeepSeek-OCR Performance Comparison', fontsize=16, fontweight='bold')

        # 1. Throughput vs Concurrency
        ax1 = axes[0, 0]
        for impl in df['implementation'].unique():
            impl_data = df[df['implementation'] == impl]
            ax1.plot(impl_data['concurrency'], impl_data['throughput'],
                    marker='o', linewidth=2, markersize=6, label=impl)
        ax1.set_xlabel('Concurrency Level')
        ax1.set_ylabel('Throughput (req/sec)')
        ax1.set_title('Throughput vs Concurrency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Average Latency vs Concurrency
        ax2 = axes[0, 1]
        for impl in df['implementation'].unique():
            impl_data = df[df['implementation'] == impl]
            ax2.plot(impl_data['concurrency'], impl_data['avg_latency'],
                    marker='s', linewidth=2, markersize=6, label=impl)
        ax2.set_xlabel('Concurrency Level')
        ax2.set_ylabel('Average Latency (seconds)')
        ax2.set_title('Average Latency vs Concurrency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. P95 Latency vs Concurrency
        ax3 = axes[1, 0]
        for impl in df['implementation'].unique():
            impl_data = df[df['implementation'] == impl]
            ax3.plot(impl_data['concurrency'], impl_data['p95_latency'],
                    marker='^', linewidth=2, markersize=6, label=impl)
        ax3.set_xlabel('Concurrency Level')
        ax3.set_ylabel('P95 Latency (seconds)')
        ax3.set_title('P95 Latency vs Concurrency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # 4. Success Rate vs Concurrency
        ax4 = axes[1, 1]
        for impl in df['implementation'].unique():
            impl_data = df[df['implementation'] == impl]
            ax4.plot(impl_data['concurrency'], impl_data['success_rate'],
                    marker='d', linewidth=2, markersize=6, label=impl)
        ax4.set_xlabel('Concurrency Level')
        ax4.set_ylabel('Success Rate (%)')
        ax4.set_title('Success Rate vs Concurrency')
        ax4.set_ylim(0, 105)
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.results_dir / 'performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

        # Create detailed metrics table
        summary_df = df.groupby('implementation').agg({
            'throughput': ['mean', 'max'],
            'avg_latency': ['mean', 'min'],
            'p95_latency': ['mean', 'min'],
            'success_rate': 'mean'
        }).round(3)

        print("\n📊 Performance Summary:")
        print(summary_df.to_string())

        # Save detailed results
        with open(self.results_dir / 'detailed_results.json', 'w') as f:
            json.dump([{
                'implementation': r.implementation,
                'concurrency': r.concurrency,
                'total_requests': r.total_requests,
                'successful_requests': r.successful_requests,
                'failed_requests': r.failed_requests,
                'avg_latency': round(r.avg_latency, 3),
                'p50_latency': round(r.p50_latency, 3),
                'p95_latency': round(r.p95_latency, 3),
                'p99_latency': round(r.p99_latency, 3),
                'throughput': round(r.throughput, 3),
                'test_duration': round(r.test_duration, 3)
            } for r in results], f, indent=2)

    async def run_full_test_suite(self):
        """Run the complete stress testing suite"""
        print("🚀 Starting DeepSeek-OCR Stress Testing Suite")
        print("=" * 60)

        # Get available test PDFs
        print("📄 Finding available test PDF files...")
        try:
            pdf_files = self.get_test_pdfs()
            print(f"Found {len(pdf_files)} PDF files:")
            for pdf_file in pdf_files:
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                print(f"  {pdf_file.name} ({size_mb:.1f}MB)")
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            return []

        # Test configurations for sustained load testing
        implementations = ['base']  # modal_base vs modal_app
        target_concurrency = 16  # Around 32 concurrent requests
        test_duration = 30  # 30 seconds per implementation

        all_results = []

        for implementation in implementations:
            try:
                result = await self.run_sustained_load_test(
                    implementation, target_concurrency, test_duration
                )
                all_results.append(result)

            except Exception as e:
                print(f"  ❌ {implementation} sustained load test failed: {e}")
        # Save numpy snapshot of results (one file per run)
        timestamp = int(time.time())
        npy_path = self.results_dir / f"results_snapshot_{timestamp}.npy"
        # Use pickle to store list of TestResult objects as dicts
        serializable = [r.__dict__ for r in all_results]
        np.save(npy_path, serializable, allow_pickle=True)

        # Create visualizations (also saves JSON/detailed_results as before)
        print("\n📈 Generating performance visualizations...")
        self.create_comparison_visualizations(all_results)

        print(f"\n✅ Sustained load testing complete! Results saved to {self.results_dir}")
        print(f"🔖 Numpy snapshot written to {npy_path}")
        return all_results

async def main():
    """Main entry point"""
    tester = StressTester()

    # Run the sustained load test suite
    results = await tester.run_full_test_suite()

    # Print final summary
    print("\n🏆 Sustained Load Test Results Summary:")
    print("=" * 50)

    for result in results:
        print(f"{result.implementation.upper()}: {result.total_requests} requests | "
              f"Throughput: {result.throughput:.2f} req/sec | "
              f"Avg Latency: {result.avg_latency:.2f}s | "
              f"P95 Latency: {result.p95_latency:.2f}s | "
              f"Success Rate: {result.successful_requests/result.total_requests*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())