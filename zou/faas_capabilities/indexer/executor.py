from zou.app import app
from zou.app.indexer import indexing
from zou.app.services import (
    assets_service,
    index_service,
    persons_service,
    shots_service,
)


def _ensure_indexer_client():
    if "indexer_client" not in app.extensions:
        app.extensions["indexer_client"] = indexing.init_client()


def _get_required(payload, key):
    value = payload.get(key)
    if value in [None, ""]:
        raise ValueError(f"Missing required payload field: {key}")
    return value


def execute(job):
    _ensure_indexer_client()
    action = job["action"]
    payload = job.get("payload") or {}

    if action == "reset_index":
        index_service.reset_index()
        return {"reset": True}

    if action == "index_asset":
        asset = assets_service.get_asset_raw(_get_required(payload, "asset_id"))
        document = index_service.index_asset(asset)
        return {"document": document}

    if action == "index_person":
        person = persons_service.get_person_raw(
            _get_required(payload, "person_id")
        )
        document = index_service.index_person(person)
        return {"document": document}

    if action == "index_shot":
        shot = shots_service.get_shot_raw(_get_required(payload, "shot_id"))
        document = index_service.index_shot(shot)
        return {"document": document}

    if action == "remove_asset":
        asset_id = _get_required(payload, "asset_id")
        index_service.remove_asset_index(asset_id)
        return {"removed_id": asset_id}

    if action == "remove_person":
        person_id = _get_required(payload, "person_id")
        index_service.remove_person_index(person_id)
        return {"removed_id": person_id}

    if action == "remove_shot":
        shot_id = _get_required(payload, "shot_id")
        index_service.remove_shot_index(shot_id)
        return {"removed_id": shot_id}

    raise ValueError(f"Unsupported indexer action: {action}")
