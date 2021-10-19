import os
import inspect

def relative_file(rel_path):
    calling_file = inspect.stack()[1].filename
    abs_path = os.path.join(os.path.dirname(os.path.realpath(calling_file)), rel_path)
    return open(abs_path, encoding='UTF-8').read()

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [{k: v["value"] for k, v in b.items()} for b in bindings]

def to_answer(result):
    return result["boolean"]
