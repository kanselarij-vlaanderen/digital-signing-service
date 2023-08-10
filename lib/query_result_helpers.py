import collections
from typing import Any, DefaultDict, Dict, List, Optional
from . import exceptions

def to_recs(result: Dict) -> List[DefaultDict]:
    bindings = result["results"]["bindings"]
    return [
        collections.defaultdict(
            lambda: None,
            [(k, v["value"]) for k, v in b.items()
        ])
    for b in bindings]

def ensure_1(collection: List[Any]) -> Any:
    if len(collection) != 1:
        raise exceptions.InvalidStateException(f"expected: 1 - found: {len(collection)}")
    return collection[0]

# TODO: below functions don't "escape" anything. Fix naming + consider added value
def sparql_escape_table(table):
    rows = ['(' + sparql_escape_list(row) + ')' for row in table]
    return '\n'.join(rows)

def sparql_escape_list(list):
    return ' '.join(list)
