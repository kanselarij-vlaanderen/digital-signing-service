import os
import inspect
import typing
import helpers
import escape_helpers
from ... import sudo_query

def file_rel(rel_path):
    calling_file = inspect.stack()[1].filename
    abs_path = os.path.join(os.path.dirname(os.path.realpath(calling_file)), rel_path)
    return abs_path

def string(str: str) -> str:
    return escape_helpers.sparql_escape_string(str)

def uri(uri: str) -> str:
    return escape_helpers.sparql_escape_uri(uri)

def list(lst: "typing.List[str]"):
    ",".join(lst)

def query(file, substitutions):
    result = _query(file, substitutions)
    bindings = result["results"]["bindings"]
    records = [{k: v["value"] for k, v in result.items()} for result in bindings]
    return records

def ask(file: str, substitutions: "dict[str, str]"):
    results = _query(file, substitutions)
    answer = results["boolean"]
    return answer

def exists(graph: str, type: str, resource_uri: str):
    exists = ask(file_rel("exists.sparql"), {
        "graph" : uri(graph),
        "type"  : uri(type),
        "uri"   : uri(resource_uri),
    })
    return exists

def _query(file, substitutions: "dict[str, str]"):
    query = _prepare_query(file, substitutions)

    helpers.log("query: " + query)
    result = helpers.query(query)
    helpers.log("result: ", result)

    return result

def update(query_file, substitutions):
    command = _prepare_query(query_file, substitutions)
    helpers.log("update: " + command)
    sudo_query.update(command)
    helpers.log("update success")

def _prepare_query(query_file, substitutions):
    query = open(query_file, 'r', encoding="utf-8").read()

    has_graph = "graph" in substitutions
    if not has_graph:
        raise Exception("no graph")

    for k, v in substitutions.items():
        if v.startswith("http://"):
            raise Exception("unescaped uri:" + v)
        query = query.replace("<http://mu.semte.ch/placeholders/" + k + ">", v)

    if query.find("<http://mu.semte.ch/placeholders/") >= 0:
        raise Exception("not fully substituted: " + query)

    return query
