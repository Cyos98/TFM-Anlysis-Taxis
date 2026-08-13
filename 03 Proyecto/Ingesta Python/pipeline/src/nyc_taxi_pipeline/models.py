"""Modelos de dominio compartidos por la ingesta Bronze."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceFile:
    source_kind: str
    service_type: str
    year: int
    month: int
    filename: str
    source_url: str

    def bronze_relative_path(self) -> Path:
        namespace = Path("bronze") / ("demo" if self.source_kind == "demo" else "tlc")
        return (
            namespace
            / self.service_type
            / f"year={self.year:04d}"
            / f"month={self.month:02d}"
            / self.filename
        )


@dataclass(frozen=True, slots=True)
class StoredFile:
    path: Path
    size_bytes: int
    sha256: str
