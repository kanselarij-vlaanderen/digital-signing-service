__BASE_CLASS_URIS = {
    "sign": "http://mu.semte.ch/vocabularies/ext/handteken/",
    "dossier": "https://data.vlaanderen.be/ns/dossier#"
}

def __type_build_uri(prefix: str, type: str):
    return prefix + type

signflow = __type_build_uri(__BASE_CLASS_URIS["sign"], "Handtekenaangelegenheid")
piece = __type_build_uri(__BASE_CLASS_URIS["dossier"], "Stuk")
