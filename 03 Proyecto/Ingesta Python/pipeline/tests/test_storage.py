from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from nyc_taxi_pipeline.config import TlcSourceConfig
from nyc_taxi_pipeline.models import SourceFile
from nyc_taxi_pipeline.storage import bronze_path, download_atomic, quarantine_file


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: object) -> None:
        return


class StorageTests(unittest.TestCase):
    def test_demo_and_tlc_use_separate_namespaces(self) -> None:
        demo = SourceFile(
            "demo", "yellow", 2024, 1, "yellow_tripdata_2024-01.parquet", "sample://x"
        )
        tlc = SourceFile(
            "tlc", "yellow", 2024, 1, "yellow_tripdata_2024-01.parquet", "https://x"
        )
        self.assertEqual(
            bronze_path(Path("/data"), demo),
            Path("/data/bronze/demo/yellow/year=2024/month=01/yellow_tripdata_2024-01.parquet"),
        )
        self.assertEqual(
            bronze_path(Path("/data"), tlc),
            Path("/data/bronze/tlc/yellow/year=2024/month=01/yellow_tripdata_2024-01.parquet"),
        )

    def test_download_is_atomic_and_hashes_content(self) -> None:
        with TemporaryDirectory() as source_dir, TemporaryDirectory() as target_dir:
            payload = b"PAR1" + (b"safe-demo-payload" * 128) + b"PAR1"
            source_path = Path(source_dir) / "yellow_tripdata_2024-01.parquet"
            source_path.write_bytes(payload)
            handler = partial(_QuietHandler, directory=source_dir)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                source_file = SourceFile(
                    "tlc",
                    "yellow",
                    2024,
                    1,
                    source_path.name,
                    f"http://127.0.0.1:{server.server_port}/{source_path.name}",
                )
                destination = Path(target_dir) / source_path.name
                config = TlcSourceConfig("http://unused", 5, 2, 128, 2, 2, 1.2, 1, 0)
                stored = download_atomic(source_file, destination, config)
                self.assertEqual(destination.read_bytes(), payload)
                self.assertEqual(stored.size_bytes, len(payload))
                self.assertEqual(list(destination.parent.glob("*.part")), [])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_quarantine_preserves_invalid_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir)
            source = data_root / "bronze" / "demo" / "broken.parquet"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"broken")
            quarantined = quarantine_file(data_root, source)
            self.assertFalse(source.exists())
            self.assertEqual(quarantined.read_bytes(), b"broken")
            self.assertTrue(quarantined.is_relative_to(data_root / "quarantine" / "bronze"))


if __name__ == "__main__":
    unittest.main()
