import os

from zou.app import config
from zou.app.services import (
    playlists_service,
    preview_files_service,
    projects_service,
)
from zou.app.stores import file_store
from zou.utils.movie import EncodingParameters


def _get_required(payload, key):
    value = payload.get(key)
    if value in [None, ""]:
        raise ValueError(f"Missing required payload field: {key}")
    return value


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ["1", "true", "yes", "on"]:
            return True
        if value in ["0", "false", "no", "off"]:
            return False
    return bool(value)


def _ensure_tmp_dir():
    os.makedirs(config.TMP_DIR, exist_ok=True)


def _get_playlist(payload):
    playlist_id = _get_required(payload, "playlist_id")
    return playlists_service.get_playlist(playlist_id)


def _get_shots(payload, playlist):
    shots = payload.get("shots")
    if shots is not None:
        return shots
    return [
        {"preview_file_id": shot.get("preview_file_id")}
        for shot in playlist.get("shots", [])
    ]


def _get_encoding_parameters(payload, playlist):
    width = payload.get("width")
    height = payload.get("height")
    fps = payload.get("fps")
    if width is not None and height is not None and fps is not None:
        return EncodingParameters(width=int(width), height=int(height), fps=fps)

    project = projects_service.get_project(playlist["project_id"])
    width, height = preview_files_service.get_preview_file_dimensions(project)
    fps = preview_files_service.get_preview_file_fps(project)
    return EncodingParameters(width=width, height=height, fps=fps)


def _get_build_job(payload, playlist):
    build_job_id = payload.get("build_job_id")
    if build_job_id:
        build_job = playlists_service.get_build_job(build_job_id)
        if str(build_job["playlist_id"]) != str(playlist["id"]):
            raise ValueError("build_job_id does not belong to playlist_id")
        return build_job
    return playlists_service.start_build_job(playlist)


def _build_playlist_movie(payload):
    playlist = _get_playlist(payload)
    _ensure_tmp_dir()
    shots = _get_shots(payload, playlist)
    params = _get_encoding_parameters(payload, playlist)
    build_job = _get_build_job(payload, playlist)
    full = _as_bool(payload.get("full"), default=False)
    remote = _as_bool(payload.get("remote"), default=False)

    if remote and config.FS_BACKEND not in ["s3", "swift"]:
        raise ValueError("Remote playlist build requires s3 or swift backend")

    build_job = playlists_service.build_playlist_movie_file(
        playlist,
        build_job,
        shots,
        params,
        full,
        remote,
    )
    return {
        "playlist_id": playlist["id"],
        "build_job_id": build_job["id"],
        "build_job": build_job,
        "movie_prefix": "playlists",
        "movie_id": build_job["id"],
    }


def _build_playlist_zip(payload, capability_job_id):
    playlist = _get_playlist(payload)
    _ensure_tmp_dir()
    zip_file_path = playlists_service.build_playlist_zip_file(playlist)
    output_id = payload.get("output_id") or capability_job_id
    output_prefix = payload.get("output_prefix") or "playlist-zips"
    file_store.add_file(output_prefix, output_id, zip_file_path)
    try:
        os.remove(zip_file_path)
    except OSError:
        pass
    return {
        "playlist_id": playlist["id"],
        "file_prefix": output_prefix,
        "file_id": output_id,
    }


def execute(job):
    action = job["action"]
    payload = job.get("payload") or {}

    if action == "build_playlist_movie":
        return _build_playlist_movie(payload)

    if action == "build_playlist_zip":
        return _build_playlist_zip(payload, job["id"])

    raise ValueError(f"Unsupported playlist-build action: {action}")
