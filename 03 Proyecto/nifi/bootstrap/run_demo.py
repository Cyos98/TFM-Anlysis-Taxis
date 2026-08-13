"""Ejecuta una única activación del Process Group demo y lo vuelve a detener."""

from __future__ import annotations

import json
import time

import bootstrap


GROUP_NAME = "05_DEMO_PIPELINE"


def schedule(token: str, group_id: str, state: str) -> None:
    bootstrap.request(
        "PUT",
        f"/flow/process-groups/{group_id}",
        token=token,
        payload={"id": group_id, "state": state},
    )


def main() -> int:
    token = bootstrap.authenticate()
    root_id = bootstrap.root_group_id(token)
    groups = bootstrap.existing_groups(token, root_id)
    if GROUP_NAME not in groups:
        raise RuntimeError(f"No existe el Process Group {GROUP_NAME}; ejecute el bootstrap")
    group_id = str(groups[GROUP_NAME]["id"])
    schedule(token, group_id, "RUNNING")
    started = time.monotonic()
    last_status: dict[str, object] = {}
    try:
        while time.monotonic() - started < 180:
            entity = bootstrap.request(
                "GET", f"/flow/process-groups/{group_id}/status", token=token
            )
            assert isinstance(entity, dict)
            snapshot = entity["processGroupStatus"]["aggregateSnapshot"]
            last_status = {
                "active_threads": snapshot["activeThreadCount"],
                "queued_count": snapshot["flowFilesQueued"],
                "queued_size": snapshot["bytesQueued"],
            }
            if time.monotonic() - started >= 15 and (
                int(snapshot["activeThreadCount"]) == 0
                and int(snapshot["flowFilesQueued"]) == 0
            ):
                break
            time.sleep(2)
        else:
            raise TimeoutError(f"La demo NiFi no terminó: {last_status}")
    finally:
        schedule(token, group_id, "STOPPED")
    print(
        json.dumps(
            {
                "event": "nifi_demo_completed",
                "group": GROUP_NAME,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "final_status": last_status,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

