from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import unittest

from nyc_taxi_pipeline.config import ConfigurationError, load_config, resolve_mode


CONFIG_PATH = Path(
    os.getenv(
        "TFM_CONFIG_PATH",
        str(Path(__file__).resolve().parents[2] / "configs" / "pipeline.toml"),
    )
)


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(CONFIG_PATH)

    def test_demo_has_all_supported_services(self) -> None:
        self.assertEqual(
            self.config.demo.services,
            ("yellow", "green", "fhv", "fhvhv"),
        )

    def test_demo_dates_come_from_toml(self) -> None:
        resolved = resolve_mode(self.config, "demo")
        self.assertEqual(resolved.start_date, date(2024, 1, 1))
        self.assertEqual(resolved.end_date, date(2024, 1, 31))

    def test_tlc_source_uses_official_https_page(self) -> None:
        self.assertTrue(self.config.tlc_source.index_url.startswith("https://www.nyc.gov/"))
        self.assertEqual(self.config.tlc_source.max_retries, 6)
        self.assertEqual(self.config.tlc_source.download_workers, 2)

    def test_full_requires_explicit_end_date(self) -> None:
        with self.assertRaises(ConfigurationError):
            resolve_mode(self.config, "full")

    def test_full_accepts_cli_interval(self) -> None:
        resolved = resolve_mode(
            self.config,
            "full",
            start_date="2018-01-01",
            end_date="2025-12-31",
        )
        self.assertEqual(resolved.end_date, date(2025, 12, 31))


if __name__ == "__main__":
    unittest.main()
