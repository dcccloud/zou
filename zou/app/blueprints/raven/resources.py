import uuid

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from zou.app import db
from zou.app.models.comment import Comment, CommentPreviewLink
from zou.app.models.entity import Entity
from zou.app.models.preview_file import PreviewFile
from zou.app.models.task import Task
from zou.app.models.task_type import TaskType
from zou.app.services import entities_service, user_service
from zou.app.utils import fields

MAX_BUNDLE_ENTITY_IDS = 100


def _query_preview_version_rows(entity_ids):
    return (
        db.session.query(Comment, PreviewFile, Task, TaskType.name)
        .join(Task, Task.id == Comment.object_id)
        .join(TaskType, TaskType.id == Task.task_type_id)
        .join(CommentPreviewLink, CommentPreviewLink.comment == Comment.id)
        .join(
            PreviewFile,
            PreviewFile.id == CommentPreviewLink.preview_file,
        )
        .filter(Task.entity_id.in_(entity_ids))
        .order_by(PreviewFile.revision, Comment.created_at)
        .all()
    )


def _serialize_version_row(comment, preview_file, task, task_type_name):
    return {
        "comment_id": str(comment.id),
        "comment_created_at": fields.serialize_value(comment.created_at),
        "comment_text": comment.text or "",
        "task_id": str(task.id),
        "task_type_id": str(task.task_type_id),
        "task_type_name": task_type_name,
        "preview_file": preview_file.serialize(),
    }


class EntityPreviewVersionsBundleResource(Resource):
    """
    Return every preview file attached to the tasks of a given entity in a
    single response. Task type name, comment and preview file are joined
    server side so API consumers do not have to walk
    tasks -> comments -> preview files one request at a time.
    """

    @jwt_required()
    def get(self, entity_id):
        entity = entities_service.get_entity(entity_id)
        user_service.check_project_access(entity["project_id"])

        rows = _query_preview_version_rows([entity_id])
        versions = [_serialize_version_row(*row) for row in rows]

        return {"entity_id": entity_id, "versions": versions}


class EntityPreviewVersionsBundlesResource(Resource):
    """
    Batch variant: ?entity_ids=<uuid>,<uuid>,... returns one bundle per
    requested entity (empty versions for entities without previews or that
    do not exist), all built from a single JOIN query.
    """

    @jwt_required()
    def get(self):
        raw = request.args.get("entity_ids", "")
        entity_ids = []
        for entity_id in raw.split(","):
            entity_id = entity_id.strip()
            if entity_id and entity_id not in entity_ids:
                entity_ids.append(entity_id)

        if not entity_ids:
            return {"bundles": []}
        if len(entity_ids) > MAX_BUNDLE_ENTITY_IDS:
            return {
                "message": "Too many entity_ids (max %s)"
                % MAX_BUNDLE_ENTITY_IDS
            }, 400
        try:
            for entity_id in entity_ids:
                uuid.UUID(entity_id)
        except ValueError:
            return {"message": "entity_ids must be valid UUIDs"}, 400

        entities = Entity.query.filter(Entity.id.in_(entity_ids)).all()
        for project_id in {str(entity.project_id) for entity in entities}:
            user_service.check_project_access(project_id)

        entity_map = {str(entity.id): entity for entity in entities}
        bundles = {
            entity_id: {
                "entity": (
                    entity_map[entity_id].serialize()
                    if entity_id in entity_map
                    else None
                ),
                "entity_id": entity_id,
                "versions": [],
            }
            for entity_id in entity_ids
        }
        for row in _query_preview_version_rows(entity_ids):
            task = row[2]
            bundles[str(task.entity_id)]["versions"].append(
                _serialize_version_row(*row)
            )

        return {"bundles": [bundles[entity_id] for entity_id in entity_ids]}
