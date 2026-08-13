from __future__ import annotations

from datetime import datetime
import unittest

from nyc_taxi_pipeline.landing import normalize_bronze_row


class LandingNormalizationTests(unittest.TestCase):
    def test_normalizes_yellow_aliases(self) -> None:
        pickup = datetime(2024, 1, 2, 8, 0)
        row = normalize_bronze_row(
            {
                "tpep_pickup_datetime": pickup,
                "tpep_dropoff_datetime": datetime(2024, 1, 2, 8, 15),
                "PULocationID": 161,
                "DOLocationID": 237,
                "trip_distance": 1.2,
                "total_amount": 12.5,
            }
        )
        self.assertEqual(row["pickup_datetime"], pickup)
        self.assertEqual(row["pickup_location_id"], 161)
        self.assertEqual(row["total_amount"], 12.5)

    def test_normalizes_fhv_location_case(self) -> None:
        row = normalize_bronze_row(
            {"PUlocationID": 10, "DOlocationID": 20, "dispatching_base_num": "B1"}
        )
        self.assertEqual(row["pickup_location_id"], 10)
        self.assertEqual(row["dropoff_location_id"], 20)
        self.assertEqual(row["dispatching_base_num"], "B1")


if __name__ == "__main__":
    unittest.main()
