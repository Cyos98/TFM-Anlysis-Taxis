"""Descubrimiento de Parquet publicados por NYC TLC."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from nyc_taxi_pipeline.config import ModeConfig, TlcSourceConfig
from nyc_taxi_pipeline.models import SourceFile


_FILENAME_PATTERN = re.compile(
    r"^(yellow|green|fhv|fhvhv)_tripdata_(\d{4})-(\d{2})\.parquet$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class RemoteFileProbe:
    source_file: SourceFile
    size_bytes: int | None
    etag: str | None
    last_modified: str | None
    error: str | None = None


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href.strip())


def _period_key(value: date) -> int:
    return value.year * 100 + value.month


def parse_tlc_links(
    html: str,
    index_url: str,
    mode: ModeConfig,
) -> list[SourceFile]:
    """Convierte el HTML oficial en un inventario filtrado y determinista."""

    if mode.end_date is None:
        raise ValueError("El discovery TLC requiere una fecha final")
    parser = _LinkParser()
    parser.feed(html)
    start_period = _period_key(mode.start_date)
    end_period = _period_key(mode.end_date)
    allowed_services = set(mode.services)
    unique: dict[tuple[str, int, int, str], SourceFile] = {}

    for href in parser.links:
        absolute_url = urljoin(index_url, href)
        filename = urlparse(absolute_url).path.rsplit("/", 1)[-1]
        match = _FILENAME_PATTERN.fullmatch(filename)
        if not match:
            continue
        service, raw_year, raw_month = match.groups()
        service = service.lower()
        year = int(raw_year)
        month = int(raw_month)
        period = year * 100 + month
        if service not in allowed_services or not start_period <= period <= end_period:
            continue
        if not 1 <= month <= 12:
            continue
        item = SourceFile("tlc", service, year, month, filename, absolute_url)
        unique[(service, year, month, filename)] = item

    grouped: dict[str, list[SourceFile]] = defaultdict(list)
    for item in unique.values():
        grouped[item.service_type].append(item)

    selected: list[SourceFile] = []
    for service in mode.services:
        service_files = sorted(
            grouped.get(service, []),
            key=lambda item: (item.year, item.month, item.filename),
        )
        if mode.max_files_per_service:
            service_files = service_files[: mode.max_files_per_service]
        selected.extend(service_files)
    return selected


def fetch_tlc_index(source: TlcSourceConfig) -> str:
    """Descarga solo el HTML de índice con timeout y reintentos controlados."""

    request = Request(
        source.index_url,
        headers={"User-Agent": "tfm-nyc-mobility-platform/0.2 (+academic-project)"},
    )
    last_error: Exception | None = None
    for attempt in range(1, source.max_retries + 1):
        try:
            with urlopen(request, timeout=source.timeout_seconds) as response:
                payload = response.read()
                return payload.decode(response.headers.get_content_charset() or "utf-8")
        except Exception as exc:  # urllib agrupa errores HTTP, TLS y socket.
            last_error = exc
            if attempt < source.max_retries:
                time.sleep(min(2 ** (attempt - 1), 4))
    assert last_error is not None
    raise RuntimeError(
        f"No se pudo consultar el índice TLC tras {source.max_retries} intentos"
    ) from last_error


def discover_tlc_files(source: TlcSourceConfig, mode: ModeConfig) -> list[SourceFile]:
    return parse_tlc_links(fetch_tlc_index(source), source.index_url, mode)


def probe_remote_file(
    source_file: SourceFile,
    source: TlcSourceConfig,
) -> RemoteFileProbe:
    request = Request(
        source_file.source_url,
        method="HEAD",
        headers={"User-Agent": "tfm-nyc-mobility-platform/0.2 (+academic-project)"},
    )
    last_error: Exception | None = None
    for attempt in range(1, source.max_retries + 1):
        try:
            with urlopen(request, timeout=source.timeout_seconds) as response:
                raw_size = response.headers.get("Content-Length")
                return RemoteFileProbe(
                    source_file,
                    int(raw_size) if raw_size else None,
                    response.headers.get("ETag"),
                    response.headers.get("Last-Modified"),
                )
        except Exception as exc:
            last_error = exc
            if attempt < source.max_retries:
                time.sleep(min(2 ** (attempt - 1), 4))
    assert last_error is not None
    return RemoteFileProbe(source_file, None, None, None, str(last_error))


def probe_remote_files(
    files: list[SourceFile],
    source: TlcSourceConfig,
) -> list[RemoteFileProbe]:
    probes: list[RemoteFileProbe] = []
    with ThreadPoolExecutor(max_workers=source.probe_workers) as executor:
        futures = {
            executor.submit(probe_remote_file, source_file, source): source_file
            for source_file in files
        }
        for future in as_completed(futures):
            probes.append(future.result())
    return sorted(
        probes,
        key=lambda probe: (
            probe.source_file.year,
            probe.source_file.month,
            probe.source_file.service_type,
        ),
    )
