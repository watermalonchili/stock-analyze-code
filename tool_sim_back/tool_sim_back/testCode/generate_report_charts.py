"""Generate high-resolution performance comparison and speed-up charts for deliverables."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from test_pipeline_common import OUTPUT_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Data ----
stages = ['YOLO Screening\n(Stage 1)', 'DTW Ranking\n(Stage 2)', 'Two-Model Fusion\n(Stage 3)']
precision = [85.4, 87.6, 85.6]
recall = [86.9, 97.7, 94.0]
f1 = [86.1, 92.4, 89.6]
target_p = [80, 85, 82]
target_r = [90, 75, 85]
target_f1 = [72, 80, 83]

# ---- Chart 1: Performance Comparison ----
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
x = np.arange(len(stages))
w = 0.22

bars_p = ax.bar(x - w, precision, w, label='Precision (%)', color='#4472C4', edgecolor='white', linewidth=0.5)
bars_r = ax.bar(x, recall, w, label='Recall (%)', color='#ED7D31', edgecolor='white', linewidth=0.5)
bars_f1 = ax.bar(x + w, f1, w, label='F1-Score (%)', color='#A5A5A5', edgecolor='white', linewidth=0.5)

# Target markers
for i in range(3):
    ax.scatter(x[i] - w, target_p[i], marker='_', s=200, c='#1F3864', linewidth=2, zorder=5)
    ax.scatter(x[i], target_r[i], marker='_', s=200, c='#7B3F00', linewidth=2, zorder=5)
    ax.scatter(x[i] + w, target_f1[i], marker='_', s=200, c='#404040', linewidth=2, zorder=5)

def _label(bars, offset_y=1.0):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset_y, f'{h:.1f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

_label(bars_p, 0.8)
_label(bars_r, 0.8)
_label(bars_f1, 0.8)

ax.set_xticks(x)
ax.set_xticklabels(stages, fontsize=11)
ax.set_ylabel('Score (%)', fontsize=12)
ax.set_title('W-Bottom Detection -- Three-Stage Performance Comparison', fontsize=14, fontweight='bold', pad=15)
ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax.set_ylim(60, 105)
ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
out_path1 = os.path.join(OUTPUT_DIR, 'performance_comparison.png')
fig.savefig(out_path1, dpi=300, facecolor='white', pad_inches=0.2)
plt.close(fig)
print(f'[OK] {out_path1}')

# ---- Chart 2: Speed-Up Comparison ----
fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
methods = ['Pure DTW Full Scan\n(Stage 2)', 'Two-Model Fusion\n(Stage 3)']
times = [6.34, 0.332]
bar_colors = ['#C00000', '#2E75B6']

bars = ax.barh(methods, times, color=bar_colors, edgecolor='white', height=0.45)

for bar, t in zip(bars, times):
    ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
            f'{t:.3f}s', va='center', fontsize=12, fontweight='bold')

speedup = times[0] / times[1]
ax.annotate(f'{speedup:.1f}x Speed-Up', xy=(0.4, 1.4),
            fontsize=16, fontweight='bold', color='#2E75B6',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#DAEEF3', edgecolor='#2E75B6', alpha=0.9))

ax.set_title('W-Bottom Detection -- Fusion Speed-Up vs Pure DTW', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Time per Stock (seconds)', fontsize=12)
ax.set_xlim(0, 8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.3, linestyle='--')

plt.tight_layout()
out_path2 = os.path.join(OUTPUT_DIR, 'speed_up_comparison.png')
fig.savefig(out_path2, dpi=300, facecolor='white', pad_inches=0.2)
plt.close(fig)
print(f'[OK] {out_path2}')
