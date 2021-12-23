from string import Template
from helpers import query
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import helpers, exceptions, uri

def ensure_signflow_exists(signflow_uri):
    if not signflow_exists(signflow_uri):
        raise exceptions.ResourceNotFoundException(signflow_uri)

def signflow_exists(signflow_uri):
    exists_template = Template("""
        PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
        
        ASK {
            $signflow a sign:Handtekenaangelegenheid .
        }
    """)
    
    exists_command = exists_template.substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        signflow=sparql_escape_uri(signflow_uri),
    )

    result = query(exists_command)
    exists = helpers.to_answer(result)
    return exists

def ensure_piece_exists(piece_uri):
    if not piece_exists(piece_uri):
        raise exceptions.ResourceNotFoundException(piece_uri)

def piece_exists(piece_uri):
    exists_template = Template("""
        PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
        
        ASK {
            $piece a dossier:Stuk .
        }
    """)
    
    exists_command = exists_template.substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        piece=sparql_escape_uri(piece_uri)
    )

    result = query(exists_command)
    exists = helpers.to_answer(result)
    return exists
