import os
from pytz import timezone

# Config
KALEIDOS_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/"
SIGNINGHUB_RESOURCE_BASE_URI = os.environ.get("SIGNINGHUB_API_URL", KALEIDOS_RESOURCE_BASE_URI).strip("/") + "/"
SIGNINGHUB_IFRAME_REDIRECT_URL = os.environ.get("SIGNINGHUB_IFRAME_REDIRECT_URL", "http://kaleidos-test.vlaanderen.be")
TIMEZONE = timezone('Europe/Brussels')

# Constants
APPLICATION_GRAPH = "http://mu.semte.ch/application"
KANSELARIJ_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"
