"""Tests for the analytical core. Pure stdlib: `python -m unittest discover tests`."""

import math
import random
import unittest

from kalshi_lab import calibration as cal
from kalshi_lab import edge
from kalshi_lab.fees import (
    FeeSchedule,
    fee,
    fee_as_fraction_of_notional,
    fee_per_contract,
    round_trip_cost,
)


class TestFees(unittest.TestCase):
    def test_peak_at_fifty_cents_matches_published_figure(self):
        # The one externally checkable anchor: 100 contracts at 50c = $1.75.
        self.assertAlmostEqual(fee(100, 0.50), 1.75, places=2)

    def test_fee_is_symmetric_about_fifty_cents(self):
        for p in (0.1, 0.25, 0.4):
            self.assertAlmostEqual(fee_per_contract(p), fee_per_contract(1.0 - p), places=12)

    def test_fee_peaks_at_fifty_cents(self):
        peak = fee_per_contract(0.50)
        for p in (0.01, 0.2, 0.35, 0.65, 0.8, 0.99):
            self.assertLess(fee_per_contract(p), peak)

    def test_fraction_of_notional_punishes_longshots(self):
        # Reduces to coefficient x (1 - price); cheap contracts are hit hardest.
        self.assertAlmostEqual(fee_as_fraction_of_notional(0.05), 0.07 * 0.95, places=12)
        self.assertAlmostEqual(fee_as_fraction_of_notional(0.95), 0.07 * 0.05, places=12)
        self.assertGreater(
            fee_as_fraction_of_notional(0.05) / fee_as_fraction_of_notional(0.95), 18.0
        )

    def test_maker_is_free_unless_series_is_flagged(self):
        self.assertEqual(fee(100, 0.5, maker=True), 0.0)
        flagged = FeeSchedule(maker_fees_enabled=True, rounding="none")
        self.assertAlmostEqual(
            fee(100, 0.5, maker=True, schedule=flagged), 0.0175 * 100 * 0.25, places=12
        )

    def test_maker_is_a_quarter_of_taker_when_charged(self):
        flagged = FeeSchedule(maker_fees_enabled=True, rounding="none")
        self.assertAlmostEqual(
            fee(100, 0.4, maker=True, schedule=flagged) * 4.0,
            fee(100, 0.4, maker=False, schedule=flagged),
            places=12,
        )

    def test_zero_multiplier_series_is_free(self):
        self.assertEqual(fee(1000, 0.5, schedule=FeeSchedule(multiplier=0.0)), 0.0)

    def test_rounding_modes_order_correctly(self):
        none_ = fee(3, 0.5, schedule=FeeSchedule(rounding="none"))
        order = fee(3, 0.5, schedule=FeeSchedule(rounding="order"))
        contract = fee(3, 0.5, schedule=FeeSchedule(rounding="contract"))
        self.assertLessEqual(none_, order)
        self.assertLessEqual(order, contract)  # per-contract rounding costs most

    def test_settlement_is_not_a_second_fee(self):
        self.assertAlmostEqual(round_trip_cost(0.6), fee_per_contract(0.6), places=12)
        self.assertGreater(round_trip_cost(0.6, exit_price=0.7), round_trip_cost(0.6))

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            fee(1, 1.5)
        with self.assertRaises(ValueError):
            FeeSchedule(rounding="sometimes")
        self.assertEqual(fee(0, 0.5), 0.0)


class TestEdge(unittest.TestCase):
    def test_expected_value_is_prob_minus_all_in_cost(self):
        ev = edge.expected_value(0.60, 0.50)
        self.assertAlmostEqual(ev, 0.60 - 0.50 - fee_per_contract(0.50), places=12)

    def test_break_even_exceeds_price_by_the_fee(self):
        self.assertGreater(edge.break_even_prob(0.50), 0.50)
        self.assertAlmostEqual(
            edge.break_even_prob(0.50) - 0.50, fee_per_contract(0.50), places=12
        )

    def test_fair_priced_contract_is_negative_ev_after_fees(self):
        # Buying at exactly your own probability loses the fee. The core reason
        # a "well calibrated" forecast is not yet an edge.
        self.assertLess(edge.expected_value(0.50, 0.50), 0.0)

    def test_kelly_zero_without_edge(self):
        self.assertEqual(edge.kelly_fraction(0.50, 0.50), 0.0)
        self.assertEqual(edge.kelly_fraction(0.30, 0.60), 0.0)

    def test_kelly_matches_closed_form(self):
        p, price = 0.70, 0.50
        c = edge.cost_per_contract(price)
        expected = (p - c) / (1.0 - c) * edge.DEFAULT_KELLY_FRACTION
        self.assertAlmostEqual(edge.kelly_fraction(p, price), expected, places=12)

    def test_kelly_never_exceeds_the_fraction_cap(self):
        self.assertLessEqual(edge.kelly_fraction(1.0, 0.01), edge.DEFAULT_KELLY_FRACTION)

    def test_size_trade_declines_thin_edges(self):
        self.assertIsNone(edge.size_trade(0.51, 0.50, 1000.0))          # under min_edge
        self.assertIsNotNone(edge.size_trade(0.70, 0.50, 1000.0))

    def test_size_trade_stake_and_ev_are_consistent(self):
        t = edge.size_trade(0.70, 0.50, 1000.0)
        self.assertAlmostEqual(t.stake, t.contracts * t.cost_per_contract, places=10)
        self.assertAlmostEqual(t.expected_value, t.contracts * t.edge, places=10)
        self.assertLessEqual(t.stake, 1000.0)

    def test_size_trade_respects_contract_cap(self):
        t = edge.size_trade(0.90, 0.50, 1_000_000.0, max_contracts=10)
        self.assertEqual(t.contracts, 10)

    def test_size_trade_rejects_bad_side(self):
        with self.assertRaises(ValueError):
            edge.size_trade(0.7, 0.5, 100.0, side="maybe")


class TestCalibration(unittest.TestCase):
    def test_brier_of_always_half_is_quarter(self):
        self.assertAlmostEqual(cal.brier_score([0.5] * 100, [1, 0] * 50), 0.25, places=12)

    def test_brier_of_a_perfect_forecaster_is_zero(self):
        self.assertEqual(cal.brier_score([1.0, 0.0, 1.0], [1, 0, 1]), 0.0)

    def test_log_loss_is_finite_at_the_extremes(self):
        self.assertTrue(math.isfinite(cal.log_loss([0.0, 1.0], [1, 0])))

    def test_perfectly_calibrated_sample_has_unit_slope(self):
        # Construct outcomes matching their probabilities exactly, in blocks.
        preds, outs = [], []
        for p in (0.1, 0.3, 0.5, 0.7, 0.9):
            n = 100
            k = round(p * n)
            preds += [p] * n
            outs += [1] * k + [0] * (n - k)
        slope, intercept = cal.calibration_slope(preds, outs)
        self.assertAlmostEqual(slope, 1.0, places=6)
        self.assertAlmostEqual(intercept, 0.0, places=6)
        self.assertTrue(cal.calibration_report(preds, outs).is_well_calibrated)

    def test_constant_forecast_reports_no_information(self):
        slope, intercept = cal.calibration_slope([0.4] * 10, [1, 0] * 5)
        self.assertEqual(slope, 0.0)
        self.assertAlmostEqual(intercept, 0.5, places=12)

    def test_reliability_bins_detect_overpriced_longshots(self):
        # 10c contracts that only come in 2% of the time: the longshot bias.
        preds = [0.10] * 500
        outs = [1] * 10 + [0] * 490
        (b,) = cal.reliability_bins(preds, outs, n_bins=10)
        self.assertEqual(b.count, 500)
        self.assertLess(b.gap, 0)  # observed below predicted => overpriced

    def test_bins_place_one_point_oh_in_the_last_bin(self):
        bins = cal.reliability_bins([1.0], [1], n_bins=10)
        self.assertEqual(len(bins), 1)
        self.assertEqual(bins[0].high, 1.0)

    def test_skill_vs_market_is_zero_when_model_equals_price(self):
        prices = [0.2, 0.5, 0.8, 0.35]
        outs = [0, 1, 1, 0]
        r = cal.skill_vs_market(prices, prices, outs)
        self.assertAlmostEqual(r["brier_skill_score"], 0.0, places=12)
        self.assertAlmostEqual(r["improvement"], 0.0, places=12)

    def test_skill_vs_market_is_negative_when_model_is_worse(self):
        outs = [1, 1, 0, 0]
        prices = [0.9, 0.8, 0.2, 0.1]
        worse = [0.5, 0.5, 0.5, 0.5]
        self.assertLess(cal.skill_vs_market(worse, prices, outs)["brier_skill_score"], 0.0)

    def test_clustered_bootstrap_is_much_wider_than_naive(self):
        """40 events x 25 strikes that share each event's outcome.

        Treating 1000 correlated contracts as 1000 independent observations is
        the single easiest way to convince yourself of an edge that is not
        there. Measured here at 4.6-5.4x too narrow across seeds; the assertion
        is set well below that so it tests the effect, not the RNG.
        """
        rng = random.Random(7)
        preds, outs, clusters = [], [], []
        for event in range(40):
            p_event = rng.uniform(0.1, 0.9)       # a confident event-level view
            outcome = 1 if rng.random() < p_event else 0
            for _ in range(25):
                preds.append(min(max(p_event + rng.uniform(-0.05, 0.05), 0.0), 1.0))
                outs.append(outcome)              # strikes share the event's fate
                clusters.append(event)
        naive = cal.bootstrap_ci(preds, outs, None, n_resamples=400, seed=1)
        clustered = cal.bootstrap_ci(preds, outs, clusters, n_resamples=400, seed=1)
        self.assertGreater(clustered[1] - clustered[0], (naive[1] - naive[0]) * 2.5)

    def test_bootstrap_ci_brackets_the_point_estimate(self):
        rng = random.Random(3)
        preds = [rng.uniform(0, 1) for _ in range(200)]
        outs = [1 if rng.random() < p else 0 for p in preds]
        lo, hi = cal.bootstrap_ci(preds, outs, n_resamples=300, seed=2)
        self.assertLessEqual(lo, cal.brier_score(preds, outs))
        self.assertGreaterEqual(hi, cal.brier_score(preds, outs))

    def test_validation_rejects_mismatched_and_out_of_range_input(self):
        with self.assertRaises(ValueError):
            cal.brier_score([0.5, 0.5], [1])
        with self.assertRaises(ValueError):
            cal.brier_score([1.5], [1])
        with self.assertRaises(ValueError):
            cal.brier_score([0.5], [2])
        with self.assertRaises(ValueError):
            cal.brier_score([], [])


class TestFeesEdgeIntegration(unittest.TestCase):
    def test_longshot_needs_far_larger_relative_mispricing_to_clear_fees(self):
        """The lab's central structural claim, as an executable assertion.

        Break-even needs price x r > fee, i.e. a RELATIVE mispricing of
        r > coefficient x (1 - price). That is 6.65% for a 5c longshot against
        0.35% for a 95c favourite -- a 19x higher bar. So at an identical 3%
        relative mispricing the favourite is profitable and the longshot is
        not, which is why the thesis reads 'buy the favourite side', not
        'hunt for cheap longshots'.

        Note this is about the fee HURDLE only. That longshots are also
        systematically overpriced is a separate empirical finding (see
        docs/edge-thesis.md); the two point the same way, which is the point.
        """
        r = 0.03
        longshot_ev = edge.expected_value(0.05 * (1 + r), 0.05)
        favourite_ev = edge.expected_value(0.95 * (1 + r), 0.95)
        self.assertLess(longshot_ev, 0.0)
        self.assertGreater(favourite_ev, 0.0)

        # And the break-even hurdle itself is ~19x worse out in the longshot tail.
        self.assertAlmostEqual(
            fee_as_fraction_of_notional(0.05) / fee_as_fraction_of_notional(0.95),
            0.95 / 0.05,
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
