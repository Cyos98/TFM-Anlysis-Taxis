"""Bootstrap idempotente de Parameter Contexts y Process Groups de NiFi."""

from __future__ import annotations

import json
import os
from pathlib import Path
import ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


BASE_URL = os.getenv("NIFI_API_URL", "https://nifi:8443/nifi-api").rstrip("/")
USERNAME = os.environ["NIFI_USERNAME"]
PASSWORD = os.environ["NIFI_PASSWORD"]
SPEC_PATH = Path(os.getenv("NIFI_FLOW_SPEC", "/bootstrap/flow_spec.json"))
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE


def request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict[str, object] | None = None,
    form: dict[str, str] | None = None,
    accept: str = "application/json",
) -> object:
    headers = {"Accept": accept}
    body: bytes | None = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    elif form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urlencode(form).encode("ascii")
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30, context=CONTEXT) as response:
            content = response.read()
            if not content:
                return None
            if "application/json" in response.headers.get("Content-Type", ""):
                return json.loads(content)
            return content.decode("utf-8")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NiFi {method} {path}: HTTP {exc.code}: {details}") from exc


def wait_for_nifi() -> None:
    for attempt in range(90):
        try:
            ui_url = BASE_URL.removesuffix("/nifi-api") + "/nifi"
            req = Request(ui_url, method="GET")
            with urlopen(req, timeout=5, context=CONTEXT):
                return
        except HTTPError as exc:
            if exc.code in {401, 403}:
                return
            time.sleep(2)
        except (URLError, TimeoutError):
            time.sleep(2)
    raise TimeoutError("NiFi no respondió en el tiempo esperado")


def authenticate() -> str:
    token = request(
        "POST",
        "/access/token",
        form={"username": USERNAME, "password": PASSWORD},
        accept="text/plain",
    )
    if not isinstance(token, str) or not token:
        raise RuntimeError("NiFi no devolvió un token de acceso")
    return token


def root_group_id(token: str) -> str:
    entity = request("GET", "/flow/process-groups/root", token=token)
    assert isinstance(entity, dict)
    return str(entity["processGroupFlow"]["id"])


def existing_contexts(token: str) -> dict[str, dict[str, object]]:
    entity = request("GET", "/flow/parameter-contexts", token=token)
    assert isinstance(entity, dict)
    return {
        str(item["component"]["name"]): item
        for item in entity.get("parameterContexts", [])
    }


def parameter_value(parameter: dict[str, object]) -> str:
    environment = parameter.get("environment")
    if environment:
        value = os.getenv(str(environment), str(parameter.get("default", "")))
    else:
        value = str(parameter.get("value", parameter.get("default", "")))
    if parameter.get("sensitive") and not value:
        raise ValueError(f"Falta el parámetro sensible {parameter['name']}")
    return value


def ensure_contexts(token: str, spec: dict[str, object]) -> dict[str, str]:
    current = existing_contexts(token)
    identifiers: dict[str, str] = {}
    for context_spec in spec["parameter_contexts"]:
        name = str(context_spec["name"])
        parameters = [
            {
                "parameter": {
                    "name": str(parameter["name"]),
                    "description": str(parameter.get("description", "")),
                    "sensitive": bool(parameter.get("sensitive", False)),
                    "value": parameter_value(parameter),
                }
            }
            for parameter in context_spec.get("parameters", [])
        ]
        if name in current:
            existing = current[name]
            context_id = str(existing["id"])
            entity = request(
                "PUT",
                f"/parameter-contexts/{context_id}",
                token=token,
                payload={
                    "revision": {
                        "version": existing["revision"]["version"],
                        "clientId": str(uuid4()),
                    },
                    "component": {
                        "id": context_id,
                        "name": name,
                        "description": str(context_spec.get("description", "")),
                        "parameters": parameters,
                    },
                },
            )
            assert isinstance(entity, dict)
            identifiers[name] = context_id
            continue
        entity = request(
            "POST",
            "/parameter-contexts",
            token=token,
            payload={
                "revision": {"version": 0, "clientId": str(uuid4())},
                "component": {
                    "name": name,
                    "description": str(context_spec.get("description", "")),
                    "parameters": parameters,
                },
            },
        )
        assert isinstance(entity, dict)
        identifiers[name] = str(entity["id"])
    return identifiers


def existing_groups(token: str, root_id: str) -> dict[str, dict[str, object]]:
    entity = request("GET", f"/process-groups/{root_id}/process-groups", token=token)
    assert isinstance(entity, dict)
    return {
        str(item["component"]["name"]): item
        for item in entity.get("processGroups", [])
    }


def ensure_groups(
    token: str,
    root_id: str,
    pipeline_context_id: str,
    spec: dict[str, object],
) -> dict[str, str]:
    current = existing_groups(token, root_id)
    identifiers: dict[str, str] = {}
    for group_spec in spec["process_groups"]:
        name = str(group_spec["name"])
        if name in current:
            identifiers[name] = str(current[name]["id"])
            continue
        entity = request(
            "POST",
            f"/process-groups/{root_id}/process-groups",
            token=token,
            payload={
                "revision": {"version": 0, "clientId": str(uuid4())},
                "component": {
                    "name": name,
                    "position": {"x": group_spec["x"], "y": group_spec["y"]},
                    "parameterContext": {"id": pipeline_context_id},
                },
            },
        )
        assert isinstance(entity, dict)
        identifiers[name] = str(entity["id"])
    return identifiers


def existing_processors(token: str, group_id: str) -> dict[str, dict[str, object]]:
    entity = request("GET", f"/process-groups/{group_id}/processors", token=token)
    assert isinstance(entity, dict)
    return {
        str(item["component"]["name"]): item
        for item in entity.get("processors", [])
    }


def existing_controller_services(
    token: str, group_id: str
) -> dict[str, dict[str, object]]:
    entity = request(
        "GET", f"/flow/process-groups/{group_id}/controller-services", token=token
    )
    assert isinstance(entity, dict)
    return {
        str(item["component"]["name"]): item
        for item in entity.get("controllerServices", [])
    }


def ensure_controller_services(
    token: str,
    group_ids: dict[str, str],
    spec: dict[str, object],
) -> tuple[dict[str, int], dict[str, dict[str, str]]]:
    counts: dict[str, int] = {}
    identifiers: dict[str, dict[str, str]] = {}
    pending_enable: list[tuple[str, dict[str, object]]] = []
    for group_spec in spec["process_groups"]:
        group_name = str(group_spec["name"])
        group_id = group_ids[group_name]
        current = existing_controller_services(token, group_id)
        created = 0
        group_identifiers: dict[str, str] = {}
        for service_spec in group_spec.get("controller_services", []):
            name = str(service_spec["name"])
            component = {
                "name": name,
                "type": str(service_spec["type"]),
                "bundle": {
                    "group": "org.apache.nifi",
                    "artifact": str(service_spec["artifact"]),
                    "version": str(spec["nifi_version"]),
                },
                "properties": service_spec.get("properties", {}),
                "comments": "Gestionado por nifi/bootstrap/bootstrap.py",
            }
            if name in current:
                existing = current[name]
                service_id = str(existing["id"])
                if existing["component"].get("state") == "ENABLED":
                    entity = existing
                else:
                    component["id"] = service_id
                    entity = request(
                        "PUT",
                        f"/controller-services/{service_id}",
                        token=token,
                        payload={
                            "revision": {
                                "version": existing["revision"]["version"],
                                "clientId": str(uuid4()),
                            },
                            "component": component,
                        },
                    )
            else:
                entity = request(
                    "POST",
                    f"/process-groups/{group_id}/controller-services",
                    token=token,
                    payload={
                        "revision": {"version": 0, "clientId": str(uuid4())},
                        "component": component,
                    },
                )
                created += 1
            assert isinstance(entity, dict)
            service_id = str(entity["id"])
            group_identifiers[name] = service_id
            pending_enable.append((service_id, entity))
        counts[group_name] = len(current) + created
        identifiers[group_name] = group_identifiers

    for service_id, entity in pending_enable:
        component = entity["component"]
        if component.get("state") == "ENABLED":
            continue
        request(
            "PUT",
            f"/controller-services/{service_id}/run-status",
            token=token,
            payload={
                "revision": {
                    "version": entity["revision"]["version"],
                    "clientId": str(uuid4()),
                },
                "state": "ENABLED",
            },
        )
    return counts, identifiers


def resolve_properties(
    properties: dict[str, object], service_ids: dict[str, str]
) -> dict[str, object]:
    resolved: dict[str, object] = {}
    for key, value in properties.items():
        if isinstance(value, str) and value.startswith("@service:"):
            service_name = value.removeprefix("@service:")
            if service_name not in service_ids:
                raise KeyError(f"Controller Service no definido: {service_name}")
            resolved[key] = service_ids[service_name]
        else:
            resolved[key] = value
    return resolved


def ensure_processors(
    token: str,
    group_ids: dict[str, str],
    service_ids: dict[str, dict[str, str]],
    spec: dict[str, object],
) -> tuple[dict[str, int], dict[str, dict[str, str]]]:
    counts: dict[str, int] = {}
    identifiers: dict[str, dict[str, str]] = {}
    for group_spec in spec["process_groups"]:
        group_name = str(group_spec["name"])
        group_id = group_ids[group_name]
        current = existing_processors(token, group_id)
        created = 0
        group_identifiers: dict[str, str] = {}
        for index, processor_spec in enumerate(group_spec.get("processors", [])):
            name = str(processor_spec["name"])
            aliases = [str(alias) for alias in processor_spec.get("legacy_names", [])]
            configuration = {
                "properties": resolve_properties(
                    processor_spec.get("properties", {}), service_ids[group_name]
                ),
                "schedulingStrategy": processor_spec.get(
                    "scheduling_strategy", "TIMER_DRIVEN"
                ),
                "schedulingPeriod": processor_spec.get("scheduling_period", "0 sec"),
                "executionNode": "ALL",
                "concurrentlySchedulableTaskCount": 1,
                "autoTerminatedRelationships": processor_spec.get(
                    "auto_terminate", []
                ),
                "comments": "Gestionado por nifi/bootstrap/bootstrap.py",
            }
            current_name = next(
                (candidate for candidate in [name, *aliases] if candidate in current),
                None,
            )
            if current_name is not None:
                existing = current[current_name]
                entity = request(
                    "PUT",
                    f"/processors/{existing['id']}",
                    token=token,
                    payload={
                        "revision": {
                            "version": existing["revision"]["version"],
                            "clientId": str(uuid4()),
                        },
                        "component": {
                            "id": existing["id"],
                            "name": name,
                            "position": {"x": 0, "y": index * 180},
                            "config": configuration,
                        },
                    },
                )
            else:
                entity = request(
                    "POST",
                    f"/process-groups/{group_id}/processors",
                    token=token,
                    payload={
                        "revision": {"version": 0, "clientId": str(uuid4())},
                        "component": {
                            "name": name,
                            "type": str(processor_spec["type"]),
                            "bundle": {
                                "group": "org.apache.nifi",
                                "artifact": str(processor_spec["artifact"]),
                                "version": str(spec["nifi_version"]),
                            },
                            "position": {"x": 0, "y": index * 180},
                            "config": configuration,
                        },
                    },
                )
                created += 1
            assert isinstance(entity, dict)
            group_identifiers[name] = str(entity["id"])
        counts[group_name] = len(current) + created
        identifiers[group_name] = group_identifiers
    return counts, identifiers


def existing_connections(token: str, group_id: str) -> dict[str, dict[str, object]]:
    entity = request("GET", f"/process-groups/{group_id}/connections", token=token)
    assert isinstance(entity, dict)
    return {
        str(item["component"].get("name", "")): item
        for item in entity.get("connections", [])
    }


def ensure_connections(
    token: str,
    group_ids: dict[str, str],
    processor_ids: dict[str, dict[str, str]],
    spec: dict[str, object],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for group_spec in spec["process_groups"]:
        group_name = str(group_spec["name"])
        group_id = group_ids[group_name]
        current = existing_connections(token, group_id)
        created = 0
        for connection_spec in group_spec.get("connections", []):
            name = str(connection_spec["name"])
            if name in current:
                continue
            source_id = processor_ids[group_name][str(connection_spec["source"])]
            destination_id = processor_ids[group_name][str(connection_spec["destination"])]
            request(
                "POST",
                f"/process-groups/{group_id}/connections",
                token=token,
                payload={
                    "revision": {"version": 0, "clientId": str(uuid4())},
                    "component": {
                        "name": name,
                        "source": {
                            "id": source_id,
                            "groupId": group_id,
                            "type": "PROCESSOR",
                        },
                        "destination": {
                            "id": destination_id,
                            "groupId": group_id,
                            "type": "PROCESSOR",
                        },
                        "selectedRelationships": connection_spec["relationships"],
                        "flowFileExpiration": "0 sec",
                        "backPressureObjectThreshold": 10000,
                        "backPressureDataSizeThreshold": "1 GB",
                        "loadBalanceStrategy": "DO_NOT_LOAD_BALANCE",
                    },
                },
            )
            created += 1
        counts[group_name] = len(current) + created
    return counts


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    wait_for_nifi()
    token = authenticate()
    root_id = root_group_id(token)
    contexts = ensure_contexts(token, spec)
    groups = ensure_groups(token, root_id, contexts["PIPELINE"], spec)
    services, service_ids = ensure_controller_services(token, groups, spec)
    processors, processor_ids = ensure_processors(token, groups, service_ids, spec)
    connections = ensure_connections(token, groups, processor_ids, spec)
    print(
        json.dumps(
            {
                "event": "nifi_bootstrap_complete",
                "nifi_version": spec["nifi_version"],
                "parameter_contexts": sorted(contexts),
                "process_groups": sorted(groups),
                "processors": processors,
                "controller_services": services,
                "connections": connections,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {"event": "nifi_bootstrap_failed", "error": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise
