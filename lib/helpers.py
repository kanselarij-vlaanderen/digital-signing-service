import typing

import collections
from helpers import query as orig_query, update as orig_update, log, logger, generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import exceptions

def query(query_command: str) -> str:
    return orig_query(query_command)

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [
        collections.defaultdict(
            lambda: None,
            [(k, v["value"]) for k, v in b.items()
        ])
    for b in bindings]

def to_answer(result):
    return result["boolean"]

def ensure_1(collection):
    if len(collection) != 1:
        raise exceptions.InvalidStateException(f"expected: 1 - found: {len(collection)}")
    return collection[0]

def sparql_escape_table(table):
    rows = ['(' + sparql_escape_list(row) + ')' for row in table]
    return '\n'.join(rows)

def sparql_escape_list(list):
    return ' '.join(list)
