from .. import config as _config

THEMIS_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/"

class __Resource:
    def __build (self, type: str, id: str):
        return THEMIS_RESOURCE_BASE_URI + type + "/" + id

    def piece(self, id: str):
        return self.__build("stuk", id)

    def signflow(self, id: str):
        return self.__build("handtekenaangelegenheid", id)

    def preparation_activity(self, id: str):
        return self.__build("handteken-voorbereidingsactiviteit", id)

    def signinghub_document(self, package_id: str, document_id: str):
        return f"{_config.SIGNINGHUB_RESOURCE_BASE_URI}package/{package_id}/document/{document_id}"

resource = __Resource()
