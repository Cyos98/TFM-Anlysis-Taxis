"""Tests estáticos de los contratos versionados del flujo NiFi."""

from __future__ import annotations

import json
import os
from pathlib import Path
import unittest


SPEC_PATH = Path(os.getenv("NIFI_FLOW_SPEC", "/parameters/flow_spec.json"))


class FlowSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SPEC_PATH.read_text(encoding="utf-8")
        cls.spec = json.loads(cls.raw)
        cls.groups = {
            group["name"]: group for group in cls.spec["process_groups"]
        }

    def test_required_parameter_contexts_are_versioned(self) -> None:
        names = {context["name"] for context in self.spec["parameter_contexts"]}
        self.assertEqual(
            {"TLC", "POSTGRES", "PATHS", "PIPELINE", "EXTERNAL_SOURCES"},
            names,
        )

    def test_no_password_value_is_versioned(self) -> None:
        parameters = [
            parameter
            for context in self.spec["parameter_contexts"]
            for parameter in context["parameters"]
        ]
        password = next(
            parameter
            for parameter in parameters
            if parameter["name"] == "POSTGRES_PASSWORD"
        )
        self.assertTrue(password["sensitive"])
        self.assertEqual("POSTGRES_PASSWORD", password["environment"])
        self.assertNotIn("value", password)

    def test_http_retries_are_finite(self) -> None:
        processors = self.groups["20_TLC_DOWNLOAD"]["processors"]
        retry = next(item for item in processors if item["name"] == "Limit HTTP retries")
        self.assertEqual("#{MAX_RETRIES}", retry["properties"]["Maximum Retries"])
        self.assertIn("retries_exceeded", retry["auto_terminate"])

    def test_error_group_has_quarantine_and_terminal_log(self) -> None:
        types = {
            processor["type"].rsplit(".", 1)[-1]
            for processor in self.groups["90_ERROR_HANDLING"]["processors"]
        }
        self.assertTrue({"PutFile", "LogMessage"}.issubset(types))

    def test_demo_is_parquet_and_idempotent(self) -> None:
        processors = self.groups["05_DEMO_PIPELINE"]["processors"]
        by_name = {processor["name"]: processor for processor in processors}
        writer = by_name["Write idempotent demo Bronze"]
        self.assertEqual("ignore", writer["properties"]["Conflict Resolution Strategy"])
        converter = by_name["Convert demo JSON to Parquet"]
        self.assertEqual("@service:Demo Parquet Writer", converter["properties"]["Record Writer"])
        sql = by_name["Prepare demo manifest and landing SQL"]["properties"]["Replacement Value"]
        self.assertIn("ON CONFLICT", sql)
        self.assertIn("control.ingestion_files", sql)


if __name__ == "__main__":
    unittest.main()

