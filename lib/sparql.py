from . import exceptions

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [{k: v["value"] for k, v in b.items()} for b in bindings]

def to_answer(result):
    return result["boolean"]

def ensure_1_rec(records):
    if len(records) != 1:
        raise exceptions.InvalidStateException(f"expected: 1 - found: {len(records)}")
    return records[0]