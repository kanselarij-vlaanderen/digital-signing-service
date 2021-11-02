from .. import config as _config


class __Graph:
    application = 'http://mu.semte.ch/application'
    kanselarij = "http://mu.semte.ch/graphs/organizations/kanselarij"

graph = __Graph()


class __Type(object):
    __TYPE_PREFIX_MAP = {
        "sign": "http://mu.semte.ch/vocabularies/ext/handteken/",
        "dossier": "https://data.vlaanderen.be/ns/dossier#"
    }
    def __type_build(self, prefix: str, type: str):        
        return self.__TYPE_PREFIX_MAP[prefix] + type

    @property
    def signflow(self):
        return self.__type_build("sign", "Handtekenaangelegenheid")

    @property
    def piece(self):
        return self.__type_build("dossier", "Stuk")

type = __Type()



class __Resource:
    __RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/"

    def __build (self, type: str, id: str):
        return self.__RESOURCE_BASE_URI + type + "/" + id

    def piece(self, id: str):
        return self.__build("stuk", id)

    def signflow(self, id: str):
        return self.__build("handtekenaangelegenheid", id)

    def preparation_activity(self, id: str):
        return self.__build("handteken-voorbereidingsactiviteit", id)

    def signing_activity(self, id: str):
        return self.__build("handteken-handtekenactiviteit", id)

    def signinghub_document(self, package_id: str, document_id: str):
        return f"{_config.SIGNINGHUB_BASE_URI}package/{package_id}/document/{document_id}"

resource = __Resource()