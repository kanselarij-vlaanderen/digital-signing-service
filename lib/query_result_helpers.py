import collections
from typing import Any, DefaultDict, Dict, List
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