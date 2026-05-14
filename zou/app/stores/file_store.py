import os
import flask_fs

import boto3
from flask import current_app
from werkzeug.utils import cached_property

from zou.app import config

from flask_fs.backends.local import LocalBackend
from flask_fs.backends.s3 import S3Backend

_original_s3_init = S3Backend.__init__


def _s3_init_virtual_host(self, name, cfg):
    """Patch S3Backend to use virtual-hosted-style addressing (required by
    Alibaba Cloud OSS and recommended by AWS)."""
    super(S3Backend, self).__init__(name, cfg)

    self.session = boto3.session.Session()
    self.s3config = boto3.session.Config(
        signature_version="s3v4",
        s3={
            "addressing_style": "virtual",
            "payload_signing_enabled": True,
        },
        request_checksum_calculation="when_required",
    )
    self.s3 = self.session.resource(
        "s3",
        config=self.s3config,
        endpoint_url=cfg.endpoint,
        region_name=cfg.region,
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
    )
    self.bucket = self.s3.Bucket(name)


S3Backend.__init__ = _s3_init_virtual_host

pictures = None
movies = None
files = None


def path(self, filename):
    folder_one = filename.split("-")[0]
    file_name = "-".join(filename.split("-")[1:])

    # Ensure root is absolute to avoid issues with relative paths
    root = (
        os.path.abspath(self.root)
        if not os.path.isabs(self.root)
        else self.root
    )

    if folder_one == "dbbackup":
        file_path = os.path.join(root, folder_one, file_name)
    else:
        folder_two = file_name[:3]
        folder_three = file_name[3:6]
        file_path = os.path.join(
            root, folder_one, folder_two, folder_three, file_name
        )
    # Normalize path to handle any remaining relative components
    return os.path.normpath(file_path)


LocalBackend.path = path


@cached_property
def _default_root(self):
    """
    Read the storage default root without opening a nested app context.

    The upstream LocalBackend wraps this in ``with current_app.app_context():``
    which, on teardown, triggers Flask-SQLAlchemy's ``db.session.remove()``
    handler. Since storage operations always happen inside a request that
    already has an app context, the nested context only serves to wipe the
    outer request's session and detach every loaded ORM instance.
    """
    default_root = current_app.config.get("FS_ROOT")
    return current_app.config.get("FS_LOCAL_ROOT", default_root)


LocalBackend.default_root = _default_root


def configure_storages(app):
    global pictures, movies, files
    pictures = make_storage("pictures")
    movies = make_storage("movies")
    files = make_storage("files")

    flask_fs.init_app(app, *[pictures, movies, files])


def clear_bucket(bucket):
    for filename in bucket.list_files():
        if isinstance(bucket.backend, LocalBackend):
            parts = filename.split("/")
            if len(parts) >= 2:
                bucket.delete(f"{parts[0]}-{parts[-1]}")
            else:
                bucket.delete(filename)
        else:
            bucket.delete(filename)


def make_key(prefix, id):
    return f"{prefix}-{id}"


def make_read_generator(bucket, key):
    """
    Create a generator that yields chunks from the storage bucket.
    This function ensures proper cleanup of the underlying stream to avoid
    reentrant call errors when the stream is accessed concurrently.
    """
    read_stream = bucket.read_chunks(key)

    def read_generator(read_stream):
        try:
            for chunk in read_stream:
                yield chunk
        finally:
            if hasattr(read_stream, "close"):
                try:
                    read_stream.close()
                except Exception:
                    pass

    return read_generator(read_stream)


def make_storage(bucket):
    return flask_fs.Storage(
        "%s%s" % (config.FS_BUCKET_PREFIX, bucket),
        overwrite=True,
    )


def clear():
    clear_bucket(pictures)
    clear_bucket(movies)
    clear_bucket(files)


def add_picture(prefix, id, path):
    key = make_key(prefix, id)
    with open(path, "rb") as fd:
        return pictures.write(key, fd)


def get_picture(prefix, id):
    key = make_key(prefix, id)
    return pictures.read(key)


def open_picture(prefix, id):
    key = make_key(prefix, id)
    return make_read_generator(pictures, key)


def read_picture(prefix, id):
    key = make_key(prefix, id)
    return pictures.read(key)


def exists_picture(prefix, id):
    key = make_key(prefix, id)
    return pictures.exists(key)


def remove_picture(prefix, id):
    key = make_key(prefix, id)
    return pictures.delete(key)


def get_local_picture_path(prefix, id):
    return path(pictures, make_key(prefix, id))


def copy_picture(prefix, id, new_prefix, new_id):
    key = make_key(prefix, id)
    target = make_key(new_prefix, new_id)
    return pictures.copy(key, target)


def add_movie(prefix, id, path):
    key = make_key(prefix, id)
    with open(path, "rb") as fd:
        return movies.write(key, fd)


def get_movie(prefix, id):
    key = make_key(prefix, id)
    return movies.read(key)


def open_movie(prefix, id):
    key = make_key(prefix, id)
    return make_read_generator(movies, key)


def read_movie(prefix, id):
    key = make_key(prefix, id)
    return movies.read(key)


def exists_movie(prefix, id):
    key = make_key(prefix, id)
    return movies.exists(key)


def remove_movie(prefix, id):
    key = make_key(prefix, id)
    return movies.delete(key)


def get_local_movie_path(prefix, id):
    return path(movies, make_key(prefix, id))


def copy_movie(prefix, id, new_prefix, new_id):
    key = make_key(prefix, id)
    target = make_key(new_prefix, new_id)
    return movies.copy(key, target)


def add_file(prefix, id, path):
    key = make_key(prefix, id)
    with open(path, "rb") as fd:
        return files.write(key, fd)


def get_file(prefix, id):
    key = make_key(prefix, id)
    return files.read(key)


def open_file(prefix, id):
    key = make_key(prefix, id)
    return make_read_generator(files, key)


def read_file(prefix, id):
    key = make_key(prefix, id)
    return files.read(key)


def exists_file(prefix, id):
    key = make_key(prefix, id)
    return files.exists(key)


def remove_file(prefix, id):
    key = make_key(prefix, id)
    return files.delete(key)


def get_local_file_path(prefix, id):
    return path(files, make_key(prefix, id))


def copy_file(prefix, id, new_prefix, new_id):
    key = make_key(prefix, id)
    target = make_key(new_prefix, new_id)
    return files.copy(key, target)


_external_s3_client = None


def _get_external_s3_client():
    global _external_s3_client
    if _external_s3_client is not None:
        return _external_s3_client
    if not config.EXTERNAL_S3_ENDPOINT or not config.EXTERNAL_S3_BUCKET:
        return None
    _external_s3_client = boto3.client(
        "s3",
        endpoint_url=config.EXTERNAL_S3_ENDPOINT,
        region_name=config.EXTERNAL_S3_REGION or "us-east-1",
        aws_access_key_id=config.EXTERNAL_S3_ACCESS_KEY,
        aws_secret_access_key=config.EXTERNAL_S3_SECRET_KEY,
        config=boto3.session.Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        ),
    )
    return _external_s3_client


def generate_external_presigned_url(key, expiration=7200):
    client = _get_external_s3_client()
    if client is None:
        return None
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": config.EXTERNAL_S3_BUCKET,
            "Key": key,
        },
        ExpiresIn=expiration,
    )
