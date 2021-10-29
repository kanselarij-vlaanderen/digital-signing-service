from . import exceptions

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [{k: v["value"] for k, v in b.items()} for b in bindings]

def to_answer(result):
    return result["boolean"]

def ensure_1(collection):
    if len(collection) != 0:
        raise exceptions.InvalidStateException(f"expected: 1 - found: {len(collection)}")
    return collection[0]