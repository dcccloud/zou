import os

from zou.app import config
from zou.app.services import preview_files_service
from zou.app.stores import file_store
from zou.app.utils import fs
from zou.utils import movie


def _get_required(payload, key):
    value = payload.get(key)
    if value in [None, ""]:
        raise ValueError(f"Missing required payload field: {key}")
    return value


def _get_movie_path(payload, default_prefix="source"):
    prefix = payload.get("prefix", default_prefix)
    movie_id = _get_required(payload, "movie_id")
    extension = payload.get("extension", ".mp4")
    if not extension.startswith("."):
        extension = f".{extension}"
    return fs.get_file_path_and_file(
        config,
        file_store.get_local_movie_path,
        file_store.open_movie,
        prefix,
        movie_id,
        extension,
    )


def _cleanup(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def execute(job):
    action = job["action"]
    payload = job.get("payload") or {}

    if action == "normalize_movie":
        preview_file_id = _get_required(payload, "preview_file_id")
        movie_path = _get_movie_path(payload, default_prefix="source")
        normalize = bool(payload.get("normalize", True))
        add_source_to_file_store = bool(
            payload.get("add_source_to_file_store", False)
        )
        preview_file = preview_files_service.prepare_and_store_movie(
            preview_file_id,
            movie_path,
            normalize=normalize,
            add_source_to_file_store=add_source_to_file_store,
        )
        return {
            "preview_file_id": str(preview_file_id),
            "preview_file": preview_file,
        }

    if action == "generate_thumbnail":
        movie_path = _get_movie_path(payload)
        thumbnail_path = movie.generate_thumbnail(movie_path)
        picture_id = payload.get("picture_id") or payload.get("movie_id")
        picture_prefix = payload.get("picture_prefix", "thumbnails")
        if picture_id:
            file_store.add_picture(picture_prefix, picture_id, thumbnail_path)
        result = {"thumbnail_path": thumbnail_path}
        if picture_id:
            result.update(
                {"picture_prefix": picture_prefix, "picture_id": picture_id}
            )
            _cleanup(thumbnail_path)
        return result

    if action == "generate_tile":
        movie_path = _get_movie_path(payload)
        tile_path = movie.generate_tile(movie_path)
        tile_id = payload.get("tile_id") or payload.get("movie_id")
        tile_prefix = payload.get("tile_prefix", "tiles")
        if tile_id:
            file_store.add_picture(tile_prefix, tile_id, tile_path)
        result = {"tile_path": tile_path}
        if tile_id:
            result.update({"tile_prefix": tile_prefix, "tile_id": tile_id})
            _cleanup(tile_path)
        return result

    raise ValueError(f"Unsupported video-processing action: {action}")
