"""Escritura segura e inmutable de ficheros Bronze."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from threading import Lock
import time
from urllib.request import Request, urlopen
from uuid import uuid4

from nyc_taxi_pipeline.config import TlcSourceConfig
from nyc_taxi_pipeline.models import SourceFile, StoredFile


_DOWNLOAD_START_LOCK = Lock()
_LAST_DOWNLOAD_START = 0.0


def _wait_for_download_slot(minimum_interval_seconds: int) -> None:
    global _LAST_DOWNLOAD_START
    with _DOWNLOAD_START_LOCK:
        elapsed = time.monotonic() - _LAST_DOWNLOAD_START
        remaining = minimum_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        _LAST_DOWNLOAD_START = time.monotonic()


def sha256_file(path: Path, chunk_size: int = 1_048_576) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(path: Path) -> StoredFile:
    return StoredFile(path, path.stat().st_size, sha256_file(path))


def bronze_path(data_root: Path, source_file: SourceFile) -> Path:
    return data_root / source_file.bronze_relative_path()


def quarantine_file(data_root: Path, path: Path) -> Path:
    """Conserva un fichero inconsistente fuera de Bronze sin eliminar evidencia."""

    quarantine_root = data_root / "quarantine" / "bronze"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    quarantined = quarantine_root / f"{path.name}.{uuid4().hex}.invalid"
    os.replace(path, quarantined)
    return quarantined


def download_atomic(
    source_file: SourceFile,
    destination: Path,
    source_config: TlcSourceConfig,
) -> StoredFile:
    """Descarga a un temporal, valida tamaño y promueve con rename atómico."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_name(f".{destination.name}.{uuid4().hex}.part")
    request = Request(
        source_file.source_url,
        headers={"User-Agent": "tfm-nyc-mobility-platform/0.2 (+academic-project)"},
    )
    last_error: Exception | None = None

    for attempt in range(1, source_config.max_retries + 1):
        try:
            _wait_for_download_slot(source_config.download_start_interval_seconds)
            digest = hashlib.sha256()
            size_bytes = 0
            with urlopen(request, timeout=source_config.timeout_seconds) as response:
                raw_length = response.headers.get("Content-Length")
                expected_length = int(raw_length) if raw_length else None
                with temp_path.open("xb") as output:
                    while True:
                        chunk = response.read(source_config.chunk_size_bytes)
                        if not chunk:
                            break
                        output.write(chunk)
                        digest.update(chunk)
                        size_bytes += len(chunk)
                    output.flush()
                    os.fsync(output.fileno())
            if expected_length is not None and size_bytes != expected_length:
                raise IOError(
                    f"Tamaño incompleto: esperado={expected_length}, recibido={size_bytes}"
                )
            os.replace(temp_path, destination)
            return StoredFile(destination, size_bytes, digest.hexdigest())
        except Exception as exc:
            last_error = exc
            temp_path.unlink(missing_ok=True)
            if attempt < source_config.max_retries:
                time.sleep(
                    min(
                        source_config.retry_backoff_seconds * (2 ** (attempt - 1)),
                        300,
                    )
                )
    assert last_error is not None
    raise RuntimeError(
        f"Falló la descarga de {source_file.filename} tras "
        f"{source_config.max_retries} intentos: "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error
