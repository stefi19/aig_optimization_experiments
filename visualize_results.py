#!/usr/bin/env python3
"""Small visualizations for the AIG optimization experiments.

Produces:
 - results/plots/node_counts.png  (grouped bars: original_nodes, optimized_nodes, exact_internal_matches)
 - results/plots/support_overlap.png (avg_best_support_overlap per optimization)

Requires matplotlib and pandas. Install with:
  pip install matplotlib pandas
"""
import os
import pandas as pd
import matplotlib.pyplot as plt


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def plot_node_counts(summary_df, out_dir):
    """
    Grouped bar chart: original nodes, optimized nodes, and exact internal matches.

    One PNG per benchmark so the axes stay readable even when node counts differ
    a lot between circuits.  The "exact_internal_matches" bar shows how many
    optimized nodes could be paired with an original node that produces an
        identical Boolean signature — a direct measure of structural preservation.
    """
    ensure_dir(out_dir)
    benchmarks = sorted(summary_df['benchmark'].unique())
    optim_order = ['original','balance','rewrite','refactor','resub','resyn2_like']

    for bench in benchmarks:
        df = summary_df[summary_df['benchmark'] == bench].copy()
        # Keep a consistent order
        df['opt_order'] = df['optimization'].apply(lambda x: optim_order.index(x) if x in optim_order else 999)
        df = df.sort_values('opt_order')

        x = range(len(df))
        width = 0.25

        plt.figure(figsize=(10,4))
        plt.bar([i - width for i in x], df['original_nodes'], width, label='original_nodes')
        plt.bar(x, df['optimized_nodes'], width, label='optimized_nodes')
        plt.bar([i + width for i in x], df['exact_internal_matches'], width, label='exact_internal_matches')

        plt.xticks(x, df['optimization'], rotation=30)
        plt.ylabel('nodes / exact matches')
        plt.title(f'Node counts and exact matches — {bench}')
        plt.legend()
        plt.tight_layout()
        out = os.path.join(out_dir, f'{bench}_node_counts.png')
        plt.savefig(out)
        plt.close()


def plot_support_overlap(summary_df, out_dir):
    """
    Line chart: avg_best_support_overlap across optimizations, one line per benchmark.

    Support overlap (Jaccard between input cones) stays meaningful even when
    simulation signatures diverge after aggressive rewriting.  A line that stays
    close to 1.0 means the optimization rearranged gates but left the dependency
    structure largely intact — those circuits are the best candidates for SAT.
    """
    ensure_dir(out_dir)
    benchmarks = sorted(summary_df['benchmark'].unique())
    optim_order = ['original','balance','rewrite','refactor','resub','resyn2_like']

    plt.figure(figsize=(10,5))

    for bench in benchmarks:
        df = summary_df[summary_df['benchmark'] == bench].copy()
        df['opt_order'] = df['optimization'].apply(lambda x: optim_order.index(x) if x in optim_order else 999)
        df = df.sort_values('opt_order')
        plt.plot(df['optimization'], df['avg_best_support_overlap'], marker='o', label=bench)

    plt.ylabel('avg_best_support_overlap')
    plt.title('Support overlap per optimization')
    plt.xticks(rotation=30)
    plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.tight_layout()
    out = os.path.join(out_dir, 'support_overlap.png')
    plt.savefig(out)
    plt.close()


def main():
    summary_path = 'results/summary_metrics.csv'
    if not os.path.exists(summary_path):
        print('Missing', summary_path)
        return

    summary_df = pd.read_csv(summary_path)
    out_dir = 'results/plots'
    plot_node_counts(summary_df, out_dir)
    plot_support_overlap(summary_df, out_dir)
    print('Saved plots to', out_dir)


if __name__ == '__main__':
    main()
