from bench.compare import paired


def test_paired_identical_is_zero():
    r = paired([0.5, 0.2, 0.9], [0.5, 0.2, 0.9], n_boot=200)
    assert r["mean_diff"] == 0 and r["ties"] == 3 and r["p_value"] > 0.9


def test_paired_clear_difference():
    a = [1.0] * 50
    b = [0.0] * 50
    r = paired(a, b, n_boot=500)
    assert r["mean_diff"] == 1.0 and r["ci95"] == (1.0, 1.0) and r["p_value"] < 0.01 and r["wins"] == 50
