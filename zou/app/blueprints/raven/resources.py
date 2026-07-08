from flask_jwt_extended import jwt_required
from flask_restful import Resource

from zou.app import db
from zou.app.models.comment import Comment, CommentPreviewLink
from zou.app.models.preview_file import PreviewFile
from zou.app.models.task import Task
from zou.app.models.task_type import TaskType
from zou.app.services import entities_service, user_service
from zou.app.utils import fields


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

        rows = (
            db.session.query(Comment, PreviewFile, Task, TaskType.name)
            .join(Task, Task.id == Comment.object_id)
            .join(TaskType, TaskType.id == Task.task_type_id)
            .join(CommentPreviewLink, CommentPreviewLink.comment == Comment.id)
            .join(
                PreviewFile,
                PreviewFile.id == CommentPreviewLink.preview_file,
            )
            .filter(Task.entity_id == entity_id)
            .order_by(PreviewFile.revision, Comment.created_at)
            .all()
        )

        versions = [
            {
                "comment_id": str(comment.id),
                "comment_created_at": fields.serialize_value(
                    comment.created_at
                ),
                "comment_text": comment.text or "",
                "task_id": str(task.id),
                "task_type_id": str(task.task_type_id),
                "task_type_name": task_type_name,
                "preview_file": preview_file.serialize(),
            }
            for (comment, preview_file, task, task_type_name) in rows
        ]

        return {"entity_id": entity_id, "versions": versions}
