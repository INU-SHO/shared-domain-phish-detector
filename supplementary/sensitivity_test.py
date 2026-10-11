import numpy as np
from scipy import stats


DATA = {
    "GPT-4.1-mini": {
        "Financial": np.array([
            0.98, 0.97, 0.95, 0.95, 0.95, 0.96, 0.96, 0.95, 0.96, 0.96
        ]),
        "Online Service": np.array([
            0.97, 0.95, 0.98, 0.95, 0.97, 0.96, 0.95, 0.97, 0.96, 0.96
        ]),
        "Telecommunication": np.array([
            0.96, 0.96, 0.97, 0.98, 0.95, 0.95, 0.96, 0.96, 0.95, 0.97
        ]),
    },
    "Qwen3-8B": {
        "Financial": np.array([
            0.78, 0.82, 0.75, 0.78, 0.77, 0.83, 0.81, 0.80, 0.77, 0.80
        ]),
        "Online Service": np.array([
            0.77, 0.78, 0.81, 0.77, 0.86, 0.84, 0.80, 0.82, 0.83, 0.81
        ]),
        "Telecommunication": np.array([
            0.80, 0.78, 0.75, 0.78, 0.75, 0.77, 0.78, 0.81, 0.84, 0.77
        ]),
    },
}


def summarize(name, data):
    """Print mean +/- std for a single group."""
    print(f"  {name:20s}: mean = {data.mean():.4f}, "
          f"std = {data.std(ddof=1):.4f}, "
          f"min = {data.min():.4f}, max = {data.max():.4f}")


def run_tests_for_model(model_name, groups):
    """Run the full battery of tests for one model."""
    print("\n" + "=" * 70)
    print(f"Model: {model_name}")
    print("=" * 70)

    industries = list(groups.keys())
    arrays = [groups[ind] for ind in industries]

    # Descriptive statistics
    print("\n[Descriptive Statistics]")
    for ind, arr in zip(industries, arrays):
        summarize(ind, arr)

    means = [arr.mean() for arr in arrays]
    within_stds = [arr.std(ddof=1) for arr in arrays]
    between_std = float(np.std(means, ddof=1))
    within_std = float(np.mean(within_stds))
    print(f"\n  Between-industry std : {between_std:.4f}")
    print(f"  Within-industry std  : {within_std:.4f}")
    print(f"  Range of group means : {max(means) - min(means):.4f}  (informational)")
    print(f"  Ratio (within-std / between-std): "
          f"{within_std / between_std:.2f}x")

    # Kruskal-Wallis H-test (primary)
    print("\n[Kruskal-Wallis H-test (primary)]")
    print("  H0: The three industries have the same distribution of Accuracy.")
    h_stat, p_kw = stats.kruskal(*arrays)
    print(f"  H statistic : {h_stat:.4f}")
    print(f"  p-value     : {p_kw:.4f}")
    verdict_kw = ("Reject H0 (significant difference)" if p_kw < 0.05
                  else "Fail to reject H0 (no significant difference)")
    print(f"  Conclusion  : {verdict_kw}")

    # One-way ANOVA (secondary)
    print("\n[One-way ANOVA (cross-check)]")
    print("  H0: The three industries have the same mean Accuracy.")
    f_stat, p_anova = stats.f_oneway(*arrays)
    print(f"  F statistic : {f_stat:.4f}")
    print(f"  p-value     : {p_anova:.4f}")
    verdict_anova = ("Reject H0 (significant difference)" if p_anova < 0.05
                     else "Fail to reject H0 (no significant difference)")
    print(f"  Conclusion  : {verdict_anova}")


    return {
        "model": model_name,
        "means": means,
        "within_stds": within_stds,
        "kw_H": h_stat, "kw_p": p_kw,
        "anova_F": f_stat, "anova_p": p_anova,
    }


def print_summary_table(results):
    """Print a side-by-side summary across models."""
    print("\n\n" + "=" * 70)
    print("Cross-Model Summary")
    print("=" * 70)
    header = (f"{'Model':<15} {'Between-std':<13} {'Within-std':<12} "
              f"{'KW H':<10} {'KW p':<10} {'ANOVA F':<10} {'ANOVA p':<10}")
    print(header)
    print("-" * len(header))
    for r in results:
        bstd = float(np.std(r["means"], ddof=1))
        wstd = float(np.mean(r["within_stds"]))
        print(f"{r['model']:<15} {bstd:<13.4f} {wstd:<12.4f} "
              f"{r['kw_H']:<10.4f} {r['kw_p']:<10.4f} "
              f"{r['anova_F']:<10.4f} {r['anova_p']:<10.4f}")


def main():
    print("=" * 70)
    print("Sensitivity Analysis: Reference Brand Industry Effect on Accuracy")
    print("=" * 70)
    print("Comparing two LLMs across three reference brand industries.")

    results = []
    for model_name, groups in DATA.items():
        result = run_tests_for_model(model_name, groups)
        results.append(result)

    print_summary_table(results)


if __name__ == "__main__":
    main()
