from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nyc_taxi_pipeline.config import ModeConfig
from nyc_taxi_pipeline.quality import validate_parquet
from nyc_taxi_pipeline.samples import demo_source_files, materialize_demo_file


class DemoSampleTests(unittest.TestCase):
    def test_four_demo_parquets_are_small_valid_and_deterministic(self) -> None:
        mode = ModeConfig(
            date(2024, 1, 1),
            date(2024, 1, 31),
            ("yellow", "green", "fhv", "fhvhv"),
            1,
        )
        with TemporaryDirectory() as temp_dir:
            for source_file in demo_source_files(mode):
                path = Path(temp_dir) / source_file.filename
                first = materialize_demo_file(source_file, path)
                second = materialize_demo_file(source_file, path)
                report = validate_parquet(path, source_file.service_type)
                self.assertTrue(report.is_valid)
                self.assertEqual(report.row_count, 2)
                self.assertEqual(first.sha256, second.sha256)
                self.assertLess(first.size_bytes, 20_000)


if __name__ == "__main__":
    unittest.main()
