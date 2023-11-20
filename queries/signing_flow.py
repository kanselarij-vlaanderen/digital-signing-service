from datetime import datetime
from string import Template
from typing import List

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)
from helpers import generate_uuid

from ..config import ANNULATIEACTIVITEIT_RESOURCE_BASE_URI


def construct_get_signing_flow_by_uri(signflow_uri: str):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT DISTINCT (?signflow_id AS ?id) ?sh_package_id ?sh_document_id
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        mu:uuid ?signflow_id .
    OPTIONAL {
        $signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit ;
            sign:voorbereidingGenereert ?sh_document .
        ?sh_document a sh:Document ;
            sh:packageId ?sh_package_id ;
            sh:documentId ?sh_document_id .
    }
}
""")
    return query_template.substitute(
      signflow=sparql_escape_uri(signflow_uri)
    )

def construct_get_signing_flow_notifiers(signflow_uri: str):
    query_template = Template("""
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT DISTINCT ?notified
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?sign_subcase a sign:HandtekenProcedurestap ;
        sign:genotificeerde ?notified .
}
""")
    return query_template.substitute(
      signflow=sparql_escape_uri(signflow_uri)
    )

def construct_get_signing_flow_creator(signflow_uri: str):
    query_template = Template("""
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT ?creator ?email
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        dct:creator ?creator .
    ?creator foaf:mbox ?email_uri .
    BIND(REPLACE(STR(?email_uri), "^mailto:", "") AS ?email)
}
""")
    return query_template.substitute(
      signflow=sparql_escape_uri(signflow_uri)
    )

def construct_get_ongoing_signing_flows() -> str:
    return """
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT DISTINCT ?sign_flow_id
WHERE {
    ?sign_flow a sign:Handtekenaangelegenheid ;
        mu:uuid ?sign_flow_id ;
        sign:doorlooptHandtekening ?signing_subcase .
    ?signing_subcase ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
    FILTER NOT EXISTS {
        ?wrap_up_activity
            a sign:Afrondingsactiviteit ;
                sign:afrondingVindtPlaatsTijdens ?signing_subcase ;
                prov:wasInformedBy ?signing_activity .
    }
    FILTER NOT EXISTS {
        ?refusal_activity a sign:Weigeractiviteit ;
            sign:weigeringVindtPlaatsTijdens ?signing_subcase .
    }
    FILTER NOT EXISTS {
        ?cancellation_activity a sign:AnnulatieActiviteit ;
            sign:annulatieVindtPlaatsTijdens ?signing_subcase .
    }
}
"""

def construct_insert_cancellation_activity(sign_flow: str, date = None) -> str:
    if date is None:
        date = datetime.now()

    uuid = generate_uuid()
    uri = ANNULATIEACTIVITEIT_RESOURCE_BASE_URI + uuid

    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX prov: <http://www.w3.org/ns/prov#>

INSERT {
    $cancellation_activity
        a sign:AnnulatieActiviteit ;
        mu:uuid $cancellation_activity_id ;
        dossier:Activiteit.startdatum $date ;
        dossier:Activiteit.einddatum $date ;
        sign:annulatieVindtPlaatsTijdens ?signing_subcase .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?signing_subcase .
}
""")
    return query_template.substitute(
        signflow=sparql_escape_uri(sign_flow),
        cancellation_activity=sparql_escape_uri(uri),
        cancellation_activity_id=sparql_escape_string(uuid),
        date=sparql_escape_datetime(date),
    )


def construct_get_signing_flows_by_uuids(ids: List[str]) -> str:
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT DISTINCT ?id ?sign_flow
    ?piece ?piece_name ?piece_created
    ?decision_activity ?decision_report
    ?meeting
WHERE {
    VALUES ?id { $ids }
    ?sign_flow a sign:Handtekenaangelegenheid ;
        mu:uuid ?id ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?sign_subcase a sign:HandtekenProcedurestap .
    ?marking_activity a sign:Markeringsactiviteit ;
        sign:markeringVindtPlaatsTijdens ?sign_subcase ;
        sign:gemarkeerdStuk ?piece .
    ?piece dct:title ?piece_name ;
           dct:created ?piece_created .

    OPTIONAL {
        ?sign_flow sign:heeftBeslissing ?decision_activity .
        ?decision_activity a besluitvorming:Beslissingsactiviteit .
        OPTIONAL {
            ?decision_report a dossier:Stuk ;
                besluitvorming:beschrijft ?decision_activity .
        }
    }
    OPTIONAL { ?sign_flow sign:heeftVergadering ?meeting . }
}
""")
    return query_template.substitute(
        ids=" ".join(list(map(sparql_escape_string, ids))),
    )


def reset_signflows(signflow_ids):
    query_template = Template("""
    PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
    PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
    PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
    PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX adms: <http://www.w3.org/ns/adms#>
    
    DELETE {
        ?sign_flow adms:status ?status .
        ?sign_flow dct:creator ?creator .
        ?s ?p ?o .
    } INSERT {
        ?sign_flow adms:status <http://themis.vlaanderen.be/id/handtekenstatus/f6a60072-0537-11ee-bb35-ee395168dcf7> .
    } WHERE {
        VALUES ?id { $signflow_ids }

        ?sign_flow a sign:Handtekenaangelegenheid ;
            mu:uuid ?id ;
            adms:status ?status ;
            dct:creator ?creator ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?marking_activity 
            sign:markeringVindtPlaatsTijdens ?sign_subcase ;
            sign:gemarkeerdStuk ?piece .
        {
            ?piece sign:getekendStukKopie ?s .
            ?s ?p ?o .
        } UNION {
            ?piece sign:getekendStukKopie ?signed_piece_copy .
            ?signed_piece_copy prov:value ?s .
            ?s ?p ?o .
        } UNION {
            ?s sign:ongetekendStuk ?piece ; ?p ?o .
        } UNION {
            ?signed_piece sign:ongetekendStuk ?piece ; prov:value ?s .
            ?s ?p ?o .
        } UNION {
            ?s sign:voorbereidingVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?s sign:handtekeningVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?s sign:goedkeuringVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?s sign:weigeringVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?s sign:annulatieVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?s sign:afrondingVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        }
    }
    """)
    return query_template.substitute(
        signflow_ids=" ".join(
            list(map(sparql_escape_string, signflow_ids))
        ),
    )


def remove_signflows(signflow_ids):
    query_template = Template("""
    PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
    PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
    PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
    PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX prov: <http://www.w3.org/ns/prov#>

    DELETE { ?s ?p ?o }
    WHERE {
        VALUES ?id { $signflow_ids }
        {
            ?s a sign:Handtekenaangelegenheid ; mu:uuid ?id ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?s .
            ?s ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:markeringVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase ; sign:gemarkeerdStuk ?piece .
            ?piece sign:getekendStukKopie ?s .
            ?s ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase ; sign:gemarkeerdStuk ?piece .
            ?piece sign:getekendStukKopie ?signed_piece_copy .
            ?signed_piece_copy prov:value ?s .
            ?s ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase ; sign:gemarkeerdStuk ?piece .
            ?s sign:ongetekendStuk ?piece ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase ; sign:gemarkeerdStuk ?piece .
            ?signed_piece sign:ongetekendStuk ?piece ; prov:value ?s .
            ?s ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:voorbereidingVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:handtekeningVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:goedkeuringVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:weigeringVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:annulatieVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        } UNION {
            ?sign_flow a sign:Handtekenaangelegenheid ; mu:uuid ?id ; sign:doorlooptHandtekening ?sign_subcase .
            ?s sign:afrondingVindtPlaatsTijdens ?sign_subcase ; ?p ?o .
        }
    }
    """)
    return query_template.substitute(
        signflow_ids=" ".join(
            list(map(sparql_escape_string, signflow_ids))
        ),
    )
