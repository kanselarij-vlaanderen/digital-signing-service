import os

__KANSELARIJ_URL = "http://kanselarij.vo.data.gift/"
SIGNINGHUB_RESOURCE_BASE_URI = os.environ.get("SIGNINGHUB_API_URL", __KANSELARIJ_URL).strip("/") + "/"

APPLICATION_GRAPH = "http://mu.semte.ch/application"
KANSELARIJ_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"
