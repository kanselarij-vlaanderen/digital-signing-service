from string import Template
from datetime import datetime
from pytz import timezone
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime

TIMEZONE = timezone('Europe/Brussels')
APPLICATION_GRAPH = "http://mu.semte.ch/application"

DOCUMENT_BASE_URI = "http://kanselarij.vo.data.gift/id/stukken/"

def construct_get_file_for_document(document_uri, file_mimetype=None, graph=APPLICATION_GRAPH):
    if file_mimetype is not None:
        format_filter = "FILTER( CONTAINS( ?format, {} ) )".format(sparql_escape_string(file_mimetype))
    else:
        format_filter = ""
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

SELECT (?file AS ?uri)
WHERE {
    GRAPH $graph {
        $document a dossier:Stuk ;
            ext:file ?file .
        ?file a nfo:FileDataObject ;
            nfo:fileName ?name ;
            dct:format ?format .
        $format_filter
    }
}
LIMIT 1
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        document=sparql_escape_uri(document_uri),
        format_filter=format_filter)

def construct_get_document_for_file(file_uri, graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

SELECT (?document AS ?uri)
WHERE {
    GRAPH $graph {
        ?document a dossier:Stuk ;
            ext:file $file .
        $file a nfo:FileDataObject .
    }
}
LIMIT 1
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        file=sparql_escape_uri(file_uri))

def construct_insert_document(document_name, file_uri, graph=APPLICATION_GRAPH):
    document = {
        "name": document_name,
        "created": datetime.now(TIMEZONE)
    }
    document["uuid"] = generate_uuid()
    document["uri"] = DOCUMENT_BASE_URI + document["uuid"]
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

INSERT {
    GRAPH $graph {
        $document a dossier:Stuk ;
            mu:uuid $uuid ;
            dct:title $name ;
            dct:created $created ;
            ext:file $file .
    }
}
WHERE {
    GRAPH $graph {
        $file a nfo:FileDataObject .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        document=sparql_escape_uri(document["uri"]),
        uuid=sparql_escape_string(document["uuid"]),
        name=sparql_escape_string(document["name"]),
        created=sparql_escape_datetime(document["created"]),
        file=sparql_escape_uri(file_uri))
