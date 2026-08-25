"""Extrae contratos de propiedades/relaciones del runtime NiFi 2.10."""

from __future__ import annotations

import json

import bootstrap


PROCESSORS = [
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.GenerateFlowFile"),
    ("org.apache.nifi", "nifi-update-attribute-nar", "org.apache.nifi.processors.attributes.UpdateAttribute"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.ExecuteStreamCommand"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.SplitText"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.EvaluateJsonPath"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.ReplaceText"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.PutSQL"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.ExecuteSQLRecord"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.RouteOnAttribute"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.InvokeHTTP"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.CryptographicHashContent"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.PutFile"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.LogMessage"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.ConvertRecord"),
    ("org.apache.nifi", "nifi-standard-nar", "org.apache.nifi.processors.standard.PutDatabaseRecord"),
]

SERVICES = [
    ("org.apache.nifi", "nifi-dbcp-service-nar", "org.apache.nifi.dbcp.DBCPConnectionPool"),
    ("org.apache.nifi", "nifi-record-serialization-services-nar", "org.apache.nifi.json.JsonRecordSetWriter"),
    ("org.apache.nifi", "nifi-record-serialization-services-nar", "org.apache.nifi.json.JsonTreeReader"),
    ("org.apache.nifi", "nifi-parquet-nar", "org.apache.nifi.parquet.ParquetReader"),
    ("org.apache.nifi", "nifi-parquet-nar", "org.apache.nifi.parquet.ParquetRecordSetWriter"),
]


def summarize(entity: dict[str, object]) -> dict[str, object]:
    definition = (
        entity.get("processorDefinition")
        or entity.get("controllerServiceDefinition")
        or entity
    )
    assert isinstance(definition, dict)
    return {
        "type": definition.get("type"),
        "properties": {
            str(descriptor.get("name")): descriptor.get("defaultValue")
            for descriptor in definition.get("propertyDescriptors", {}).values()
        },
        "relationships": definition.get("supportedRelationships", []),
    }


token = bootstrap.authenticate()
result: dict[str, object] = {"processors": [], "services": []}
for group, artifact, processor_type in PROCESSORS:
    entity = bootstrap.request(
        "GET",
        f"/flow/processor-definition/{group}/{artifact}/2.10.0/{processor_type}",
        token=token,
    )
    assert isinstance(entity, dict)
    result["processors"].append(summarize(entity))
for group, artifact, service_type in SERVICES:
    entity = bootstrap.request(
        "GET",
        f"/flow/controller-service-definition/{group}/{artifact}/2.10.0/{service_type}",
        token=token,
    )
    assert isinstance(entity, dict)
    result["services"].append(summarize(entity))
print(json.dumps(result, indent=2, sort_keys=True))
