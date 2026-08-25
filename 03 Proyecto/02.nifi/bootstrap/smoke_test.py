"""Smoke test reproducible del bootstrap NiFi."""

from __future__ import annotations

import json
import sys

import bootstrap


EXPECTED_CONTEXTS = {"TLC", "POSTGRES", "PATHS", "PIPELINE", "EXTERNAL_SOURCES"}
EXPECTED_GROUPS = {
    "00_PIPELINE_CONTROL",
    "05_DEMO_PIPELINE",
    "10_TLC_DISCOVERY",
    "20_TLC_DOWNLOAD",
    "30_BRONZE_VALIDATION",
    "40_EXTERNAL_DATA",
    "50_DBT_TRIGGER",
    "60_ML_TRIGGER",
    "90_ERROR_HANDLING",
}


def main() -> int:
    token = bootstrap.authenticate()
    contexts = bootstrap.existing_contexts(token)
    root_id = bootstrap.root_group_id(token)
    groups = bootstrap.existing_groups(token, root_id)
    missing_contexts = sorted(EXPECTED_CONTEXTS - set(contexts))
    missing_groups = sorted(EXPECTED_GROUPS - set(groups))
    processor_counts: dict[str, int] = {}
    invalid: dict[str, list[dict[str, object]]] = {}
    invalid_services: dict[str, list[dict[str, object]]] = {}
    catalog = bootstrap.request("GET", "/flow/controller-service-types", token=token)
    assert isinstance(catalog, dict)
    controller_service_types = {
        str(item["type"]) for item in catalog.get("controllerServiceTypes", [])
    }
    required_service_types = {
        "org.apache.nifi.dbcp.DBCPConnectionPool",
        "org.apache.nifi.parquet.ParquetReader",
    }
    missing_service_types = sorted(required_service_types - controller_service_types)
    for name in sorted(EXPECTED_GROUPS & set(groups)):
        group_id = str(groups[name]["id"])
        processors = bootstrap.existing_processors(token, group_id)
        services = bootstrap.existing_controller_services(token, group_id)
        processor_counts[name] = len(processors)
        group_invalid = []
        for processor in processors.values():
            component = processor["component"]
            errors = component.get("validationErrors", [])
            if errors:
                group_invalid.append({"name": component["name"], "errors": errors})
        if group_invalid:
            invalid[name] = group_invalid
        group_invalid_services = []
        for service in services.values():
            component = service["component"]
            errors = component.get("validationErrors", [])
            if errors or component.get("state") != "ENABLED":
                group_invalid_services.append(
                    {
                        "name": component["name"],
                        "state": component.get("state"),
                        "errors": errors,
                    }
                )
        if group_invalid_services:
            invalid_services[name] = group_invalid_services
    payload = {
        "event": "nifi_smoke_test",
        "missing_contexts": missing_contexts,
        "missing_groups": missing_groups,
        "processor_counts": processor_counts,
        "invalid_processors": invalid,
        "invalid_controller_services": invalid_services,
        "missing_controller_service_types": missing_service_types,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if (
        missing_contexts
        or missing_groups
        or invalid
        or invalid_services
        or missing_service_types
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
