"""
GPU Metrics Collection for Modal DeepSeek-OCR

This module provides utilities to collect GPU memory usage, utilization,
and other performance metrics during OCR processing.
"""

import time
import psutil
import GPUtil
from typing import Dict, List, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import threading
import json

@dataclass
class GPUMetrics:
    """Container for GPU metrics snapshot"""
    timestamp: float
    gpu_id: int
    memory_used: float  # MB
    memory_total: float  # MB
    memory_utilization: float  # %
    gpu_utilization: float  # %
    temperature: float  # Celsius

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    start_time: float
    end_time: float
    duration: float
    gpu_memory_peak: float
    gpu_utilization_avg: float
    cpu_usage_avg: float
    gpu_metrics_history: List[GPUMetrics]

class MetricsCollector:
    """Collects GPU and system metrics during processing"""

    def __init__(self, collection_interval: float = 0.5):
        self.collection_interval = collection_interval
        self.is_collecting = False
        self.metrics_history: List[GPUMetrics] = []
        self.collection_thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None

    def _collect_gpu_metrics(self) -> List[GPUMetrics]:
        """Collect current GPU metrics"""
        try:
            gpus = GPUtil.getGPUs()
            metrics = []

            for gpu in gpus:
                metric = GPUMetrics(
                    timestamp=time.time(),
                    gpu_id=gpu.id,
                    memory_used=gpu.memoryUsed,
                    memory_total=gpu.memoryTotal,
                    memory_utilization=(gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
                    gpu_utilization=gpu.load * 100,
                    temperature=gpu.temperature
                )
                metrics.append(metric)

            return metrics
        except Exception as e:
            print(f"Warning: Failed to collect GPU metrics: {e}")
            return []

    def _collection_worker(self):
        """Background worker to collect metrics"""
        while self.is_collecting:
            metrics = self._collect_gpu_metrics()
            self.metrics_history.extend(metrics)
            time.sleep(self.collection_interval)

    def start_collection(self):
        """Start collecting metrics in background"""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.start_time = time.time()
        self.metrics_history = []
        self.collection_thread = threading.Thread(target=self._collection_worker, daemon=True)
        self.collection_thread.start()

    def stop_collection(self) -> PerformanceMetrics:
        """Stop collecting and return aggregated metrics"""
        if not self.is_collecting:
            # Be resilient: if stop_collection is called without a matching start_collection,
            # return an empty PerformanceMetrics object instead of raising. This can happen
            # if the context manager was entered but start failed, or if collection was
            # disabled in the environment.
            print("Warning: stop_collection called but metrics collection was not started")
            end_time = time.time()
            return PerformanceMetrics(
                start_time=self.start_time or end_time,
                end_time=end_time,
                duration=0.0,
                gpu_memory_peak=0.0,
                gpu_utilization_avg=0.0,
                cpu_usage_avg=0.0,
                gpu_metrics_history=[]
            )

        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1.0)

        end_time = time.time()
        duration = end_time - (self.start_time or end_time)

        # Calculate aggregates
        if self.metrics_history:
            memory_usages = [m.memory_used for m in self.metrics_history]
            gpu_utilizations = [m.gpu_utilization for m in self.metrics_history]

            gpu_memory_peak = max(memory_usages) if memory_usages else 0
            gpu_utilization_avg = sum(gpu_utilizations) / len(gpu_utilizations) if gpu_utilizations else 0
        else:
            gpu_memory_peak = 0
            gpu_utilization_avg = 0

        # CPU usage (rough estimate)
        if _HAS_PSUTIL and psutil is not None:
            try:
                cpu_usage_avg = psutil.cpu_percent(interval=None)
            except Exception:
                cpu_usage_avg = 0.0
        else:
            cpu_usage_avg = 0.0

        return PerformanceMetrics(
            start_time=self.start_time or 0,
            end_time=end_time,
            duration=duration,
            gpu_memory_peak=gpu_memory_peak,
            gpu_utilization_avg=gpu_utilization_avg,
            cpu_usage_avg=cpu_usage_avg,
            gpu_metrics_history=self.metrics_history
        )

    @contextmanager
    def collect_metrics(self):
        """Context manager for automatic metrics collection"""
        collection_started = False
        try:
            try:
                self.start_collection()
                collection_started = True
            except Exception as e:
                # Don't let metrics startup errors break the main processing flow
                print(f"Warning: failed to start metrics collection: {e}")
                collection_started = False

            yield self

        finally:
            try:
                # Attempt to stop collection; stop_collection is resilient and will
                # return an empty PerformanceMetrics if collection wasn't started.
                metrics = self.stop_collection()
                # Store metrics for later retrieval
                self._last_metrics = metrics
            except Exception as e:
                # Last-resort guard: log but do not propagate exceptions to caller
                print(f"Warning: stop_collection raised an exception: {e}")

    def get_last_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the last collected metrics"""
        return getattr(self, '_last_metrics', None)

    def save_metrics_to_file(self, filepath: str, metrics: PerformanceMetrics):
        """Save metrics to JSON file"""
        data = {
            'start_time': metrics.start_time,
            'end_time': metrics.end_time,
            'duration': metrics.duration,
            'gpu_memory_peak_mb': metrics.gpu_memory_peak,
            'gpu_utilization_avg_percent': metrics.gpu_utilization_avg,
            'cpu_usage_avg_percent': metrics.cpu_usage_avg,
            'gpu_metrics_count': len(metrics.gpu_metrics_history),
            'gpu_metrics': [
                {
                    'timestamp': m.timestamp,
                    'gpu_id': m.gpu_id,
                    'memory_used_mb': m.memory_used,
                    'memory_total_mb': m.memory_total,
                    'memory_utilization_percent': m.memory_utilization,
                    'gpu_utilization_percent': m.gpu_utilization,
                    'temperature_celsius': m.temperature
                }
                for m in metrics.gpu_metrics_history
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_gpu_metrics_summary() -> Dict[str, float]:
    """Get a quick summary of current GPU metrics"""
    try:
        if not _HAS_GPUTIL or GPUtil is None:
            return {'error': 'GPUtil not available'}

        gpus = GPUtil.getGPUs()
        if not gpus:
            return {'error': 'No GPUs found'}

        gpu = gpus[0]  # Primary GPU
        return {
            'gpu_id': gpu.id,
            'memory_used_mb': gpu.memoryUsed,
            'memory_total_mb': gpu.memoryTotal,
            'memory_utilization_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
            'gpu_utilization_percent': gpu.load * 100,
            'temperature_celsius': gpu.temperature
        }
    except Exception as e:
        return {'error': str(e)}