from __future__ import annotations

from datetime import date
import unittest

from nyc_taxi_pipeline.config import ModeConfig
from nyc_taxi_pipeline.discovery import parse_tlc_links


HTML = """
<html><body>
  <a href="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet">yellow</a>
  <a href="https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2024-01.parquet">green</a>
  <a href="https://d37ci6vzurychx.cloudfront.net/trip-data/fhv_tripdata_2024-01.parquet">fhv</a>
  <a href="https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2024-01.parquet">fhvhv</a>
  <a href="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-12.parquet">outside</a>
  <a href="/not-a-parquet.csv">ignore</a>
</body></html>
"""


class DiscoveryTests(unittest.TestCase):
    def test_filters_period_and_recognizes_four_services(self) -> None:
        mode = ModeConfig(
            date(2024, 1, 1),
            date(2024, 1, 31),
            ("yellow", "green", "fhv", "fhvhv"),
            1,
        )
        files = parse_tlc_links(HTML, "https://www.nyc.gov/index.html", mode)
        self.assertEqual(len(files), 4)
        self.assertEqual(
            {item.service_type for item in files},
            {"yellow", "green", "fhv", "fhvhv"},
        )
        self.assertTrue(all(item.year == 2024 and item.month == 1 for item in files))


if __name__ == "__main__":
    unittest.main()
