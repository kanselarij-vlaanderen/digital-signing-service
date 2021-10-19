__PREFIX_MAP = {
    "sign": "http://mu.semte.ch/vocabularies/ext/handteken/",
    "dossier": "https://data.vlaanderen.be/ns/dossier#"
}

def __build(prefix: str, type: str):
    return __PREFIX_MAP[prefix] + type

signflow = __build("sign", "Handtekenaangelegenheid")
piece = __build("dossier", "Stuk")
