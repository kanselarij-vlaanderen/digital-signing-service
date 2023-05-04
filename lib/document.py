from string import Template
from helpers import generate_uuid, query, update, logger
from flask import g
from escape_helpers import sparql_escape_uri, sparql_escape_string
from ..queries.document import construct_insert_document
from ..agent_query import update as agent_update
from .file import download_sh_doc_to_mu_file
from ..config import APPLICATION_GRAPH, KANSELARIJ_GRAPH, KALEIDOS_RESOURCE_BASE_URI
from ..queries.document import construct_get_file_for_document
from ..queries.file import construct_get_file_query
from . import exceptions, query_result_helpers, uri, signing_flow

SH_SOURCE = "Kaleidos"

SIGNED_DOCS_GRAPH = KANSELARIJ_GRAPH

DOC_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/stuk/"

def upload_piece_to_sh(piece_uri, signinghub_package_id=None):
    get_file_query_string = construct_get_file_for_document(
        piece_uri,
        "application/pdf"
    )
    file_result = query(get_file_query_string)
    file_records = query_result_helpers.to_recs(file_result)
    file_record = query_result_helpers.ensure_1(file_records)
    get_file_query_string = construct_get_file_query(
        file_record["uri"],
    )
    file_result = query(get_file_query_string)
    file_records = query_result_helpers.to_recs(file_result)
    file_record = query_result_helpers.ensure_1(file_records)
    file_name = file_record["name"]
    file_path = file_record["physicalFile"]

    file_path = file_path.replace("share://", "/share/")
    with open(file_path, "rb") as f:
        file_content = f.read()

    if signinghub_package_id is None:
        signinghub_package = g.sh_session.add_package({
            # package_name: "New Package", # Defaults to "Undefined"
            "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
        })
        signinghub_package_id = signinghub_package["package_id"]

    signinghub_document = g.sh_session.upload_document(
        signinghub_package_id,
        file_content,
        file_name,
        SH_SOURCE,
        convert_document=False)
    signinghub_document_id = signinghub_document["documentid"]
    signinghub_document_uri = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    sh_document_muid = generate_uuid()

    update_template = Template("""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
    PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
    PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

    INSERT DATA {
        GRAPH $graph {
            $sh_document a sh:Document ;
                mu:uuid $sh_document_muid ;
                sh:packageId $sh_package_id ;
                sh:documentId $sh_document_id ;
                prov:hadPrimarySource $piece .
        }
    }
    """)

    query_string = update_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        piece=sparql_escape_uri(piece_uri),
        sh_document=sparql_escape_uri(signinghub_document_uri),
        sh_document_muid=sparql_escape_string(sh_document_muid),
        sh_document_id=sparql_escape_string(str(signinghub_document_id)),
        sh_package_id=sparql_escape_string(str(signinghub_package_id)),
    )
    update(query_string)

    return signinghub_document_uri, signinghub_package_id, signinghub_document_id

def download_sh_doc_to_kaleidos_doc(sh_package_id, sh_document_id, document_name):
    virtual_file = download_sh_doc_to_mu_file(sh_package_id, sh_document_id)
    doc = {
        "uuid": generate_uuid(),
        "name": document_name
    }
    doc["uri"] = DOC_BASE_URI + doc["uuid"]
    ins_doc_query_string = construct_insert_document(document_name,
                                                     doc["uri"],
                                                     doc["uuid"],
                                                     virtual_file["uri"])
    agent_update(ins_doc_query_string)
    return doc
