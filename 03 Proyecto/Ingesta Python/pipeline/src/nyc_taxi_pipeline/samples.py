"""Generación determinista de una muestra Parquet pequeña para el modo demo."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from nyc_taxi_pipeline.config import ModeConfig
from nyc_taxi_pipeline.models import SourceFile, StoredFile
from nyc_taxi_pipeline.storage import inspect_file


def demo_source_files(mode: ModeConfig) -> list[SourceFile]:
    year = mode.start_date.year
    month = mode.start_date.month
    return [
        SourceFile(
            "demo",
            service,
            year,
            month,
            f"{service}_tripdata_{year:04d}-{month:02d}.parquet",
            f"sample://synthetic/{service}/{year:04d}-{month:02d}",
        )
        for service in mode.services
    ]


def _table_for(service_type: str) -> pa.Table:
    pickup = [datetime(2024, 1, 2, 8, 0), datetime(2024, 1, 2, 9, 0)]
    dropoff = [datetime(2024, 1, 2, 8, 15), datetime(2024, 1, 2, 9, 22)]
    common = {
        "PULocationID": pa.array([161, 237], type=pa.int32()),
        "DOLocationID": pa.array([237, 236], type=pa.int32()),
    }
    if service_type == "yellow":
        return pa.table(
            {
                "VendorID": [1, 2],
                "tpep_pickup_datetime": pickup,
                "tpep_dropoff_datetime": dropoff,
                **common,
                "trip_distance": [1.2, 2.4],
                "total_amount": [12.5, 18.75],
            }
        )
    if service_type == "green":
        return pa.table(
            {
                "VendorID": [1, 2],
                "lpep_pickup_datetime": pickup,
                "lpep_dropoff_datetime": dropoff,
                **common,
                "trip_distance": [1.0, 2.0],
                "total_amount": [11.0, 16.0],
            }
        )
    if service_type == "fhv":
        return pa.table(
            {
                "dispatching_base_num": ["B00001", "B00002"],
                "pickup_datetime": pickup,
                "dropOff_datetime": dropoff,
                "PUlocationID": common["PULocationID"],
                "DOlocationID": common["DOLocationID"],
            }
        )
    return pa.table(
        {
            "hvfhs_license_num": ["HV0003", "HV0005"],
            "pickup_datetime": pickup,
            "dropoff_datetime": dropoff,
            **common,
            "trip_miles": [1.1, 2.2],
            "base_passenger_fare": [10.0, 15.0],
        }
    )


def materialize_demo_file(source_file: SourceFile, destination: Path) -> StoredFile:
    if destination.is_file():
        return inspect_file(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_name(f".{destination.name}.{uuid4().hex}.part")
    try:
        pq.write_table(_table_for(source_file.service_type), temp_path, compression="snappy")
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)
    return inspect_file(destination)
