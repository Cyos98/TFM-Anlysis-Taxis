"""Inspección de solo lectura del catálogo NiFi usado por las pruebas."""

from __future__ import annotations

import json

import bootstrap


NAMES = {
    "GenerateFlowFile",
    "UpdateAttribute",
    "ExecuteStreamCommand",
    "SplitText",
    "EvaluateJsonPath",
    "ReplaceText",
    "PutSQL",
    "ExecuteSQLRecord",
    "RouteOnAttribute",
    "InvokeHTTP",
    "HashContent",
    "ValidateRecord",
    "PutFile",
    "LogMessage",
}


token = bootstrap.authenticate()
entity = bootstrap.request("GET", "/flow/processor-types", token=token)
assert isinstance(entity, dict)
selected = [
    item
    for item in entity["processorTypes"]
    if item["type"].rsplit(".", 1)[-1] in NAMES
]
services = bootstrap.request("GET", "/flow/controller-service-types", token=token)
assert isinstance(services, dict)
service_names = {
    "DBCPConnectionPool",
    "JsonRecordSetWriter",
    "AvroReader",
    "ParquetReader",
    "JsonTreeReader",
}
selected_services = [
    item
    for item in services["controllerServiceTypes"]
    if item["type"].rsplit(".", 1)[-1] in service_names
]
hash_processors = [
    item
    for item in entity["processorTypes"]
    if "Hash" in item["type"].rsplit(".", 1)[-1]
]
print(
    json.dumps(
        {
            "processors": selected,
            "hash_processors": hash_processors,
            "controller_services": selected_services,
        },
        indent=2,
        sort_keys=True,
    )
)
