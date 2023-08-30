import os
from datetime import datetime
from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)
from helpers import generate_uuid

from ..authentication_config import MACHINE_ACCOUNTS
from ..config import TIMEZONE

SESSION_GRAPH = "http://mu.semte.ch/graphs/sessions"
ACCOUNT_GRAPH = "http://mu.semte.ch/graphs/system/users" # http://mu.semte.ch/graphs/public for mock-login
SIGNINGHUB_TOKEN_BASE_URI = "http://kanselarij.vo.data.gift/id/signinghub-tokens/"

SIGNINGHUB_API_URL = os.environ.get("SIGNINGHUB_API_URL")
SIGNINGHUB_OAUTH_TOKEN_EP = SIGNINGHUB_API_URL.strip("/") + "/" + "authenticate" # https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1010
AVAILABLE_OVO_CODES = MACHINE_ACCOUNTS.keys()

def construct_get_mu_session_query(mu_session_uri):
    # Note the filtering by ovo-code values. Since users might have memberships for
    # multiple organizations, we want to restrict the returned value to one for which we have a
    # technical user available.
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX session: <http://mu.semte.ch/vocabularies/session/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>

SELECT ?uuid ?email ?ovoCode
WHERE {
    GRAPH $session_graph {
        $mu_session mu:uuid ?uuid ;
            session:account ?account .
    }
    GRAPH $account_graph {
        ?person foaf:account ?account ;
            foaf:mbox ?email_uri ;
            ^org:member / org:organization / org:identifier ?ovoCode .
        BIND(REPLACE(STR(?email_uri), "^mailto:", "") AS ?email)
        FILTER(?ovoCode IN ($ovo_codes))
    }
}""")
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        account_graph=sparql_escape_uri(ACCOUNT_GRAPH),
        mu_session=sparql_escape_uri(mu_session_uri),
        ovo_codes=", ".join([sparql_escape_string(ovo_code) for ovo_code in AVAILABLE_OVO_CODES]))
    return query_string

def construct_get_org_for_email(email):
    query_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.w3.org/ns/org#>

SELECT ?ovoCode
WHERE {
    GRAPH $account_graph {
        BIND(URI(CONCAT("mailto:", $email)) AS ?email_uri)
        ?person foaf:mbox ?email_uri ;
            ^org:member / org:organization / org:identifier ?ovoCode .
        FILTER(?ovoCode IN ($ovo_codes))
    }
}""")
    query_string = query_template.substitute(
        account_graph=sparql_escape_uri(ACCOUNT_GRAPH),
        email=sparql_escape_string(email),
        ovo_codes=", ".join([sparql_escape_string(ovo_code) for ovo_code in AVAILABLE_OVO_CODES]))
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

def construct_insert_signinghub_session_query(signinghub_session, signinghub_session_uri, signinghub_scope=None):
    # At first sight it might seem unnecessary to add a SH scope address property to the session
    # since sessions are directly linked to a users' mu-session already. This however isn't always the case.
    # Due to SH's authorization model it isn't possible to download a file created by a scoped user with the machine user.
    # To work around this limitation, we also open scoped sessions for the machine user in case the operation requires it.
    # For this use-case, it thus ís necessary to store the scope on the session to be able to differentiate between the different
    # scoped sessions initiated by the machine user.
    # Note that it might be possible to reuse sessions opened by users themselves instead, but we prefer a clear distinction between
    # sessions initiated by users and by the machine.
    signinghub_token_uri = SIGNINGHUB_TOKEN_BASE_URI + generate_uuid()
    expiry_time = signinghub_session.last_successful_auth_time + signinghub_session.access_token_expiry_time
    query_template = Template("""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX oauth-2.0: <http://kanselarij.vo.data.gift/vocabularies/oauth-2.0-session/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>

INSERT DATA {
    GRAPH $session_graph {
        $signinghub_session a oauth-2.0:OauthSession ;
            oauth-2.0:hasEndpointURI $signinghub_token_endpoint ;
            $signinghub_scope
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
        signinghub_scope=f"ext:scope {sparql_escape_string(signinghub_scope)} ;" if signinghub_scope else "",
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

def construct_get_signinghub_machine_user_session_query(signinghub_scope=None):
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
        $signinghub_scope_filter
        ?tokenUri oauth-2.0:hasTokenValue ?token ;
            oauth-2.0:hasExpirytime ?expiryTime .
        BIND($now as ?now)
        FILTER (?now < ?expiryTime)
    }
}
ORDER BY DESC(?expiryTime)
LIMIT 1
""")
    if signinghub_scope:
        signinghub_scope_filter = f"?signinghubSession ext:scope {sparql_escape_string(signinghub_scope)} ."
    else:
        signinghub_scope_filter = "FILTER NOT EXISTS { ?signinghubSession ext:scope ?scope }"
    query_string = query_template.substitute(
        session_graph=sparql_escape_uri(SESSION_GRAPH),
        signinghub_scope_filter=signinghub_scope_filter,
        signinghub_token_endpoint=sparql_escape_uri(SIGNINGHUB_OAUTH_TOKEN_EP),
        now=sparql_escape_datetime(datetime.now(tz=TIMEZONE)))
    return query_string
