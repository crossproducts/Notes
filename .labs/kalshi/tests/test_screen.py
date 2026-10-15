"""Tests for the series gate."""

import random
import unittest

from kalshi_lab.calibration import bootstrap_paired_improvement
from kalshi_lab.screen import calibration_by_price_bucket, screen_series


def _make_series(n_events, strikes, skill, seed=1):
    """Synthetic settled history.

    `skill` shrinks the model's forecast toward the truth: 0.0 means the model
    just repeats the market price, 1.0 means it knows the outcome.
    """
    rng = random.Random(seed)
    model, market, outs, events = [], [], [], []
    for e in range(n_events):
        p = rng.uniform(0.15, 0.85)
        outcome = 1 if rng.random() < p else 0
        for _ in range(strikes):
            price = min(max(p + rng.uniform(-0.04, 0.04), 0.01), 0.99)
            market.append(price)
            model.append(price + skill * (outcome - price))
            outs.append(outcome)
            events.append(e)
    return model, market, outs, events


class TestScreenSeries(unittest.TestCase):
    def test_a_model_that_only_echoes_the_price_is_rejected(self):
        model, market, outs, events = _make_series(60, 20, skill=0.0)
        v = screen_series("KXECHO", model, market, outs, events, n_resamples=300, seed=1)
        self.assertFalse(v.passed)
        self.assertTrue(any("no skill" in r or "not significant" in r for r in v.reasons))

    def test_a_genuinely_skilled_model_passes(self):
        model, market, outs, events = _make_series(60, 20, skill=0.5)
        v = screen_series("KXSKILL", model, market, outs, events, n_resamples=300, seed=1)
        self.assertTrue(v.passed, v.summary())
        self.assertGreater(v.brier_skill_score, 0)
        self.assertGreater(v.skill_ci[0], 0)

    def test_skill_on_too_few_events_is_rejected_for_sample_size(self):
        # Real skill, but only 8 events: the gate must still refuse.
        model, market, outs, events = _make_series(8, 50, skill=0.5)
        v = screen_series("KXTHIN", model, market, outs, events, n_resamples=300, seed=1)
        self.assertFalse(v.passed)
        self.assertTrue(any("distinct events" in r for r in v.reasons))

    def test_counts_events_not_contracts(self):
        model, market, outs, events = _make_series(12, 40, skill=0.3)
        v = screen_series("KXCOUNT", model, market, outs, events, n_resamples=100, seed=1)
        self.assertEqual(v.n_contracts, 480)
        self.assertEqual(v.n_events, 12)

    def test_rejection_reasons_are_diagnostic(self):
        model, market, outs, events = _make_series(5, 10, skill=0.0)
        v = screen_series("KXWHY", model, market, outs, events, n_resamples=100, seed=1)
        self.assertFalse(v.passed)
        self.assertTrue(v.reasons)
        self.assertIn("REJECT", v.summary())

    def test_net_edge_subtracts_the_fee_hurdle(self):
        model, market, outs, events = _make_series(40, 10, skill=0.4)
        v = screen_series("KXNET", model, market, outs, events, n_resamples=100, seed=1)
        self.assertAlmostEqual(v.net_edge, v.mean_edge - v.mean_fee_hurdle, places=12)

    def test_mismatched_input_lengths_raise(self):
        with self.assertRaises(ValueError):
            screen_series("KXBAD", [0.5, 0.5], [0.5], [1, 0], [1, 1])


class TestPairedBootstrap(unittest.TestCase):
    def test_identical_forecasts_give_an_interval_around_zero(self):
        _, market, outs, events = _make_series(30, 10, skill=0.0)
        lo, hi = bootstrap_paired_improvement(
            market, market, outs, events, n_resamples=200, seed=1
        )
        self.assertLessEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.0)

    def test_clustering_widens_the_improvement_interval(self):
        model, market, outs, events = _make_series(30, 25, skill=0.3)
        naive = bootstrap_paired_improvement(
            model, market, outs, None, n_resamples=300, seed=1
        )
        clustered = bootstrap_paired_improvement(
            model, market, outs, events, n_resamples=300, seed=1
        )
        self.assertGreater(clustered[1] - clustered[0], naive[1] - naive[0])


class TestMarketCalibrationBuckets(unittest.TestCase):
    def test_overpriced_longshots_show_a_negative_gap_in_low_bins(self):
        # 8c contracts resolving YES only 3% of the time -- the published
        # favourite-longshot pattern, which the bucket report should surface.
        prices = [0.08] * 400
        outs = [1] * 12 + [0] * 388
        (b,) = calibration_by_price_bucket(prices, outs, n_bins=10)
        self.assertLess(b.gap, 0)
        self.assertAlmostEqual(b.observed_rate, 0.03, places=6)


if __name__ == "__main__":
    unittest.main()
