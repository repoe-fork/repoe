import os

# directory that this __init__ file lives in
__REPOE_DIR__, _ = os.path.split(__file__)

# full path to ./data
__DATA_PATH__ = os.path.join(__REPOE_DIR__, "data", "")
# full path to ./poe2
__POE2_DATA_PATH__ = os.path.join(__REPOE_DIR__, "data", "poe2", "")
