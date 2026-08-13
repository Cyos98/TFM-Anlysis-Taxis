"""Entrenamiento reproducible de demanda con partición temporal."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
from typing import Iterable
from uuid import UUID, uuid4

import joblib
import numpy as np
import psycopg
from psycopg.rows import dict_row
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from nyc_taxi_ml import __version__
from nyc_taxi_ml.config import AppConfig, SUPPORTED_SERVICES
from nyc_taxi_ml.database import apply_ml_migration


@dataclass(frozen=True)
class HourlyDemandPoint:
    timestamp: datetime
    service_type: str
    taxi_zone_key: int
    demand: float


@dataclass(frozen=True)
class ForecastDataset:
    features: np.ndarray
    target: np.ndarray
    baseline: np.ndarray
    timestamps: tuple[datetime, ...]
    services: tuple[str, ...]
    zones: tuple[int, ...]
    train_mask: np.ndarray
    test_mask: np.ndarray
    cutoff: datetime


def generate_demo_hourly_demand(days: int = 120) -> list[HourlyDemandPoint]:
    """Panel sintético determinista; valida el flujo, no resultados científicos."""

    rng = np.random.default_rng(42)
    start = datetime(2024, 1, 1)
    zones = (161, 236, 237)
    points: list[HourlyDemandPoint] = []
    for hour_index in range(days * 24):
        timestamp = start + timedelta(hours=hour_index)
        hour = timestamp.hour
        weekday = timestamp.weekday()
        morning_peak = math.exp(-((hour - 8) ** 2) / 8.0)
        evening_peak = math.exp(-((hour - 18) ** 2) / 10.0)
        weekly_factor = 0.82 if weekday >= 5 else 1.0
        trend = 1.0 + (hour_index / (days * 24)) * 0.08
        for service_index, service in enumerate(SUPPORTED_SERVICES):
            for zone_index, zone in enumerate(zones):
                level = 5.0 + service_index * 1.8 + zone_index * 1.2
                intensity = max(
                    0.1,
                    level
                    * weekly_factor
                    * trend
                    * (0.45 + 1.9 * morning_peak + 1.6 * evening_peak),
                )
                points.append(
                    HourlyDemandPoint(
                        timestamp,
                        service,
                        zone,
                        float(rng.poisson(intensity)),
                    )
                )
    return points


def _connection_args(config: AppConfig) -> dict[str, object]:
    return {
        "host": config.database.host,
        "port": config.database.port,
        "dbname": config.database.name,
        "user": config.database.user,
        "password": config.database.password,
        "connect_timeout": 5,
        "row_factory": dict_row,
    }


def load_gold_hourly_demand(config: AppConfig) -> list[HourlyDemandPoint]:
    with psycopg.connect(**_connection_args(config)) as connection:
        rows = connection.execute(
            """
            SELECT
                (d.full_date + t.hour_start)::timestamp AS target_timestamp,
                f.service_type_key,
                f.taxi_zone_key,
                f.trip_count
            FROM gold.fact_zone_hourly_demand AS f
            JOIN gold.dim_date AS d ON f.date_key = d.date_key
            JOIN gold.dim_time AS t ON f.hour_key = t.hour_key
            ORDER BY f.service_type_key, f.taxi_zone_key, target_timestamp
            """
        ).fetchall()
    return [
        HourlyDemandPoint(
            row["target_timestamp"],
            str(row["service_type_key"]),
            int(row["taxi_zone_key"]),
            float(row["trip_count"]),
        )
        for row in rows
    ]


def _dense_series(
    points: Iterable[HourlyDemandPoint],
) -> dict[tuple[str, int], list[HourlyDemandPoint]]:
    grouped: dict[tuple[str, int], list[HourlyDemandPoint]] = defaultdict(list)
    for point in points:
        grouped[(point.service_type, point.taxi_zone_key)].append(point)
    dense: dict[tuple[str, int], list[HourlyDemandPoint]] = {}
    for key, values in grouped.items():
        by_timestamp = {value.timestamp: value.demand for value in values}
        first = min(by_timestamp)
        last = max(by_timestamp)
        cursor = first
        series: list[HourlyDemandPoint] = []
        while cursor <= last:
            series.append(HourlyDemandPoint(cursor, key[0], key[1], by_timestamp.get(cursor, 0.0)))
            cursor += timedelta(hours=1)
        dense[key] = series
    return dense


def build_forecast_dataset(
    points: Iterable[HourlyDemandPoint], horizon_hours: int
) -> ForecastDataset:
    if horizon_hours not in {1, 24}:
        raise ValueError("El horizonte debe ser 1 o 24 horas")
    features: list[list[float]] = []
    targets: list[float] = []
    baselines: list[float] = []
    timestamps: list[datetime] = []
    services: list[str] = []
    zones: list[int] = []
    service_codes = {service: index for index, service in enumerate(SUPPORTED_SERVICES)}

    for (service, zone), series in sorted(_dense_series(points).items()):
        values = np.asarray([point.demand for point in series], dtype=float)
        for target_index in range(48, len(series)):
            origin_index = target_index - horizon_hours
            if origin_index < 24:
                continue
            target_time = series[target_index].timestamp
            target_hour = target_time.hour
            target_weekday = target_time.weekday()
            rolling = values[origin_index - 23 : origin_index + 1]
            features.append(
                [
                    values[origin_index],
                    values[origin_index - 1],
                    values[origin_index - 24],
                    float(np.mean(rolling)),
                    math.sin(2 * math.pi * target_hour / 24),
                    math.cos(2 * math.pi * target_hour / 24),
                    math.sin(2 * math.pi * target_weekday / 7),
                    math.cos(2 * math.pi * target_weekday / 7),
                    float(service_codes[service]),
                    float(zone),
                ]
            )
            targets.append(values[target_index])
            baselines.append(values[target_index - 24])
            timestamps.append(target_time)
            services.append(service)
            zones.append(zone)

    unique_times = sorted(set(timestamps))
    if len(unique_times) < 30 * 24:
        raise ValueError(
            "Se requieren al menos 30 días horarios para una partición temporal fiable"
        )
    cutoff = unique_times[int(len(unique_times) * 0.8)]
    train_mask = np.asarray([value < cutoff for value in timestamps], dtype=bool)
    test_mask = ~train_mask
    return ForecastDataset(
        np.asarray(features, dtype=float),
        np.asarray(targets, dtype=float),
        np.asarray(baselines, dtype=float),
        tuple(timestamps),
        tuple(services),
        tuple(zones),
        train_mask,
        test_mask,
        cutoff,
    )


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | None]:
    denominator = float(np.sum(np.abs(actual)))
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "wape": float(np.sum(np.abs(actual - predicted)) / denominator)
        if denominator
        else None,
        "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else None,
    }


def train_demand_models(config: AppConfig, mode: str = "demo") -> dict[str, object]:
    if mode not in {"demo", "full"}:
        raise ValueError("mode debe ser demo o full")
    apply_ml_migration(config)
    points = generate_demo_hourly_demand() if mode == "demo" else load_gold_hourly_demand(config)
    data_version = "synthetic_hourly_v1" if mode == "demo" else "gold_hourly_v1"
    model_run_id = uuid4()
    code_version = os.getenv("TFM_CODE_VERSION", __version__)
    artifacts_root = config.artifacts_root
    artifacts_root.mkdir(parents=True, exist_ok=True)
    parameters = {
        "horizons": [1, 24],
        "temporal_test_fraction": 0.20,
        "random_seed": 42,
        "synthetic_demo": mode == "demo",
        "point_count": len(points),
    }

    with psycopg.connect(**_connection_args(config), autocommit=True) as connection:
        connection.execute(
            """
            INSERT INTO ml.model_runs (
                model_run_id, mode, status, data_version, code_version, parameters
            ) VALUES (%s, %s, 'RUNNING', %s, %s, %s::jsonb)
            """,
            (model_run_id, mode, data_version, code_version, json.dumps(parameters)),
        )

    summaries: list[dict[str, object]] = []
    try:
        with psycopg.connect(**_connection_args(config), autocommit=True) as connection:
            for horizon in (1, 24):
                dataset = build_forecast_dataset(points, horizon)
                actual = dataset.target[dataset.test_mask]
                candidates: dict[str, tuple[object | None, np.ndarray]] = {
                    "seasonal_naive": (None, dataset.baseline[dataset.test_mask])
                }
                estimators = {
                    "extra_trees": ExtraTreesRegressor(
                        n_estimators=120,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=1,
                    ),
                    "hist_gradient_boosting": HistGradientBoostingRegressor(
                        max_iter=120,
                        learning_rate=0.08,
                        max_leaf_nodes=31,
                        l2_regularization=0.1,
                        random_state=42,
                    ),
                }
                for name, estimator in estimators.items():
                    estimator.fit(
                        dataset.features[dataset.train_mask],
                        dataset.target[dataset.train_mask],
                    )
                    predicted = np.maximum(
                        0.0, estimator.predict(dataset.features[dataset.test_mask])
                    )
                    candidates[name] = (estimator, predicted)

                horizon_results: list[tuple[str, dict[str, float | None], np.ndarray]] = []
                for name, (_estimator, predicted) in candidates.items():
                    metrics = _metrics(actual, predicted)
                    horizon_results.append((name, metrics, predicted))
                selected_name = min(
                    horizon_results, key=lambda result: float(result[1]["mae"] or math.inf)
                )[0]
                selected_estimator = candidates[selected_name][0]
                if selected_estimator is not None:
                    joblib.dump(
                        selected_estimator,
                        artifacts_root
                        / f"{model_run_id}_{selected_name}_{horizon}h.joblib",
                    )

                test_indices = np.flatnonzero(dataset.test_mask)
                for name, metrics, predicted in horizon_results:
                    connection.execute(
                        """
                        INSERT INTO ml.model_metrics (
                            model_run_id, model_name, horizon_hours, split,
                            mae, rmse, wape, r2, sample_count, is_selected
                        ) VALUES (%s, %s, %s, 'test', %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            model_run_id,
                            name,
                            horizon,
                            metrics["mae"],
                            metrics["rmse"],
                            metrics["wape"],
                            metrics["r2"],
                            len(actual),
                            name == selected_name,
                        ),
                    )
                    rows = [
                        (
                            model_run_id,
                            name,
                            horizon,
                            dataset.timestamps[index],
                            dataset.services[index],
                            dataset.zones[index],
                            float(dataset.target[index]),
                            float(predicted[position]),
                        )
                        for position, index in enumerate(test_indices)
                    ]
                    with connection.cursor() as cursor:
                        cursor.executemany(
                            """
                            INSERT INTO ml.predictions (
                                model_run_id, model_name, horizon_hours,
                                target_timestamp, service_type, taxi_zone_key,
                                actual_demand, predicted_demand, split
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'test')
                            """,
                            rows,
                        )
                selected_metrics = next(
                    metrics
                    for name, metrics, _predicted in horizon_results
                    if name == selected_name
                )
                summaries.append(
                    {
                        "horizon_hours": horizon,
                        "selected_model": selected_name,
                        "test_samples": len(actual),
                        "cutoff": dataset.cutoff.isoformat(),
                        **selected_metrics,
                    }
                )
            connection.execute(
                """
                UPDATE ml.model_runs
                SET status = 'SUCCEEDED', finished_at = CURRENT_TIMESTAMP
                WHERE model_run_id = %s
                """,
                (model_run_id,),
            )
    except Exception as exc:
        with psycopg.connect(**_connection_args(config), autocommit=True) as connection:
            connection.execute(
                """
                UPDATE ml.model_runs
                SET status = 'FAILED', finished_at = CURRENT_TIMESTAMP, error_message = %s
                WHERE model_run_id = %s
                """,
                (str(exc), model_run_id),
            )
        raise

    metadata_path = artifacts_root / f"{model_run_id}_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "model_run_id": str(model_run_id),
                "mode": mode,
                "data_version": data_version,
                "parameters": parameters,
                "results": summaries,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {
        "event": "ml_training_complete",
        "model_run_id": str(model_run_id),
        "mode": mode,
        "data_version": data_version,
        "synthetic_demo": mode == "demo",
        "results": summaries,
    }
