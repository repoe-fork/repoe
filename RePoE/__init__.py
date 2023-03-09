import os

# directory that this __init__ file lives in
__REPOE_DIR__, _ = os.path.split(__file__)

# full path to ./data
__DATA_PATH__ = os.path.join(__REPOE_DIR__, "data", "")


def _get_all_json_files(base_path=__DATA_PATH__):
    """get all json files in /data"""
    json_files = [
        pos_json
        for pos_json in os.listdir(base_path)
        if pos_json.endswith(".json") and not pos_json.endswith(".min.json")
    ]
    return json_files


def _assert_all_json_files_accounted_for(base_path=__DATA_PATH__, globals=globals()):
    json_files = _get_all_json_files(base_path=base_path)
    for json_file in json_files:
        json_file_stripped, _, _ = json_file.partition(".json")

        assert json_file_stripped in globals, f"the following json file needs to be added to load: {json_file_stripped}"
