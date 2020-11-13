from string import Template
from datetime import datetime
from pytz import timezone
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime

TIMEZONE = timezone('Europe/Brussels')
APPLICATION_GRAPH = "http://mu.semte.ch/application"

SIGNING_PREP_ACT_TYPE_URI = "http://example.com/concept/123"

SIGNING_ACT_TYPE_URI = "http://example.com/concept/123"

def construct_insert_signing_prep_activity(activity,
                                           signing_subcase_uri,
                                           document_uri,
                                           sh_package_id,
                                           sh_document_id,
                                           graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        $signing_prep a prov:Activity ;
            mu:uuid $uuid ;
            dct:type $type ;
            sh:packageId $sh_package_id ;
            sh:documentId $sh_document_id .
        $signing_prep dossier:vindtPlaatsTijdens $signing_subcase .
        $signing_prep prov:used $document .
    }
}
WHERE {
    GRAPH $graph {
        $signing_subcase a dossier:Procedurestap .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signing_prep=sparql_escape_uri(activity["uri"]),
        signing_subcase=sparql_escape_uri(signing_subcase_uri),
        uuid=sparql_escape_string(activity["uuid"]),
        type=sparql_escape_uri(SIGNING_PREP_ACT_TYPE_URI),
        sh_package_id=sparql_escape_string(sh_package_id),
        sh_document_id=sparql_escape_string(sh_document_id),
        document=sparql_escape_uri(document_uri))

def construct_get_signing_prep_from_subcase_doc(signing_subcase_uri,
                                                document_uri,
                                                graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT (?signing_prep AS ?uri) ?sh_package_id ?sh_document_id ?signing
WHERE {
    GRAPH $graph {
        ?signing_prep a prov:Activity ;
            dct:type $prep_type ;
            sh:packageId ?sh_package_id ;
            sh:documentId ?sh_document_id .
        ?signing_prep dossier:vindtPlaatsTijdens $signing_subcase .
        ?signing_prep prov:used $document .
        OPTIONAL {
            ?signing a prov:Activity ;
                dct:type $sign_type ;
                dossier:vindtPlaatsTijdens $signing_subcase ;
                prov:wasInformedBy ?signing_prep .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signing_subcase=sparql_escape_uri(signing_subcase_uri),
        prep_type=sparql_escape_uri(SIGNING_PREP_ACT_TYPE_URI),
        sign_type=sparql_escape_uri(SIGNING_ACT_TYPE_URI),
        document=sparql_escape_uri(document_uri))

def construct_insert_signing_activity(activity,
                                      signing_prep_uri,
                                      mandatee_uri,
                                      graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>

INSERT {
    GRAPH $graph {
        $signing a prov:Activity ;
            mu:uuid $uuid ;
            dct:type $type ;
            prov:wasInformedBy $signing_prep ;
            prov:qualifiedAssociation $mandatee .
        $signing dossier:vindtPlaatsTijdens ?signing_subcase .
    }
}
WHERE {
    GRAPH $graph {
        $signing_prep a prov:Activity ;
            dct:type $prep_type ;
            dossier:vindtPlaatsTijdens ?signing_subcase .
        $mandatee a mandaat:Mandataris .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signing=sparql_escape_uri(activity["uri"]),
        uuid=sparql_escape_string(activity["uuid"]),
        type=sparql_escape_string(SIGNING_ACT_TYPE_URI),
        signing_prep=sparql_escape_uri(signing_prep_uri),
        mandatee=sparql_escape_uri(mandatee_uri))
