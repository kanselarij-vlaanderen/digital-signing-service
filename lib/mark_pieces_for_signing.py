from datetime import datetime
from string import Template
from typing import List
from helpers import query, logger, generate_uuid, update
from escape_helpers import (
    sparql_escape_date,
    sparql_escape_datetime, 
    sparql_escape_string, 
    sparql_escape_uri, 
)
from lib.query_result_helpers import to_recs
from ..config import (
    APPLICATION_GRAPH,
    HANDTEKEN_PROCEDURESTAP_RESOURCE_BASE_URI, 
    HANDTEKENACTIVITEIT_RESOURCE_BASE_URI, 
    MARKED_STATUS,
    SIGN_MARKING_ACTIVITY_RESOURCE_BASE_URI,
    TIMEZONE,
)


def mark_piece_for_signing(piece_id):
    signflow_id = generate_uuid()
    signflow_uri = f"{HANDTEKENACTIVITEIT_RESOURCE_BASE_URI}{signflow_id}"
    subcase_id = generate_uuid()
    subcase_uri = f"{HANDTEKEN_PROCEDURESTAP_RESOURCE_BASE_URI}{subcase_id}"
    marking_activity_id = generate_uuid()
    marking_activity_uri = f"{SIGN_MARKING_ACTIVITY_RESOURCE_BASE_URI}{marking_activity_id}"
    now = datetime.now(TIMEZONE)

    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX besluitvorming: <https://data.vlaanderen.be/ns/besluitvorming#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

INSERT {
    GRAPH $graph {
        ?markingActivity a sign:Markeringsactiviteit .
        ?markingActivity mu:uuid ?markingActivityId .
        ?markingActivity dossier:Activiteit.startdatum ?nowDatetime .
        ?markingActivity dossier:Activiteit.einddatum ?nowDatetime .
        ?markingActivity sign:markeringVindtPlaatsTijdens ?signSubcase .
        ?markingActivity sign:gemarkeerdStuk ?piece .

        ?signSubcase a sign:HandtekenProcedurestap .
        ?signSubcase mu:uuid ?signSubcaseId .
        ?signSubcase dossier:Procedurestap.startdatum ?nowDatetime .
        
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow mu:uuid ?signflowId .
        ?signflow dct:alternative ?caseShortTitle .
        ?signflow dct:title ?caseTitle .
        ?signflow dossier:openingsdatum ?nowDate .
        ?signflow adms:status ?markedStatus .
        ?signflow sign:behandeltDossier ?case .
        ?signflow sign:doorlooptHandtekening ?signSubcase .
        ?signflow sign:heeftBeslissing ?decisionActivity .
        ?signflow sign:heeftVergadering ?meeting .
    }
} WHERE {
    VALUES ?pieceId { $piece_id }
    VALUES ?markingActivity { $marking_activity }
    VALUES ?markingActivityId { $marking_activity_id }
    VALUES ?signSubcase { $sign_subcase }
    VALUES ?signSubcaseId { $sign_subcase_id }
    VALUES ?signflow { $signflow }
    VALUES ?signflowId { $signflow_id }
    VALUES ?nowDatetime { $now_datetime }
    VALUES ?nowDate { $now_date }
    VALUES ?markedStatus { $marked_status }

    ?piece mu:uuid ?pieceId .
    OPTIONAL { 
        ?piece besluitvorming:beschrijft ?decisionActivity . 
        OPTIONAL {
            ?treatment besluitvorming:heeftBeslissing ?decisionActivity .
            ?treatment dct:subject ?agendaitem .
            ?agenda dct:hasPart ?agendaitem .
            ?agenda besluitvorming:isAgendaVoor ?meeting .
        }
        OPTIONAL {
            ?decisionActivity ext:beslissingVindtPlaatsTijdens ?subcase .
            ?decisionmakingFlow dossier:doorloopt ?subcase .
            ?case dossier:Dossier.isNeerslagVan ?decisionmakingFlow . 
            OPTIONAL { ?case dct:title ?caseTitle . }
            OPTIONAL { ?case dct:alternative ?caseShortTitle . }
        }
    }
}
    """)
    query_string = query_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),  # question: is this the right graph?
        piece_id=sparql_escape_string(piece_id),
        signflow=sparql_escape_uri(signflow_uri),
        signflow_id=sparql_escape_string(signflow_id),
        sign_subcase=sparql_escape_uri(subcase_uri),
        sign_subcase_id=sparql_escape_string(subcase_id),
        marking_activity=sparql_escape_uri(marking_activity_uri),
        marking_activity_id=sparql_escape_string(marking_activity_id),
        now_date=sparql_escape_date(now),
        now_datetime=sparql_escape_datetime(now),
        marked_status=sparql_escape_uri(MARKED_STATUS),
    )
    update(query_string)


def mark_pieces_for_signing(piece_ids):
    signflows = get_signflows(piece_ids)
    for signflow in signflows:
        if signflow['signflow'] is None:
            mark_piece_for_signing(signflow['pieceId'])


def get_signflows(piece_ids: List[str]):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT ?pieceId ?markingActivity ?signSubcase ?flow
WHERE {
    VALUES ?pieceId {
        $piece_ids
    }
    ?piece mu:uuid ?pieceId .
    OPTIONAL { 
        ?markingActivity sign:gemarkeerdStuk ?piece . 
        ?markingActivity sign:markeringVindtPlaatsTijdens ?signSubcase . 
        ?flow sign:doorlooptHandtekening ?signSubcase . 
    }
}
    """)
    query_string = query_template.substitute(
        piece_ids=" ".join(map(sparql_escape_string, piece_ids))
    )
    

    return to_recs(query(query_string))