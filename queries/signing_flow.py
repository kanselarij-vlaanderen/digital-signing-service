from string import Template
from escape_helpers import sparql_escape_uri, sparql_escape_string
from ..config import APPLICATION_GRAPH

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

def construct_get_signing_flow_by_package_id(sh_package_id: str):
    query_template = Template("""
    PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
    PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
    PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

    SELECT DISTINCT (?signing_flow AS ?uri) ?sh_package_id ?sh_document_id
    WHERE {
        ?signing_flow a sign:Handtekenaangelegenheid ;
            mu:uuid ?signflow_id ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit ;
            sign:voorbereidingGenereert ?sh_document .
        ?sh_document a sh:Document ;
            sh:packageId $sh_package_id ;
            sh:documentId ?sh_document_id .
        }
    }
    """)
    return query_template.substitute(
      sh_package_id=sparql_escape_string(sh_package_id)
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
