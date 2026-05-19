from fido2.webauthn import (
    PublicKeyCredentialRpEntity,
)
from fido2.server import Fido2Server
from urllib.parse import urlparse

from zou.app import config

DEFAULT_FIDO_RP_ID = "localhost"


def get_fido_rp_id(domain_name=None):
    domain_name = config.DOMAIN_NAME if domain_name is None else domain_name
    domain_name = (domain_name or "").strip()
    if not domain_name:
        return DEFAULT_FIDO_RP_ID

    parsed_url = urlparse(domain_name)
    if parsed_url.hostname is None:
        parsed_url = urlparse(f"https://{domain_name}")

    return parsed_url.hostname or DEFAULT_FIDO_RP_ID


def get_fido_server():
    rp_id = get_fido_rp_id()
    return Fido2Server(
        PublicKeyCredentialRpEntity(name="Kitsu", id=rp_id),
        verify_origin=(
            None if config.DOMAIN_NAME != "localhost:8080" else lambda a: True
        ),
    )
