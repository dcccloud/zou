from zou.faas_capabilities.common import register_capability_routes
from zou.faas_capabilities.actions import CAPABILITY_ACTIONS
from zou.faas_capabilities.video_processing.executor import execute

app = register_capability_routes(
    "video-processing",
    CAPABILITY_ACTIONS["video-processing"],
    execute_job=execute,
)
