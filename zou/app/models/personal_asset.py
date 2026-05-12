from sqlalchemy_utils import UUIDType
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class PersonalAsset(db.Model, BaseMixin, SerializerMixin):
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text())
    file_name = db.Column(db.String(250))
    extension = db.Column(db.String(10))
    file_size = db.Column(db.BigInteger(), default=0)
    source = db.Column(db.String(40), default="upload")
    data = db.Column(JSONB)

    person_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("project.id"),
        nullable=True,
        index=True,
    )
    entity_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("entity.id"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "name",
            "person_id",
            name="personal_asset_uc",
        ),
    )

    def __repr__(self):
        return "<PersonalAsset %s>" % self.id
