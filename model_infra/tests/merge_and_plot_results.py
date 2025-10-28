#!/usr/bin/env python3
"""
Merge saved stress test JSON results and create comparison visualizations.

Usage:
  python merge_and_plot_results.py --input-dir ../stress_test_results --out combined_results.json

It will look for files matching `detailed_results*.json` or any .json in the input directory,
merge them into a single table keyed by implementation + concurrency + timestamp, and
produce `combined_performance.png` and `combined_results.json` in the same folder.
"""
import argparse
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def load_json_files(input_dir: Path):
    files = sorted([p for p in input_dir.glob("*.json") if p.is_file()])
    all_rows = []
    for p in files:
        try:
            data = json.loads(p.read_text())
            # data may be a list of result entries or a dict; handle both
            if isinstance(data, list):
                for r in data:
                    r_copy = dict(r)
                    r_copy['_source_file'] = p.name
                    all_rows.append(r_copy)
            elif isinstance(data, dict):
                d = dict(data)
                d['_source_file'] = p.name
                all_rows.append(d)
        except Exception as e:
            print(f"Skipping {p.name}: failed to parse JSON ({e})")
    return all_rows


def load_npy_files(input_dir: Path):
    files = sorted([p for p in input_dir.glob("*.npy") if p.is_file()])
    all_rows = []
    for p in files:
        try:
            data = np.load(p, allow_pickle=True)
            # data might be array-like of dicts or list
            for item in data:
                if isinstance(item, dict):
                    d = dict(item)
                    d['_source_file'] = p.name
                    all_rows.append(d)
        except Exception as e:
            print(f"Skipping {p.name}: failed to load NPY ({e})")
    return all_rows


def plot_results(df: pd.DataFrame, out_dir: Path):
    sns.set(style='whitegrid')
    # Ensure numeric
    for col in ['throughput','avg_latency','p95_latency','success_rate']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Plot throughput per implementation
    plt.figure(figsize=(10,6))
    sns.barplot(data=df, x='implementation', y='throughput', ci='sd')
    plt.title('Throughput by Implementation (merged runs)')
    plt.tight_layout()
    plt.savefig(out_dir / 'combined_throughput.png', dpi=200)

    # Plot avg latency per implementation
    plt.figure(figsize=(10,6))
    sns.barplot(data=df, x='implementation', y='avg_latency', ci='sd')
    plt.title('Average Latency by Implementation (merged runs)')
    plt.tight_layout()
    plt.savefig(out_dir / 'combined_avg_latency.png', dpi=200)

    # P95
    if 'p95_latency' in df.columns:
        plt.figure(figsize=(10,6))
        sns.barplot(data=df, x='implementation', y='p95_latency', ci='sd')
        plt.title('P95 Latency by Implementation (merged runs)')
        plt.tight_layout()
        plt.savefig(out_dir / 'combined_p95_latency.png', dpi=200)

    print(f"Saved combined plots to {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, default='stress_test_results', help='Directory with saved JSON results')
    parser.add_argument('--out', type=str, default='combined_results.json', help='Output combined JSON filename (in input-dir)')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Input directory {input_dir} not found")
        return

    rows = load_json_files(input_dir)
    # also load any numpy snapshots
    rows += load_npy_files(input_dir)
    if not rows:
        print("No JSON results found in", input_dir)
        return

    # Normalize rows into a flat table
    df = pd.json_normalize(rows)

    # Compute success_rate if missing
    if 'success_rate' not in df.columns and 'successful_requests' in df.columns and 'total_requests' in df.columns:
        df['success_rate'] = df['successful_requests'] / df['total_requests'] * 100

    # Save combined JSON
    out_path = input_dir / args.out
    out_path.write_text(df.to_json(orient='records', indent=2))
    print(f"Wrote combined results to {out_path}")

    # Create plots
    plot_results(df, input_dir)

if __name__ == '__main__':
    main()
