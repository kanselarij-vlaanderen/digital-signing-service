import os

__MU_APPLICATION_GRAPH = "http://mu.semte.ch/application"
DATABASE_GRAPH = os.environ.get("DATABASE_GRAPH", __MU_APPLICATION_GRAPH)

__KANSELARIJ_URL = "http://kanselarij.vo.data.gift/"
SIGNINGHUB_BASE_URI = os.environ.get("SIGNINGHUB_API_URL", __KANSELARIJ_URL).strip("/") + "/"
