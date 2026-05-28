from zou.faas_capabilities.actions import CAPABILITY_ACTIONS


def test_capability_action_allowlist_contains_split_faas_work():
    assert set(CAPABILITY_ACTIONS) == {
        "indexer",
        "playlist-build",
        "video-processing",
    }
    assert {
        "index_asset",
        "index_person",
        "index_shot",
        "remove_asset",
        "remove_person",
        "remove_shot",
        "reset_index",
    }.issubset(CAPABILITY_ACTIONS["indexer"])
    assert {
        "build_playlist_movie",
        "build_playlist_zip",
    }.issubset(CAPABILITY_ACTIONS["playlist-build"])
    assert {
        "normalize_movie",
        "generate_thumbnail",
        "generate_tile",
    }.issubset(CAPABILITY_ACTIONS["video-processing"])
