from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_int,
                            sparql_escape_string, sparql_escape_uri)

from ..config import APPLICATION_GRAPH


def construct_insert_file_query(file, physical_file, graph=APPLICATION_GRAPH):
    """
    Construct a SPARQL query for inserting a file.
    :param file: dict containing properties for file
    :param share_uri: 
    :returns: string containing SPARQL query
    """
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX nie: <http://www.semanticdesktop.org/ontologies/2007/01/19/nie#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dbpedia: <http://dbpedia.org/ontology/>

INSERT DATA {
    GRAPH $graph {
        $uri a nfo:FileDataObject ;
            mu:uuid $uuid ;
            nfo:fileName $name ;
            dct:format $mimetype ;
            dct:created $created ;
            nfo:fileSize $size ;
            dbpedia:fileExtension $extension .
        $physical_uri a nfo:FileDataObject ;
            mu:uuid $physical_uuid ;
            nfo:fileName $physical_name ;
            dct:format $mimetype ;
            dct:created $created ;
            nfo:fileSize $size ;
            dbpedia:fileExtension $extension ;
            nie:dataSource $uri .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        uri=sparql_escape_uri(file["uri"]),
        uuid=sparql_escape_string(file["uuid"]),
        name=sparql_escape_string(file["name"]),
        mimetype=sparql_escape_string(file["mimetype"]),
        created=sparql_escape_datetime(file["created"]),
        size=sparql_escape_int(file["size"]),
        extension=sparql_escape_string(file["extension"]),
        physical_uri=sparql_escape_uri(physical_file["uri"]),
        physical_uuid=sparql_escape_string(physical_file["uuid"]),
        physical_name=sparql_escape_string(physical_file["name"]))


def construct_get_file_query(file_uri, graph=APPLICATION_GRAPH):
    """
    Construct a SPARQL query for querying a file.
    :param file_uri: string containing file uri
    :returns: string containing SPARQL query
    """
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX nie: <http://www.semanticdesktop.org/ontologies/2007/01/19/nie#>
PREFIX dbpedia: <http://dbpedia.org/ontology/>

SELECT (?file_uri AS ?uri) ?uuid ?name ?size ?extension ?physicalFile
WHERE {
    GRAPH $graph {
        $file_uri a nfo:FileDataObject ;
            mu:uuid ?uuid ;
            nfo:fileName ?name ;
            nfo:fileSize ?size ;
            dbpedia:fileExtension ?extension ;
            ^nie:dataSource ?physicalFile .
        BIND($file_uri AS ?file_uri)
        ?physicalFile a nfo:FileDataObject .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        file_uri=sparql_escape_uri(file_uri))

def construct_get_file_by_id(file_id, graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>

SELECT (?file AS ?uri)
WHERE {
    GRAPH $graph {
        ?file a nfo:FileDataObject ;
            mu:uuid $uuid .
    }
}
LIMIT 1
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        uuid=sparql_escape_string(file_id))
