from string import Template
from helpers import query
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import helpers, exceptions, uri, validate, \
    get_signflow_pieces

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
    
    exists_command = exists_template.safe_substitute(
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
    
    exists_command = exists_template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        piece=sparql_escape_uri(piece_uri)
    )

    result = query(exists_command)
    exists = helpers.to_answer(result)
    return exists

def ensure_signer_exists(signer_uri):
    if not piece_exists(signer_uri):
        raise exceptions.ResourceNotFoundException(signer_uri)

def signer_exists(signer_uri):
    exists_template = Template("""
        PREFIX mandaat: <https://data.vlaanderen.be/ns/mandaat#>
        
        ASK {
            $signer a mandaat:Mandataris .
        }
    """)
    
    exists_command = exists_template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.application),
        signer=sparql_escape_uri(signer_uri)
    )

    result = query(exists_command)
    exists = helpers.to_answer(result)
    return exists

def ensure_piece_linked(signflow_uri, piece_uri, valid_statuses):
    pieces = get_signflow_pieces.get_signflow_pieces(signflow_uri)

    if len(pieces) == 0:
        raise exceptions.InvalidStateException(f"Piece {piece_uri} is not associated to signflow {signflow_uri}.")
    elif len(pieces) > 1:
        raise exceptions.InvalidStateException(f"expected: 1 piece - found: {len(pieces)}")
    
    piece = pieces[0]
    if piece["uri"] != piece_uri:
        raise exceptions.InvalidStateException(
            f"Piece {piece_uri} is not associated to signflow {signflow_uri}.")
    if piece["status"] not in valid_statuses:
        raise exceptions.InvalidStateException(
            f"Piece {piece_uri} is in incorrect state for this action.")
