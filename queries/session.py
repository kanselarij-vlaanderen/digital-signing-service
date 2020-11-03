from string import Template
from datetime import datetime
from pytz import timezone
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime

TIMEZONE = timezone('Europe/Brussels')
SESSION_GRAPH = "http://mu.semte.ch/graphs/sessions"
SIGNINGHUB_SESSION_BASE_URI = "http://example.com/signinghub-sessions/"

def construct_get_mu_session_query(mu_session_uri):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

SELECT ?uuid ?oauthToken
WHERE {
    GRAPH $session_graph {
        $mu_session mu:uuid ?uuid ;
            ext:oauthToken ?oauthToken .
    }
}""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        mu_session=sparql_escape_uri(mu_session_uri))
    return query_string

def construct_get_signinghub_session_query(mu_session_uri):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

SELECT (?signinghubSession AS ?uri) ?expiryTime ?token
WHERE {
    GRAPH $session_graph {
        $mu_session ext:signinghubSession ?signinghubSession
        ?signinghubSession mu:uuid ?uuid ;
            ext:expiryTime ?expiryTime ;
            ext:token ?token .
        BIND($now as ?now)
        FILTER (?expiryTime > ?now)
    }
}
ORDER BY DESC(?expiryTime)
LIMIT 1
""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        mu_session=sparql_escape_uri(mu_session_uri),
        now=sparql_escape_datetime(datetime.now(tz=TIMEZONE)))
    return query_string

def construct_insert_signinghub_session_query(signinghub_session, mu_session_uri):
    signinghub_session["uuid"] = generate_uuid()
    signinghub_session["uri"] = SIGNINGHUB_SESSION_BASE_URI + signinghub_session["uuid"]
    query_template = Template("""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

INSERT {
    GRAPH $session_graph {
        $signinghub_session mu:uuid $uuid ;
            dct:created $creation_time ;
            ext:expiryTime $expiry_time ;
            ext:token $token .
        $mu_session ext:signinghubSession $signinghub_session .
    }
}
WHERE {
    GRAPH $session_graph {
        $mu_session mu:uuid ?uuid .
    }
}""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_session=sparql_escape_uri(signinghub_session["uri"]),
        mu_session=sparql_escape_uri(mu_session_uri),
        uuid=sparql_escape_string(signinghub_session["uuid"]),
        creation_time=sparql_escape_datetime(signinghub_session["creation_time"].astimezone(TIMEZONE)),
        expiry_time=sparql_escape_datetime(signinghub_session["expiry_time"].astimezone(TIMEZONE)),
        token=sparql_escape_string(signinghub_session["token"]))
    return query_string
