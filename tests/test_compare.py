from bench.compare import paired


def test_paired_identical_is_zero():
    r = paired([0.5, 0.2, 0.9], [0.5, 0.2, 0.9], n_boot=200)
    assert r["mean_diff"] == 0 and r["ties"] == 3 and r["p_value"] > 0.9


def test_paired_clear_difference():
    a = [1.0] * 50
    b = [0.0] * 50
    r = paired(a, b, n_boot=500)
    assert r["mean_diff"] == 1.0 and r["ci95"] == (1.0, 1.0) and r["p_value"] < 0.01 and r["wins"] == 50


def test_paired_ci90_is_inside_ci95_and_leaves_ci95_unchanged():
    import random

    rng = random.Random(1)
    a = [rng.random() for _ in range(200)]
    b = [x - 0.01 + rng.gauss(0, 0.05) for x in a]
    r = paired(a, b, n_boot=2000)
    assert r["ci95"][0] <= r["ci90"][0] <= r["mean_diff"] <= r["ci90"][1] <= r["ci95"][1]
    # The 90% interval is read from the same bootstrap draws, so the 95% interval and p are as before.
    assert (round(r["ci95"][0], 6), round(r["ci95"][1], 6), round(r["p_value"], 6)) == (-0.000936, 0.01206, 0.090955)  # values from the pre-ci90 code


def test_holm_and_p_formatting():
    from bench.leaderboard import fmt_p
    from bench.stats import holm

    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert holm([0.5]) == [0.5]
    assert fmt_p(1 / 10001) == "p≤0.0001" and fmt_p(0.0002) == "p=0.0002"
