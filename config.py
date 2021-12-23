import os

KALEIDOS_RESOURCE_BASE_URI = "http://kanselarij.vo.data.gift/"
SIGNINGHUB_RESOURCE_BASE_URI = os.environ.get("SIGNINGHUB_API_URL", KALEIDOS_RESOURCE_BASE_URI).strip("/") + "/"

APPLICATION_GRAPH = "http://mu.semte.ch/application"
KANSELARIJ_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"
