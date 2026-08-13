from __future__ import annotations

import unittest

from nyc_taxi_ml.modeling import build_forecast_dataset, generate_demo_hourly_demand


class MachineLearningFeatureTests(unittest.TestCase):
    def test_demo_generation_is_deterministic(self) -> None:
        first = generate_demo_hourly_demand(days=31)
        second = generate_demo_hourly_demand(days=31)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 31 * 24 * 4 * 3)

    def test_temporal_split_has_no_overlap(self) -> None:
        dataset = build_forecast_dataset(generate_demo_hourly_demand(days=40), 24)
        train_times = [
            value
            for value, selected in zip(dataset.timestamps, dataset.train_mask)
            if selected
        ]
        test_times = [
            value
            for value, selected in zip(dataset.timestamps, dataset.test_mask)
            if selected
        ]
        self.assertLess(max(train_times), min(test_times))
        self.assertEqual(dataset.features.shape[1], 10)

    def test_rejects_unknown_horizon(self) -> None:
        with self.assertRaises(ValueError):
            build_forecast_dataset(generate_demo_hourly_demand(days=40), 2)


if __name__ == "__main__":
    unittest.main()
