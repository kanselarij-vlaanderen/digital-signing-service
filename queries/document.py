from string import Template
from datetime import datetime
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime
from ..config import APPLICATION_GRAPH, KALEIDOS_RESOURCE_BASE_URI, TIMEZONE

DOCUMENT_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/stuk/"

def construct_get_file_for_document(document_uri, file_mimetype=None, graph=APPLICATION_GRAPH):
    if file_mimetype is not None:
        format_filter = "FILTER( CONTAINS( ?format, {} ) )".format(sparql_escape_string(file_mimetype))
    else:
        format_filter = ""
    # Union between both paths to file. We want to be able to select a certain format (pdf)
    # regardless of the fact if it was derived (converted between formats) or not.
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT (?file AS ?uri)
WHERE {
GRAPH $graph {
    $document a dossier:Stuk .
    {
        $document prov:value ?file .
    }
    UNION
    {
        $document prov:value/^prov:hadPrimarySource ?file .
    }
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
PREFIX prov: <http://www.w3.org/ns/prov#>

SELECT (?document AS ?uri)
WHERE {
    GRAPH $graph {
        ?document a dossier:Stuk ;
            prov:value $file .
        $file a nfo:FileDataObject .
    }
}
LIMIT 1
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        file=sparql_escape_uri(file_uri))

def construct_get_document(document_uri):
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT ?name
WHERE {
    $document a dossier:Stuk ;
        dct:title ?name .
}
LIMIT 1
""")
    return query_template.substitute(
        document=sparql_escape_uri(document_uri))

def construct_insert_document(document_name,
                              document_uri,
                              document_uuid,
                              file_uri,
                              graph=APPLICATION_GRAPH):
    creation_date = datetime.now(TIMEZONE)
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX prov: <http://www.w3.org/ns/prov#>

INSERT {
    GRAPH $graph {
        $document a dossier:Stuk ;
            mu:uuid $uuid ;
            dct:title $name ;
            dct:created $created ;
            prov:value $file .
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
        document=sparql_escape_uri(document_uri),
        uuid=sparql_escape_string(document_uuid),
        name=sparql_escape_string(document_name),
        created=sparql_escape_datetime(creation_date),
        file=sparql_escape_uri(file_uri))

def construct_attach_document_to_previous_version(doc_uri, prev_ver_doc_uri, graph=APPLICATION_GRAPH):
    """ Also handles attaching the new version to the previous one's case"""
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX pav: <http://purl.org/pav/>

INSERT {
    GRAPH $graph {
        $doc pav:previousVersion $prev_doc .
        ?case dossier:Dossier.bestaatUit $doc .
    }
}
WHERE {
    GRAPH $graph {
        $doc a dossier:Stuk .
        $prev_doc a dossier:Stuk .
        OPTIONAL {
            ?case a dossier:Dossier ;
                dossier:Dossier.bestaatUit $prev_doc .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        doc=sparql_escape_uri(doc_uri),
        prev_doc=sparql_escape_uri(prev_ver_doc_uri))
