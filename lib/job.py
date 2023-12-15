from config import APPLICATION_GRAPH, JOB, JOB_RESOURCE_BASE_URI
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
from .file import delete_physical_file
from .prepare_signing_flow import prepare_signing_flow
from .query_result_helpers import to_recs
from ..queries.signing_flow import (
    construct_get_signing_flows_by_uris,
    get_physical_files_of_sign_flows,
    reset_signflows,
)


def create_job(sign_flow_uris, mu_session_uri):
    uuid = generate_uuid()
    uri = f"{JOB_RESOURCE_BASE_URI}{uuid}"
    now = datetime.now()
    logger.info(
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
        $uri a ext:PrepareSignFlowJob ;
            mu:uuid $uuid ;
            prov:used $sign_flow_uris ;
            adms:status $status ;
            dct:creator $mu_session_uri ;
            dct:created $created ;
            dct:modified $modified .
    }
}"""
    ).substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        uri=sparql_escape_uri(uri),
        uuid=sparql_escape_string(uuid),
        sign_flow_uris=", ".join(map(sparql_escape_uri, sign_flow_uris)),
        status=sparql_escape_uri(JOB["STATUSES"]["SCHEDULED"]),
        mu_session_uri=sparql_escape_uri(mu_session_uri),
        created=sparql_escape_datetime(now),
        modified=sparql_escape_datetime(now),
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

SELECT ?uri ?status ?sign_flow_uris ?created ?modified ?error_message
WHERE {
  GRAPH $graph {
    ?uri a ext:PrepareSignFlowJob ;
      mu:uuid $uuid ;
      prov:used ?sign_flow_uris ;
      dct:creator ?mu_session_uri ;
      dct:created ?created ;
      dct:modified ?modified ;
      adms:status ?status .
    OPTIONAL { ?uri ext:errorMessage ?error_message }
  }
} ORDER BY ASC(?created) LIMIT 1"""
    ).substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        uuid=sparql_escape_string(uuid),
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
            "modified": record["modified"],
            "status": record["status"],
            "error_message": record["error_message"],
        }
    return None


def update_job_status(job_uri, status_uri):
    now = datetime.now()
    query_string = Template(
        """PREFIX dct: <http://purl.org/dc/terms/>
PREFIX adms: <http://www.w3.org/ns/adms#>

DELETE WHERE {
  $job_uri dct:modified ?modified ;
           adms:status ?status.
}
;
INSERT DATA {
  $job_uri dct:modified $now;
           adms:status $status_uri.
}"""
    ).substitute(
        job_uri=sparql_escape_uri(job_uri),
        status_uri=sparql_escape_uri(status_uri),
        now=sparql_escape_datetime(now),
    )
    agent_update(query_string)


def update_job_error_message(job_uri, error_message):
    now = datetime.now()
    query_string = Template(
        """PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

DELETE WHERE {
  $job_uri dct:modified ?modified ;
           ext:errorMessage ?errorMessage.
}
;
INSERT DATA {
  $job_uri dct:modified $now;
           ext:errorMessage $error_message.
}"""
    ).substitute(
        job_uri=sparql_escape_uri(job_uri),
        error_message=sparql_escape_string(error_message),
        now=sparql_escape_datetime(now),
    )
    agent_update(query_string)


def execute_job(job):
    try:
        update_job_status(job["uri"], JOB["STATUSES"]["BUSY"])
        execute_prepare_sign_flow_job(job)
        update_job_status(job["uri"], JOB["STATUSES"]["SUCCESS"])

        logger.info("**************************************")
        logger.info(f"Successfully finished job <{job['uri']}>")
        logger.info("**************************************")
    except Exception as e:
        logger.exception(f"Execution of job <{job['uri']}> failed:")
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
        agent_update(reset_signflows(sign_flow_uris))
        raise exception
