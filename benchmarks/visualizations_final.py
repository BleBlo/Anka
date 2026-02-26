"""Generate final publication-quality figures including multi-model validation."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11


def plot_multi_model_comparison(output_dir='benchmarks/figures'):
    """Compare Anka advantage across models."""

    Path(output_dir).mkdir(exist_ok=True)

    models = ['Claude 3.5\nHaiku', 'GPT-4o\nmini']
    anka_advantage = [40, 26.7]

    fig, ax = plt.subplots(figsize=(7, 5))

    colors = ['#9b59b6', '#3498db']
    bars = ax.bar(models, anka_advantage, color=colors, edgecolor='black', linewidth=0.5, width=0.5)

    ax.set_ylabel('Anka Advantage on Multi-Step Tasks\n(percentage points)', fontsize=11)
    ax.set_title('Anka Advantage Confirmed Across LLM Models', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 50)

    # Add value labels
    for bar, adv in zip(bars, anka_advantage):
        ax.annotate(f'+{adv:.1f}%', xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 1),
                    ha='center', va='bottom', fontsize=14, fontweight='bold', color='#27ae60')

    # Add average line
    avg = sum(anka_advantage) / len(anka_advantage)
    ax.axhline(y=avg, color='#e74c3c', linestyle='--', linewidth=2, label=f'Average: +{avg:.1f}%')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/multi_model_advantage.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/multi_model_advantage.pdf', bbox_inches='tight')
    print(f"Saved: {output_dir}/multi_model_advantage.png")
    plt.close()


def plot_headline_figure(output_dir='benchmarks/figures'):
    """Create the main headline figure for paper."""

    Path(output_dir).mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Multi-step comparison
    ax1 = axes[0]
    categories = ['Claude\nHaiku', 'GPT-4o\nmini']
    anka = [100, 86.7]
    python = [60, 60]

    x = np.arange(len(categories))
    width = 0.35

    ax1.bar(x - width/2, anka, width, label='Anka', color='#2ecc71', edgecolor='black')
    ax1.bar(x + width/2, python, width, label='Python', color='#3498db', edgecolor='black')

    ax1.set_ylabel('Accuracy (%)', fontsize=12)
    ax1.set_title('Multi-Step Pipeline Tasks', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend(loc='lower right')
    ax1.set_ylim(0, 115)

    # Add annotations
    ax1.annotate('+40%', xy=(0, 105), ha='center', fontsize=12, fontweight='bold', color='#27ae60')
    ax1.annotate('+27%', xy=(1, 92), ha='center', fontsize=12, fontweight='bold', color='#27ae60')

    # Right: Overall comparison
    ax2 = axes[1]
    languages = ['Anka', 'Python']
    overall = [95.8, 91.2]

    colors = ['#2ecc71', '#3498db']
    bars = ax2.bar(languages, overall, color=colors, edgecolor='black', width=0.5)

    ax2.set_ylabel('Accuracy (%)', fontsize=12)
    ax2.set_title('Overall Accuracy\n(Claude 3.5 Haiku)', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, 105)

    for bar, score in zip(bars, overall):
        ax2.annotate(f'{score:.1f}%', xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 1),
                    ha='center', va='bottom', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/headline_figure.png', dpi=300, bbox_inches='tight')
    plt.savefig(f'{output_dir}/headline_figure.pdf', bbox_inches='tight')
    print(f"Saved: {output_dir}/headline_figure.png")
    plt.close()


if __name__ == '__main__':
    plot_multi_model_comparison()
    plot_headline_figure()
    print("\nFinal figures generated!")
