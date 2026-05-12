from sqlalchemy.exc import StatementError

from zou.app.models.personal_asset import PersonalAsset
from zou.app.services import assets_service, persons_service
from zou.app.services.exception import PersonalAssetNotFoundException
from zou.app.utils import events, permissions


def get_personal_asset_raw(personal_asset_id):
    try:
        personal_asset = PersonalAsset.get(personal_asset_id)
    except StatementError:
        raise PersonalAssetNotFoundException
    if personal_asset is None:
        raise PersonalAssetNotFoundException
    return personal_asset


def get_personal_asset(personal_asset_id):
    return get_personal_asset_raw(personal_asset_id).serialize()


def get_personal_assets_for_person(person_id):
    personal_assets = PersonalAsset.get_all_by(person_id=person_id)
    return PersonalAsset.serialize_list(personal_assets)


def create_personal_asset(
    person_id,
    name,
    description="",
    file_name=None,
    extension=None,
    file_size=0,
    source="upload",
    data=None,
    project_id=None,
):
    personal_asset = PersonalAsset.create(
        person_id=person_id,
        name=name,
        description=description,
        file_name=file_name,
        extension=extension,
        file_size=file_size,
        source=source,
        data=data or {},
        project_id=project_id,
    )
    personal_asset_dict = personal_asset.serialize()
    events.emit(
        "personal-asset:new",
        {"personal_asset_id": personal_asset_dict["id"]},
        project_id=personal_asset_dict.get("project_id"),
    )
    return personal_asset_dict


def update_personal_asset(personal_asset_id, data):
    personal_asset = get_personal_asset_raw(personal_asset_id)
    personal_asset.update(data)
    personal_asset_dict = personal_asset.serialize()
    events.emit(
        "personal-asset:update",
        {"personal_asset_id": personal_asset_dict["id"]},
        project_id=personal_asset_dict.get("project_id"),
    )
    return personal_asset_dict


def delete_personal_asset(personal_asset_id):
    personal_asset = get_personal_asset_raw(personal_asset_id)
    personal_asset_dict = personal_asset.serialize()
    personal_asset.delete()
    events.emit(
        "personal-asset:delete",
        {"personal_asset_id": personal_asset_dict["id"]},
        project_id=personal_asset_dict.get("project_id"),
    )
    return personal_asset_dict


def check_personal_asset_access(personal_asset_dict):
    if permissions.has_admin_permissions():
        return True
    current_user = persons_service.get_current_user()
    if personal_asset_dict["person_id"] != current_user["id"]:
        raise permissions.PermissionDenied
    return True


def promote_to_entity(personal_asset_id, project_id, asset_type_id):
    personal_asset = get_personal_asset_raw(personal_asset_id)
    personal_asset_dict = personal_asset.serialize()
    current_user = persons_service.get_current_user()

    entity = assets_service.create_asset(
        project_id=project_id,
        asset_type_id=asset_type_id,
        name=personal_asset_dict["name"],
        description=personal_asset_dict.get("description", ""),
        data=personal_asset_dict.get("data", {}),
        created_by=current_user["id"],
    )

    personal_asset.update(
        {
            "entity_id": entity["id"],
            "project_id": project_id,
        }
    )

    updated_dict = personal_asset.serialize()
    events.emit(
        "personal-asset:promote",
        {
            "personal_asset_id": updated_dict["id"],
            "entity_id": entity["id"],
        },
        project_id=project_id,
    )
    return updated_dict
