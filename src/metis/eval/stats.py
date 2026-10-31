"""Statistics for the evaluation protocol (PLAN section 8.3, spec section P criteria C and D)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.stats import binomtest, norm, spearmanr
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score

from metis.router.select_k import fit_psi, halvings


@dataclass(frozen=True)
class BootResult:
    estimate: float
    low: float
    high: float
    se: float
    n_boot: int
    seed: int

    def excludes_zero(self) -> bool:
        return self.low > 0 or self.high < 0


def session_resample(groups: np.ndarray, seed: int) -> Callable[[], np.ndarray]:
    """A function giving one bootstrap sample of prompt indices, drawing whole sessions (D-060)."""
    rng = np.random.default_rng(seed)
    members = np.argsort(groups, kind="stable")
    _, starts, sizes = np.unique(groups[members], return_index=True, return_counts=True)

    def draw() -> np.ndarray:
        picked = rng.integers(len(sizes), size=len(sizes))
        lengths = sizes[picked]
        ends = np.cumsum(lengths)
        offset = np.arange(ends[-1]) - np.repeat(ends - lengths, lengths)
        return members[np.repeat(starts[picked], lengths) + offset]

    return draw


def bootstrap(
    statistic: Callable[[np.ndarray], float],
    groups: np.ndarray,
    n_boot: int = 10_000,
    seed: int = 20261020,
    confidence: float = 0.95,
) -> BootResult:
    """Percentile interval of `statistic(indices)`. For a difference, compute both sides on the
    same indices: that is what makes the comparison paired."""
    groups = np.asarray(groups)
    draw = session_resample(groups, seed)
    values = np.array([statistic(draw()) for _ in range(n_boot)])
    tail = (1 - confidence) / 2 * 100
    low, high = np.percentile(values, [tail, 100 - tail])
    estimate = statistic(np.arange(len(groups)))
    return BootResult(float(estimate), float(low), float(high), float(values.std()), n_boot, seed)


def mcnemar_exact(pass_a: np.ndarray, pass_b: np.ndarray) -> tuple[int, int, float]:
    """(a only, b only, two-sided exact p). Treats prompts as independent, unlike the bootstrap."""
    pass_a, pass_b = np.asarray(pass_a, bool), np.asarray(pass_b, bool)
    only_a = int((pass_a & ~pass_b).sum())
    only_b = int((pass_b & ~pass_a).sum())
    if only_a + only_b == 0:
        return 0, 0, 1.0
    return only_a, only_b, float(binomtest(only_a, only_a + only_b, 0.5).pvalue)


def wilson_ci(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    z = float(norm.ppf(1 - (1 - confidence) / 2))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def cohen_kappa(a: np.ndarray, b: np.ndarray) -> float:
    return float(cohen_kappa_score(a, b))


def balanced_accuracy(truth: np.ndarray, predicted: np.ndarray) -> float:
    return float(balanced_accuracy_score(truth, predicted))


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return float(spearmanr(a, b).statistic)


def fingerprint_stability(
    losses: np.ndarray,
    labels: np.ndarray,
    k: int,
    seed: int,
    repeats: int = 5,
    groups: np.ndarray | None = None,
    method: str = "pt",
    anchor: int | None = None,
) -> float:
    """Criterion C: mean Pearson correlation of the Psi tables of two halves."""
    values = []
    for part_a, part_b in halvings(len(losses), repeats, seed, groups):
        psi_a = fit_psi(losses[part_a], labels[part_a], k, method, anchor=anchor)
        psi_b = fit_psi(losses[part_b], labels[part_b], k, method, anchor=anchor)
        values.append(np.corrcoef(psi_a.ravel(), psi_b.ravel())[0, 1])
    return float(np.mean(values))


def separability(psi: np.ndarray, counts: np.ndarray) -> float:
    """Criterion D: share of (cluster, model pair) cells that differ by more than 2 SE."""
    filled = counts > 0
    psi, counts = psi[filled], counts[filled]
    variance = psi * (1 - psi) / counts[:, None]
    first, second = np.triu_indices(psi.shape[1], k=1)
    gap = np.abs(psi[:, first] - psi[:, second])
    return float((gap > 2 * np.sqrt(variance[:, first] + variance[:, second])).mean())
