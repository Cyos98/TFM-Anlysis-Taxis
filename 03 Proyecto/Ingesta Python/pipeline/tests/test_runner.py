from __future__ import annotations

import os
from pathlib import Path
import unittest

from nyc_taxi_pipeline.config import load_config
from nyc_taxi_pipeline.runner import build_execution_plan


CONFIG_PATH = Path(
    os.getenv(
        "TFM_CONFIG_PATH",
        str(Path(__file__).resolve().parents[2] / "configs" / "pipeline.toml"),
    )
)


class RunnerTests(unittest.TestCase):
    def test_demo_plan_does_not_expose_password(self) -> None:
        config = load_config(CONFIG_PATH)
        plan = build_execution_plan(config, "demo")
        self.assertEqual(plan["implemented_phase"], 1)
        self.assertNotIn("password", plan["database"])
        self.assertEqual(plan["mode"], "demo")


if __name__ == "__main__":
    unittest.main()
