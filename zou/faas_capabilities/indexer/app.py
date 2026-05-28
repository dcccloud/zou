from zou.faas_capabilities.common import register_capability_routes
from zou.faas_capabilities.actions import CAPABILITY_ACTIONS
from zou.faas_capabilities.indexer.executor import execute

app = register_capability_routes(
    "indexer", CAPABILITY_ACTIONS["indexer"], execute_job=execute
)
