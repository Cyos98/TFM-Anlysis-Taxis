"""Crea de forma idempotente los activos Superset del TFM."""

from __future__ import annotations

import json
import os
from urllib.parse import quote_plus

from superset.app import create_app


app = create_app()
with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice


DATABASE_NAME = "TFM Mobility Analytics"

DATASETS = {
    "mobility_overview": ("gold", "mart_mobility_overview"),
    "service_comparison": ("gold", "mart_service_comparison"),
    "driver_opportunity": ("gold", "mart_driver_opportunity"),
    "congestion_proxy": ("gold", "mart_congestion_proxy"),
    "profitability_scenario": ("gold", "mart_profitability_scenario"),
    "model_metrics": ("ml", "model_metrics"),
    "predictions": ("ml", "predictions"),
}

CHARTS = (
    (
        "Resumen diario de movilidad",
        "mobility_overview",
        ["date_key", "service_type_name", "trip_count", "active_pickup_zones", "observed_trip_amount"],
    ),
    (
        "Comparación de servicios",
        "service_comparison",
        ["service_type_name", "trip_count", "active_days", "active_pickup_zones", "observed_trip_amount"],
    ),
    (
        "Demanda relativa por zona y hora",
        "driver_opportunity",
        ["date_key", "hour_key", "borough", "zone_name", "service_type_key", "trip_count", "relative_demand_score"],
    ),
    (
        "Proxy de congestión",
        "congestion_proxy",
        ["date_key", "hour_key", "borough", "zone_name", "service_type_key", "average_speed_mph", "minutes_per_mile_proxy"],
    ),
    (
        "Oportunidad por hora ocupada",
        "driver_opportunity",
        ["date_key", "hour_key", "zone_name", "service_type_key", "trip_count", "observed_amount_per_occupied_hour"],
    ),
    (
        "Escenario de contribución neta",
        "profitability_scenario",
        ["date_key", "zone_name", "service_type_key", "trip_count", "observed_trip_amount", "estimated_net_contribution_scenario"],
    ),
    (
        "Métricas de predicción",
        "model_metrics",
        ["model_name", "horizon_hours", "mae", "rmse", "wape", "r2", "is_selected"],
    ),
    (
        "Demanda real frente a predicha",
        "predictions",
        ["target_timestamp", "service_type", "taxi_zone_key", "horizon_hours", "model_name", "actual_demand", "predicted_demand"],
    ),
)

DASHBOARDS = (
    ("Resumen ejecutivo de movilidad", "resumen-ejecutivo-movilidad", CHARTS[0:2]),
    ("Análisis geográfico", "analisis-geografico", CHARTS[2:4]),
    ("Oportunidades para conductores", "oportunidades-conductores", CHARTS[4:6]),
    ("Predicción y evaluación", "prediccion-evaluacion", CHARTS[6:8]),
)


def _analytics_uri() -> str:
    user = quote_plus(os.getenv("POSTGRES_USER", "tfm"))
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    database = quote_plus(os.getenv("POSTGRES_DB", "tfm_mobility"))
    return f"postgresql+psycopg2://{user}:{password}@postgres:5432/{database}"


def _database() -> Database:
    database = db.session.query(Database).filter_by(database_name=DATABASE_NAME).one_or_none()
    if database is None:
        database = Database(database_name=DATABASE_NAME)
        db.session.add(database)
    database.set_sqlalchemy_uri(_analytics_uri())
    database.expose_in_sqllab = True
    db.session.flush()
    return database


def _datasets(database: Database) -> dict[str, SqlaTable]:
    result: dict[str, SqlaTable] = {}
    for key, (schema, table_name) in DATASETS.items():
        dataset = (
            db.session.query(SqlaTable)
            .filter_by(database_id=database.id, schema=schema, table_name=table_name)
            .one_or_none()
        )
        if dataset is None:
            dataset = SqlaTable(
                database=database,
                schema=schema,
                table_name=table_name,
            )
            db.session.add(dataset)
            db.session.flush()
        dataset.fetch_metadata()
        result[key] = dataset
    db.session.flush()
    return result


def _chart(dataset: SqlaTable, title: str, columns: list[str]) -> Slice:
    chart = db.session.query(Slice).filter_by(slice_name=title).one_or_none()
    if chart is None:
        chart = Slice(slice_name=title)
        db.session.add(chart)
    chart.datasource_id = dataset.id
    chart.datasource_type = "table"
    chart.viz_type = "table"
    chart.params = json.dumps(
        {
            "datasource": f"{dataset.id}__table",
            "viz_type": "table",
            "query_mode": "raw",
            "all_columns": columns,
            "adhoc_filters": [],
            "order_by_cols": [],
            "row_limit": 100,
            "server_pagination": True,
            "table_timestamp_format": "%Y-%m-%d %H:%M:%S",
        },
        sort_keys=True,
    )
    db.session.flush()
    return chart


def _position_json(charts: list[Slice]) -> str:
    positions: dict[str, object] = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
        "GRID_ID": {"id": "GRID_ID", "type": "GRID", "children": []},
    }
    grid = positions["GRID_ID"]
    assert isinstance(grid, dict)
    for index, chart in enumerate(charts):
        row_id = f"ROW-{index}"
        chart_id = f"CHART-{chart.id}"
        grid["children"].append(row_id)
        positions[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": [chart_id],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        positions[chart_id] = {
            "id": chart_id,
            "type": "CHART",
            "children": [],
            "meta": {"chartId": chart.id, "height": 50, "width": 12},
        }
    return json.dumps(positions, sort_keys=True)


def bootstrap() -> None:
    database = _database()
    datasets = _datasets(database)
    chart_by_title: dict[str, Slice] = {}
    for title, dataset_key, columns in CHARTS:
        chart_by_title[title] = _chart(datasets[dataset_key], title, list(columns))

    for title, slug, chart_specs in DASHBOARDS:
        dashboard = db.session.query(Dashboard).filter_by(slug=slug).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=title, slug=slug)
            db.session.add(dashboard)
        dashboard.dashboard_title = title
        dashboard.published = True
        charts = [chart_by_title[chart_title] for chart_title, _key, _columns in chart_specs]
        dashboard.slices = charts
        dashboard.position_json = _position_json(charts)
    db.session.commit()
    print(
        json.dumps(
            {
                "event": "superset_assets_ready",
                "database": DATABASE_NAME,
                "datasets": len(datasets),
                "charts": len(CHARTS),
                "dashboards": len(DASHBOARDS),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    with app.app_context():
        bootstrap()
