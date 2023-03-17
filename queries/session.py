import os
from string import Template
from datetime import datetime
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime
from ..config import TIMEZONE

SESSION_GRAPH = "http://mu.semte.ch/graphs/sessions"
ACCOUNT_GRAPH = "http://mu.semte.ch/graphs/system/users" # http://mu.semte.ch/graphs/public for mock-login
ACCOUNT_GRAPH = "http://mu.semte.ch/graphs/public"
SIGNINGHUB_TOKEN_BASE_URI = "http://kanselarij.vo.data.gift/id/signinghub-tokens/"

SIGNINGHUB_API_URL = os.environ.get("SIGNINGHUB_API_URL")
SIGNINGHUB_OAUTH_TOKEN_EP = SIGNINGHUB_API_URL.strip("/") + "/" + "authenticate" # https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1010

def construct_get_mu_session_query(mu_session_uri):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX session: <http://mu.semte.ch/vocabularies/session/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?uuid ?email
WHERE {
    GRAPH $session_graph {
        $mu_session mu:uuid ?uuid ;
            session:account ?account .
    }
    GRAPH $account_graph {
        ?person foaf:account ?account ;
            foaf:mbox ?email_uri .
        BIND(REPLACE(STR(?email_uri), "^mailto:", "") AS ?email)
    }
}""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        account_graph=sparql_escape_uri(ACCOUNT_GRAPH),
        mu_session=sparql_escape_uri(mu_session_uri))
    return query_string

def construct_get_signinghub_session_query(mu_session_uri):
    # TODO: Model connection betheen Signinghub Session and user/account (now "ext:shSessionAccount").
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX session: <http://mu.semte.ch/vocabularies/session/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX oauth-2.0: <http://kanselarij.vo.data.gift/vocabularies/oauth-2.0-session/>

SELECT (?signinghubSession AS ?uri) ?expiryTime ?token
WHERE {
    GRAPH $session_graph {
        $mu_session session:account ?account .
        ?signinghubSession ext:shSessionAccount ?account .
        ?signinghubSession oauth-2.0:hasEndpointURI $signinghub_token_endpoint ;
            oauth-2.0:hasTokenValue ?tokenUri.
        ?tokenUri oauth-2.0:hasTokenValue ?token ;
            oauth-2.0:hasExpirytime ?expiryTime .
        BIND($now as ?now)
        FILTER (?now < ?expiryTime)
    }
}
ORDER BY DESC(?expiryTime)
LIMIT 1
""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        mu_session=sparql_escape_uri(mu_session_uri),
        signinghub_token_endpoint=sparql_escape_uri(SIGNINGHUB_OAUTH_TOKEN_EP),
        now=sparql_escape_datetime(datetime.now(tz=TIMEZONE)))
    return query_string

def construct_insert_signinghub_session_query(signinghub_session, signinghub_session_uri):
    signinghub_token_uri = SIGNINGHUB_TOKEN_BASE_URI + generate_uuid()
    expiry_time = signinghub_session.last_successful_auth_time + signinghub_session.access_token_expiry_time
    query_template = Template("""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX oauth-2.0: <http://kanselarij.vo.data.gift/vocabularies/oauth-2.0-session/>

INSERT DATA {
    GRAPH $session_graph {
        $signinghub_session a oauth-2.0:OauthSession ;
            oauth-2.0:hasEndpointURI $signinghub_token_endpoint ;
            oauth-2.0:hasTokenValue $token_uri .
        $token_uri a oauth-2.0:BearerToken ;
            dct:created $creation_time ;
            oauth-2.0:hasTokenValue $token_value ;
            oauth-2.0:hasExpirytime $expiry_time .
    }
}""")

    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_session=sparql_escape_uri(signinghub_session_uri),
        signinghub_token_endpoint=sparql_escape_uri(SIGNINGHUB_OAUTH_TOKEN_EP),
        token_uri=sparql_escape_uri(signinghub_token_uri),
        creation_time=sparql_escape_datetime(signinghub_session.last_successful_auth_time.astimezone(TIMEZONE)),
        expiry_time=sparql_escape_datetime(expiry_time.astimezone(TIMEZONE)),
        token_value=sparql_escape_string(signinghub_session.access_token))
    return query_string

def construct_attach_signinghub_session_to_mu_session_query(signinghub_session_uri, mu_session_uri):
    # TODO: Model connection betheen Signinghub Session and user/account (now "ext:shSessionAccount").
    query_template = Template("""
PREFIX session: <http://mu.semte.ch/vocabularies/session/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

INSERT {
    GRAPH $session_graph {
        $signinghub_session ext:shSessionAccount ?account .
    }
}
WHERE {
    GRAPH $session_graph {
        $mu_session session:account ?account .
    }
}""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_session=sparql_escape_uri(signinghub_session_uri),
        mu_session=sparql_escape_uri(mu_session_uri))
    return query_string

def construct_mark_signinghub_session_as_machine_users_query(signinghub_session_uri):
    # TODO: this is a hacky way of marking the machine user session.
    # Should think about way to model the service as an agent (with a mu session?)
    query_template = Template("""
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX oauth-2.0: <http://kanselarij.vo.data.gift/vocabularies/oauth-2.0-session/>

INSERT {
    GRAPH $session_graph {
        $signinghub_session a ext:SigninghubSudoSession .
    }
}
WHERE {
    GRAPH $session_graph {
        $signinghub_session a oauth-2.0:OauthSession .
    }
}
""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_session=sparql_escape_uri(signinghub_session_uri),
        now=sparql_escape_datetime(datetime.now(tz=TIMEZONE)))
    return query_string

def construct_get_signinghub_machine_user_session_query():
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX oauth-2.0: <http://kanselarij.vo.data.gift/vocabularies/oauth-2.0-session/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

SELECT (?signinghubSession AS ?uri) ?expiryTime ?token
WHERE {
    GRAPH $session_graph {
        ?signinghubSession a ext:SigninghubSudoSession .
        ?signinghubSession oauth-2.0:hasEndpointURI $signinghub_token_endpoint ;
            oauth-2.0:hasTokenValue ?tokenUri.
        ?tokenUri oauth-2.0:hasTokenValue ?token ;
            oauth-2.0:hasExpirytime ?expiryTime .
        BIND($now as ?now)
        FILTER (?now < ?expiryTime)
    }
}
ORDER BY DESC(?expiryTime)
LIMIT 1
""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_token_endpoint=sparql_escape_uri(SIGNINGHUB_OAUTH_TOKEN_EP),
        now=sparql_escape_datetime(datetime.now(tz=TIMEZONE)))
    return query_string
