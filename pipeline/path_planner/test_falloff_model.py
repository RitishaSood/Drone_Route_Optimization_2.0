from __future__ import annotations

from pipeline.path_planner.vehicle_model import FalloffConfig, compute_falloff_probability


def main() -> int:
    soft = FalloffConfig()
    assert 0.0 <= compute_falloff_probability(0.0, soft) <= 1.0
    assert compute_falloff_probability(0.0, soft) >= 0.9
    mid = compute_falloff_probability(soft.R0, soft)
    assert 0.0 < mid < 1.0
    assert compute_falloff_probability(10_000.0, FalloffConfig(use_hard_range_cutoff=False)) >= 0.0
    hard = FalloffConfig(use_hard_range_cutoff=True)
    assert compute_falloff_probability(hard.max_range + 1.0, hard) == 0.0
    exp = FalloffConfig(falloff_model="exponential", decay_k=10.0)
    gau = FalloffConfig(falloff_model="gaussian", sigma=10.0)
    assert compute_falloff_probability(0.0, exp) <= 1.0
    assert compute_falloff_probability(0.0, gau) <= 1.0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
