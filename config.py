import os

__KANSELARIJ_URL = "http://kanselarij.vo.data.gift/"
SIGNINGHUB_BASE_URI = os.environ.get(
    "SIGNINGHUB_API_URL", __KANSELARIJ_URL).strip("/") + "/"


MODE = os.environ.get("MODE")
