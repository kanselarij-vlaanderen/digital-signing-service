from datetime import datetime

from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)

from ..config import (ACCESS_LEVEL_CABINET, ACCESS_LEVEL_GOVERNMENT,
                      ACCESS_LEVEL_PUBLIC, APPLICATION_GRAPH,
                      TIMEZONE)

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

def construct_attach_document_to_unsigned_version(doc_uri, prev_ver_doc_uri, graph=APPLICATION_GRAPH):
    """Also handles attaching the signed version to the previous one's case
    The relation ?case dossier:Dossier.bestaatUit $doc is what lets
    Yggdrasil propagate the signed pieces.
    """
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX pav: <http://purl.org/pav/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>

DELETE {
    GRAPH $graph {
        $doc dct:title ?old_title .
    }
}
INSERT {
    GRAPH $graph {
        $doc sign:ongetekendStuk $prev_doc .
        $doc dct:title ?signed_title .
        ?case dossier:Dossier.bestaatUit $doc .
        $doc besluitvorming:vertrouwelijkheidsniveau ?access_level .
    }
}
WHERE {
    GRAPH $graph {
        $doc a dossier:Stuk .
        $prev_doc a dossier:Stuk ;
            dct:title ?prev_title ;
            besluitvorming:vertrouwelijkheidsniveau ?prev_access_level .
        BIND(CONCAT(?prev_title, " (met certificaat)") AS ?signed_title)
        OPTIONAL {
            $doc dct:title ?old_title .
        }
        OPTIONAL {
            ?case a dossier:Dossier ;
                dossier:Dossier.bestaatUit $prev_doc .
        }
        BIND(
            IF(?prev_access_level IN ($access_level_public, $access_level_government),
            $access_level_cabinet,
            ?prev_access_level)
        AS ?access_level)
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        doc=sparql_escape_uri(doc_uri),
        prev_doc=sparql_escape_uri(prev_ver_doc_uri),
        access_level_cabinet=sparql_escape_uri(ACCESS_LEVEL_CABINET),
        access_level_government=sparql_escape_uri(ACCESS_LEVEL_GOVERNMENT),
        access_level_public=sparql_escape_uri(ACCESS_LEVEL_PUBLIC),
    )
