import os
from pytz import timezone

# Config
KALEIDOS_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/"
SIGNINGHUB_RESOURCE_BASE_URI = os.environ.get("SIGNINGHUB_API_URL", KALEIDOS_RESOURCE_BASE_URI).strip("/") + "/"
SIGNINGHUB_IFRAME_REDIRECT_URL = os.environ.get("SIGNINGHUB_IFRAME_REDIRECT_URL", "http://kaleidos-test.vlaanderen.be")
TIMEZONE = timezone('Europe/Brussels')
SYNC_CRON_PATTERN = os.environ.get("SYNC_CRON_PATTERN", "*/2 * * * *")
SIGNINGHUB_APP_DOMAIN = os.environ.get("SIGNINGHUB_APP_DOMAIN")

# Constants
APPLICATION_GRAPH = "http://mu.semte.ch/application"
KANSELARIJ_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"
ACCESS_LEVEL_CABINET = "http://themis.vlaanderen.be/id/concept/toegangsniveau/13ae94b0-6188-49df-8ecd-4c4a17511d6d"
ACCESS_LEVEL_GOVERNMENT = "http://themis.vlaanderen.be/id/concept/toegangsniveau/634f438e-0d62-4ae4-923a-b63460f6bc46"
ACCESS_LEVEL_PUBLIC = "http://themis.vlaanderen.be/id/concept/toegangsniveau/c3de9c70-391e-4031-a85e-4b03433d6266"
GOEDKEURINGSACTIVITEIT_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/handteken-goedkeuringsactiviteit/"
WEIGERACTIVITEIT_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/handteken-weigeractiviteit/"
ANNULATIEACTIVITEIT_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/handteken-annulatie-activiteit/"
