from config import APPLICATION_GRAPH, JOB
from escape_helpers import (
    sparql_escape_string,
    sparql_escape_uri,
    sparql_escape_datetime,
)
from helpers import generate_uuid, logger, update, query

from datetime import datetime
from string import Template

from ..authentication import get_or_create_signinghub_session
from ..agent_query import query as agent_query, update as agent_update

from .session import get_mu_session
from .file import delete_physical_file
from .prepare_signing_flow import prepare_signing_flow
from .query_result_helpers import to_recs

from ..queries.signing_flow import (
    construct_get_signing_flows_by_uris,
    get_physical_files_of_sign_flows,
    reset_signflows,
)
from ..queries.file import delete_physical_file_metadata


def create_job(sign_flow_uris, mu_session_uri):
    uuid = generate_uuid()
    uri = f"{JOB["RESOURCE_BASE_URI"]}{uuid}"
    now = datetime.now()
    logger.debug(
        f"Creating job with uri {sparql_escape_uri(uri)} for {len(sign_flow_uris)} sign flows"
    )

    query_string = Template(
        """PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX adms: <http://www.w3.org/ns/adms#>

INSERT DATA {
    GRAPH $graph {
        $uri a $rdf_type ;
            mu:uuid $uuid ;
            prov:used $sign_flow_uris ;
            adms:status $status ;
            dct:creator $mu_session_uri ;
            dct:created $created .
    }
}"""
    ).substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        uri=sparql_escape_uri(uri),
        rdf_type=sparql_escape_uri(JOB["RDF_TYPE"]),
        uuid=sparql_escape_string(uuid),
        sign_flow_uris=", ".join(map(sparql_escape_uri, sign_flow_uris)),
        status=sparql_escape_uri(JOB["STATUSES"]["SCHEDULED"]),
        mu_session_uri=sparql_escape_uri(mu_session_uri),
        created=sparql_escape_datetime(now),
    )
    update(query_string)

    return {
        "id": uuid,
        "uri": uri,
        "sign_flow_uris": sign_flow_uris,
        "mu_session_uri": mu_session_uri,
        "created": now,
        "modified": now,
        "status": JOB["STATUSES"]["SCHEDULED"],
    }

def get_job(uuid):
    query_string = Template(
        """PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <http://schema.org/>

SELECT ?uri ?status ?sign_flow_uris ?mu_session_uri ?created ?time_started ?time_ended ?error_message
WHERE {
  GRAPH $graph {
    ?uri a $rdf_type ;
      mu:uuid $uuid ;
      prov:used ?sign_flow_uris ;
      dct:creator ?mu_session_uri ;
      dct:created ?created ;
      adms:status ?status .
    OPTIONAL { ?uri prov:startedAtTime ?time_started }
    OPTIONAL { ?uri prov:endedAtTime ?time_ended }
    OPTIONAL { ?uri schema:error ?error_message }
  }
} ORDER BY ASC(?created) LIMIT 1"""
    ).substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        uuid=sparql_escape_string(uuid),
        rdf_type=sparql_escape_uri(JOB["RDF_TYPE"]),
    )

    result = query(query_string)
    records = to_recs(result)
    if len(records):
        record = records[0]
        return {
            "id": uuid,
            "uri": record["uri"],
            "sign_flow_uris": record["sign_flow_uris"],
            "mu_session_uri": record["mu_session_uri"],
            "created": record["created"],
            "time_started": record["time_started"],
            "time_ended": record["time_ended"],
            "status": record["status"],
            "error_message": record["error_message"],
        }
    return None


def update_job_status(job_uri, status_uri):
    now = datetime.now()
    if  status_uri == JOB["STATUSES"]["SUCCESS"] or status_uri == JOB["STATUSES"]["FAILED"]: # final statusses
        time_predicate = 'http://www.w3.org/ns/prov#endedAtTime'
    else:
        time_predicate = 'http://www.w3.org/ns/prov#startedAtTime'
    
    query_string = Template(
        """PREFIX adms: <http://www.w3.org/ns/adms#>

DELETE WHERE {
  $job_uri adms:status ?status_uri .
  OPTIONAL { $job_uri $time_predicate ?now . }
}
;

;
INSERT DATA {
  $job_uri adms:status $status_uri ;
           $time_predicate $now .
}"""
    ).substitute(
        job_uri=sparql_escape_uri(job_uri),
        status_uri=sparql_escape_uri(status_uri),
        now=sparql_escape_datetime(now),
        time_predicate=sparql_escape_uri(time_predicate)
    )
    agent_update(query_string)


def update_job_error_message(job_uri, error_message):
    query_string = Template(
        """PREFIX schema: <http://schema.org/>

DELETE WHERE {
  $job_uri schema:error ?errorMessage.
}
;
INSERT DATA {
  $job_uri schema:error $error_message.
}"""
    ).substitute(
        job_uri=sparql_escape_uri(job_uri),
        error_message=sparql_escape_string(error_message),
    )
    agent_update(query_string)


def execute_job(job):
    try:
        mu_session_uri = job["mu_session_uri"]
        mu_session = get_mu_session(mu_session_uri)
        email = mu_session["email"]["value"]

        logger.info(f"Starting execution of job <{job['uri']}> started by user {email}")

        update_job_status(job["uri"], JOB["STATUSES"]["BUSY"])
        execute_prepare_sign_flow_job(job)
        update_job_status(job["uri"], JOB["STATUSES"]["SUCCESS"])

        logger.info(f"Successfully finished job <{job['uri']}>")
    except Exception as e:
        logger.exception(f"Failed to execute job <{job['uri']}>: {e}")

        update_job_status(job["uri"], JOB["STATUSES"]["FAILED"])
        error_message = str(e)
        update_job_error_message(
            job["uri"],
            str(
                {
                    "errors": [
                        {
                            "detail": error_message,
                            "status": 500,
                        }
                    ]
                }
            ),
        )


def execute_prepare_sign_flow_job(job):
    mu_session_uri = job["mu_session_uri"]
    sign_flow_uris = job["sign_flow_uris"]
    query_string = construct_get_signing_flows_by_uris(sign_flow_uris)
    sign_flows = to_recs(agent_query(query_string))

    # Remove decision_report when it's equal to piece
    for sign_flow in sign_flows:
        if sign_flow["piece"] == sign_flow["decision_report"]:
            sign_flow["decision_report"] = None

    try:
        sh_session = get_or_create_signinghub_session(mu_session_uri)
        prepare_signing_flow(
            sh_session,
            sign_flows,
            query_method=agent_query,
            update_method=agent_update,
        )
    except Exception as exception:
        physical_files = to_recs(
            agent_query(get_physical_files_of_sign_flows(sign_flow_uris))
        )
        for physical_file in physical_files:
            delete_physical_file(physical_file["uri"])
            agent_update(delete_physical_file_metadata(physical_file["uri"]))
        agent_update(reset_signflows(sign_flow_uris))
        raise exception
