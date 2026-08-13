"""Validaciones mínimas y auditables de Bronze Parquet."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq


@dataclass(frozen=True, slots=True)
class QualityCheck:
    name: str
    status: str
    observed: str
    expected: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class ValidationReport:
    row_count: int
    columns: tuple[str, ...]
    checks: tuple[QualityCheck, ...]

    @property
    def is_valid(self) -> bool:
        return all(check.status != "FAIL" for check in self.checks)


_REQUIRED_COLUMN_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "yellow": (
        ("tpep_pickup_datetime",),
        ("tpep_dropoff_datetime",),
        ("PULocationID",),
        ("DOLocationID",),
    ),
    "green": (
        ("lpep_pickup_datetime",),
        ("lpep_dropoff_datetime",),
        ("PULocationID",),
        ("DOLocationID",),
    ),
    "fhv": (
        ("pickup_datetime",),
        ("dropOff_datetime", "dropoff_datetime"),
        ("PUlocationID", "PULocationID"),
        ("DOlocationID", "DOLocationID"),
    ),
    "fhvhv": (
        ("pickup_datetime",),
        ("dropoff_datetime",),
        ("PULocationID",),
        ("DOLocationID",),
    ),
}


def validate_parquet(path: Path, service_type: str) -> ValidationReport:
    parquet = pq.ParquetFile(path)
    metadata = parquet.metadata
    columns = tuple(parquet.schema_arrow.names)
    checks: list[QualityCheck] = [
        QualityCheck("parquet_readable", "PASS", "true", "true", {})
    ]

    row_count = metadata.num_rows
    checks.append(
        QualityCheck(
            "row_count_positive",
            "PASS" if row_count > 0 else "FAIL",
            str(row_count),
            "> 0",
            {},
        )
    )
    checks.append(
        QualityCheck(
            "parquet_has_columns",
            "PASS" if columns else "FAIL",
            str(len(columns)),
            "> 0",
            {},
        )
    )

    missing_groups = [
        alternatives
        for alternatives in _REQUIRED_COLUMN_GROUPS[service_type]
        if not any(column in columns for column in alternatives)
    ]
    checks.append(
        QualityCheck(
            "service_required_columns",
            "PASS" if not missing_groups else "FAIL",
            ",".join(columns),
            " | ".join("/".join(group) for group in _REQUIRED_COLUMN_GROUPS[service_type]),
            {"missing_groups": [list(group) for group in missing_groups]},
        )
    )
    return ValidationReport(row_count, columns, tuple(checks))
