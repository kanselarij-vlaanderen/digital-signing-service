from .... import config

__BASE_RESOURCE_URI = "http://themis.vlaanderen.be/id/"

def __resource_build_uri(type: str, id: str):
    return __BASE_RESOURCE_URI + type + "/" + id

def signflow(id: str):
    return __resource_build_uri("handtekenaangelegenheid", id)

def preparation_activity(id: str):
    return __resource_build_uri("handteken-voorbereidingsactiviteit", id)

def signing_activity(id: str):
    return __resource_build_uri("handteken-handtekenactiviteit", id)

def signinghub_document(package_id: str, document_id: str):
    return f"{config.SIGNINGHUB_BASE_URI}package/{package_id}/document/{document_id}"
