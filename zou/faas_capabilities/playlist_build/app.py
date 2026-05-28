from zou.faas_capabilities.common import register_capability_routes
from zou.faas_capabilities.actions import CAPABILITY_ACTIONS
from zou.faas_capabilities.playlist_build.executor import execute

app = register_capability_routes(
    "playlist-build", CAPABILITY_ACTIONS["playlist-build"], execute_job=execute
)
