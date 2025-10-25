#!/usr/bin/env python3
"""
Performance Analysis and Visualization for DeepSeek-OCR Stress Tests

This script analyzes stress test results and creates comprehensive visualizations
comparing modal_base.py vs modal_app.py performance.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class PerformanceAnalyzer:
    """Analyzes and visualizes performance test results"""

    def __init__(self, results_dir: str = "stress_test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

        # Set up plotting styles
        plt.style.use('default')
        sns.set_palette("husl")
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    def load_results(self, results_file: str = "detailed_results.json") -> pd.DataFrame:
        """Load test results from JSON file"""
        results_path = self.results_dir / results_file

        if not results_path.exists():
            raise FileNotFoundError(f"Results file not found: {results_path}")

        with open(results_path, 'r') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        # Add derived metrics
        df['success_rate'] = (df['successful_requests'] / df['total_requests'] * 100).round(2)
        df['error_rate'] = (df['failed_requests'] / df['total_requests'] * 100).round(2)
        df['efficiency'] = (df['throughput'] / df['avg_latency']).round(4)

        return df

    def create_comprehensive_dashboard(self, df: pd.DataFrame):
        """Create a comprehensive dashboard with multiple visualizations"""
        implementations = df['implementation'].unique()

        # Create subplots
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Throughput vs Concurrency', 'Average Latency vs Concurrency',
                'P95 Latency vs Concurrency', 'Success Rate vs Concurrency',
                'GPU Memory Usage', 'GPU Utilization',
                'Latency Distribution', 'Throughput Distribution', 'Performance Summary'
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}, {"type": "table"}]
            ]
        )

        # Color mapping
        color_map = {impl: self.colors[i] for i, impl in enumerate(implementations)}

        # 1. Throughput vs Concurrency
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            fig.add_trace(
                go.Scatter(
                    x=impl_data['concurrency'],
                    y=impl_data['throughput'],
                    mode='lines+markers',
                    name=f'{impl.upper()} Throughput',
                    line=dict(color=color_map[impl], width=3),
                    marker=dict(size=8),
                    legendgroup=impl
                ),
                row=1, col=1
            )

        # 2. Average Latency vs Concurrency
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            fig.add_trace(
                go.Scatter(
                    x=impl_data['concurrency'],
                    y=impl_data['avg_latency'],
                    mode='lines+markers',
                    name=f'{impl.upper()} Avg Latency',
                    line=dict(color=color_map[impl], width=3, dash='dash'),
                    marker=dict(size=8),
                    legendgroup=impl,
                    showlegend=False
                ),
                row=1, col=2
            )

        # 3. P95 Latency vs Concurrency
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            fig.add_trace(
                go.Scatter(
                    x=impl_data['concurrency'],
                    y=impl_data['p95_latency'],
                    mode='lines+markers',
                    name=f'{impl.upper()} P95 Latency',
                    line=dict(color=color_map[impl], width=3, dash='dot'),
                    marker=dict(size=8),
                    legendgroup=impl,
                    showlegend=False
                ),
                row=1, col=3
            )

        # 4. Success Rate vs Concurrency
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            fig.add_trace(
                go.Scatter(
                    x=impl_data['concurrency'],
                    y=impl_data['success_rate'],
                    mode='lines+markers',
                    name=f'{impl.upper()} Success Rate',
                    line=dict(color=color_map[impl], width=3, dash='dashdot'),
                    marker=dict(size=8),
                    legendgroup=impl,
                    showlegend=False
                ),
                row=2, col=1
            )

        # 5. GPU Memory Usage (placeholder - would need GPU metrics data)
        fig.add_trace(
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[0, 0, 0, 0, 0],
                mode='lines',
                name='GPU Memory (MB)',
                line=dict(color='red', width=2),
                showlegend=False
            ),
            row=2, col=2
        )

        # 6. GPU Utilization (placeholder)
        fig.add_trace(
            go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[0, 0, 0, 0, 0],
                mode='lines',
                name='GPU Utilization (%)',
                line=dict(color='orange', width=2),
                showlegend=False
            ),
            row=2, col=3
        )

        # 7. Latency Distribution
        latency_data = []
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            latency_data.append(
                go.Box(
                    y=impl_data['avg_latency'],
                    name=f'{impl.upper()}',
                    marker_color=color_map[impl]
                )
            )
        for trace in latency_data:
            fig.add_trace(trace, row=3, col=1)

        # 8. Throughput Distribution
        throughput_data = []
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            throughput_data.append(
                go.Box(
                    y=impl_data['throughput'],
                    name=f'{impl.upper()}',
                    marker_color=color_map[impl],
                    showlegend=False
                )
            )
        for trace in throughput_data:
            fig.add_trace(trace, row=3, col=2)

        # 9. Performance Summary Table
        summary_data = []
        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            summary_data.append([
                impl.upper(),
                f"{impl_data['throughput'].mean():.2f}",
                f"{impl_data['throughput'].max():.2f}",
                f"{impl_data['avg_latency'].mean():.2f}s",
                f"{impl_data['p95_latency'].mean():.2f}s",
                f"{impl_data['success_rate'].mean():.1f}%"
            ])

        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Implementation', 'Avg Throughput<br>(req/sec)', 'Peak Throughput<br>(req/sec)',
                           'Avg Latency<br>(sec)', 'Avg P95 Latency<br>(sec)', 'Success Rate'],
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=np.array(summary_data).T,
                    fill_color='white',
                    align='center',
                    font=dict(size=11)
                )
            ),
            row=3, col=3
        )

        # Update layout
        fig.update_layout(
            height=1200,
            width=1600,
            title_text="DeepSeek-OCR Performance Comparison Dashboard",
            title_x=0.5,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Update axes labels
        fig.update_xaxes(title_text="Concurrency Level", row=1, col=1)
        fig.update_xaxes(title_text="Concurrency Level", row=1, col=2)
        fig.update_xaxes(title_text="Concurrency Level", row=1, col=3)
        fig.update_xaxes(title_text="Concurrency Level", row=2, col=1)

        fig.update_yaxes(title_text="Throughput (req/sec)", row=1, col=1)
        fig.update_yaxes(title_text="Latency (seconds)", row=1, col=2)
        fig.update_yaxes(title_text="P95 Latency (seconds)", row=1, col=3)
        fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1)

        fig.update_yaxes(title_text="GPU Memory (MB)", row=2, col=2)
        fig.update_yaxes(title_text="GPU Utilization (%)", row=2, col=3)

        fig.update_yaxes(title_text="Latency (seconds)", row=3, col=1)
        fig.update_yaxes(title_text="Throughput (req/sec)", row=3, col=2)

        return fig

    def create_matplotlib_comparison(self, df: pd.DataFrame):
        """Create matplotlib-based comparison plots"""
        implementations = df['implementation'].unique()

        # Set up the plotting area
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('DeepSeek-OCR Performance Comparison (Matplotlib)', fontsize=16, fontweight='bold')

        # Colors for implementations
        colors = ['blue', 'orange']

        # 1. Throughput vs Concurrency
        ax = axes[0, 0]
        for i, impl in enumerate(implementations):
            impl_data = df[df['implementation'] == impl]
            ax.plot(impl_data['concurrency'], impl_data['throughput'],
                   marker='o', linewidth=2, markersize=8, color=colors[i], label=f'{impl.upper()}')
        ax.set_xlabel('Concurrency Level')
        ax.set_ylabel('Throughput (req/sec)')
        ax.set_title('Throughput vs Concurrency')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Average Latency vs Concurrency
        ax = axes[0, 1]
        for i, impl in enumerate(implementations):
            impl_data = df[df['implementation'] == impl]
            ax.plot(impl_data['concurrency'], impl_data['avg_latency'],
                   marker='s', linewidth=2, markersize=8, color=colors[i], label=f'{impl.upper()}')
        ax.set_xlabel('Concurrency Level')
        ax.set_ylabel('Average Latency (seconds)')
        ax.set_title('Average Latency vs Concurrency')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. P95 Latency vs Concurrency
        ax = axes[0, 2]
        for i, impl in enumerate(implementations):
            impl_data = df[df['implementation'] == impl]
            ax.plot(impl_data['concurrency'], impl_data['p95_latency'],
                   marker='^', linewidth=2, markersize=8, color=colors[i], label=f'{impl.upper()}')
        ax.set_xlabel('Concurrency Level')
        ax.set_ylabel('P95 Latency (seconds)')
        ax.set_title('P95 Latency vs Concurrency')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 4. Success Rate vs Concurrency
        ax = axes[1, 0]
        for i, impl in enumerate(implementations):
            impl_data = df[df['implementation'] == impl]
            ax.plot(impl_data['concurrency'], impl_data['success_rate'],
                   marker='d', linewidth=2, markersize=8, color=colors[i], label=f'{impl.upper()}')
        ax.set_xlabel('Concurrency Level')
        ax.set_ylabel('Success Rate (%)')
        ax.set_title('Success Rate vs Concurrency')
        ax.set_ylim(0, 105)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 5. Latency Distribution
        ax = axes[1, 1]
        latency_data = [df[df['implementation'] == impl]['avg_latency'] for impl in implementations]
        ax.boxplot(latency_data, labels=[impl.upper() for impl in implementations])
        ax.set_ylabel('Latency (seconds)')
        ax.set_title('Latency Distribution')
        ax.grid(True, alpha=0.3)

        # 6. Throughput Distribution
        ax = axes[1, 2]
        throughput_data = [df[df['implementation'] == impl]['throughput'] for impl in implementations]
        ax.boxplot(throughput_data, labels=[impl.upper() for impl in implementations])
        ax.set_ylabel('Throughput (req/sec)')
        ax.set_title('Throughput Distribution')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def generate_performance_report(self, df: pd.DataFrame) -> str:
        """Generate a detailed performance report"""
        report = []
        report.append("# DeepSeek-OCR Performance Comparison Report")
        report.append("=" * 60)
        report.append("")

        implementations = df['implementation'].unique()

        for impl in implementations:
            impl_data = df[df['implementation'] == impl]
            report.append(f"## {impl.upper()} Implementation Analysis")
            report.append("-" * 40)

            # Basic statistics
            report.append("### Performance Metrics:")
            report.append(f"- **Average Throughput**: {impl_data['throughput'].mean():.2f} req/sec")
            report.append(f"- **Peak Throughput**: {impl_data['throughput'].max():.2f} req/sec")
            report.append(f"- **Average Latency**: {impl_data['avg_latency'].mean():.2f} seconds")
            report.append(f"- **P95 Latency**: {impl_data['p95_latency'].mean():.2f} seconds")
            report.append(f"- **Success Rate**: {impl_data['success_rate'].mean():.1f}%")
            report.append(f"- **Efficiency**: {impl_data['efficiency'].mean():.4f} (throughput/latency)")
            report.append("")

            # Concurrency analysis
            report.append("### Concurrency Scaling:")
            for _, row in impl_data.iterrows():
                report.append(f"- Concurrency {int(row['concurrency'])}: "
                            f"{row['throughput']:.2f} req/sec, "
                            f"{row['avg_latency']:.2f}s latency, "
                            f"{row['success_rate']:.1f}% success")
            report.append("")

        # Comparative analysis
        report.append("## Comparative Analysis")
        report.append("-" * 30)

        base_data = df[df['implementation'] == 'base']
        app_data = df[df['implementation'] == 'app']

        if not base_data.empty and not app_data.empty:
            throughput_improvement = (app_data['throughput'].mean() - base_data['throughput'].mean()) / base_data['throughput'].mean() * 100
            latency_improvement = (base_data['avg_latency'].mean() - app_data['avg_latency'].mean()) / base_data['avg_latency'].mean() * 100

            report.append(f"- **Throughput Improvement**: {throughput_improvement:+.1f}% (APP vs BASE)")
            report.append(f"- **Latency Improvement**: {latency_improvement:+.1f}% (APP vs BASE)")
            report.append("")

            if throughput_improvement > 0:
                report.append("📈 **APP implementation shows better throughput performance**")
            else:
                report.append("📉 **BASE implementation shows better throughput performance**")

            if latency_improvement > 0:
                report.append("⚡ **APP implementation shows lower latency**")
            else:
                report.append("🐌 **BASE implementation shows lower latency**")

        report.append("")
        report.append("### Recommendations:")
        report.append("Based on the performance data, consider the following:")

        # Simple recommendations based on data
        avg_throughput = df.groupby('implementation')['throughput'].mean()
        best_throughput = avg_throughput.idxmax()

        avg_latency = df.groupby('implementation')['avg_latency'].mean()
        best_latency = avg_latency.idxmin()

        if best_throughput == best_latency:
            report.append(f"- Use **{best_throughput.upper()}** implementation for balanced performance")
        else:
            report.append(f"- Use **{best_throughput.upper()}** for maximum throughput")
            report.append(f"- Use **{best_latency.upper()}** for minimum latency")

        # Memory efficiency considerations
        report.append("- Consider memory constraints when choosing batch sizes")
        report.append("- Monitor GPU utilization for optimal resource usage")

        return "\n".join(report)

    def save_all_visualizations(self, df: pd.DataFrame):
        """Save all visualizations and reports"""
        # Create plotly dashboard
        plotly_fig = self.create_comprehensive_dashboard(df)
        plotly_fig.write_html(str(self.results_dir / "performance_dashboard.html"))
        plotly_fig.write_image(str(self.results_dir / "performance_dashboard.png"))

        # Create matplotlib plots
        plt_fig = self.create_matplotlib_comparison(df)
        plt_fig.savefig(str(self.results_dir / "performance_comparison.png"), dpi=300, bbox_inches='tight')
        plt.close(plt_fig)

        # Generate and save report
        report = self.generate_performance_report(df)
        with open(self.results_dir / "performance_report.md", 'w') as f:
            f.write(report)

        print("✅ All visualizations and reports saved to:", self.results_dir)

def main():
    """Main analysis function"""
    analyzer = PerformanceAnalyzer()

    try:
        # Load results
        df = analyzer.load_results()
        print(f"📊 Loaded {len(df)} test results")
        print(df.head())

        # Generate all visualizations and reports
        analyzer.save_all_visualizations(df)

        print("\n🎯 Analysis complete!")
        print("Generated files:")
        print("- performance_dashboard.html (Interactive dashboard)")
        print("- performance_dashboard.png (Static dashboard image)")
        print("- performance_comparison.png (Matplotlib comparison)")
        print("- performance_report.md (Detailed analysis report)")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure to run stress_test.py first to generate results.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()