import typing

import string
from helpers import query as orig_query, update as orig_update, log, generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string
from .. import config
from . import exceptions

class Template():
    def __init__(self, template_string: str) -> None:
        self.template = string.Template(template_string)

    def substitute(self, **substitutions: typing.Dict[str, str]):
        if config.mode.dev:
            for (key, val) in substitutions.items():
                valid_sparql_val = (val.startswith('"') or val.startswith("'")
                    or val.startswith('<')
                    or val.isnumeric()
                    or val == "true" or val == "false"
                    or val.startswith('('))
                if not valid_sparql_val:
                    raise Exception(f"You probably forgot to escape: {key}")
        
        return self.template.substitute(**substitutions)

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [{k: v["value"] for k, v in b.items()} for b in bindings]

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
