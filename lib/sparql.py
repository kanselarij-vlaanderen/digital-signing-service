import os
import inspect
import helpers

def query(query_command):
    return helpers.query(query_command)

def update(update_command):
    helpers.update(update_command)

def to_recs(result):
    bindings = result["results"]["bindings"]
    return [{k: v["value"] for k, v in b.items()} for b in bindings]

def to_answer(result):
    return result["boolean"]
