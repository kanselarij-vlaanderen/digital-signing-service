from string import Template
from pikepdf import Pdf, AttachedFileSpec
from io import BytesIO
import os

from escape_helpers import sparql_escape_string, sparql_escape_uri
from helpers import generate_uuid

from ..agent_query import query as agent_query, update as agent_update
from ..config import APPLICATION_GRAPH, KALEIDOS_RESOURCE_BASE_URI
from ..queries.document import (construct_get_document,
                                construct_get_file_for_document,
                                construct_insert_document,
                                construct_get_decreet_of_bekrachtiging)
from ..queries.file import construct_get_file_query
from . import query_result_helpers, uri, exceptions
from .file import download_sh_doc_to_mu_file, fs_sanitize_filename
from ..constants import BEKRACHTIGING_TYPE_URI

SH_SOURCE = "Kaleidos"

DOC_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/stuk/"


def get_file_path_of_piece(piece_uri):
    get_doc_query_string = construct_get_document(piece_uri)
    doc_result = agent_query(get_doc_query_string)
    doc_records = query_result_helpers.to_recs(doc_result)
    try:
      doc_record = query_result_helpers.ensure_1(doc_records)
    except exceptions.InvalidStateException as e:
      raise exceptions.InvalidStateException(
        f"Piece with uri <{piece_uri}> has zero or multiple titles and cannot be processed correctly. Error message: {e}"
      )

    get_file_query_string = construct_get_file_for_document(
        piece_uri,
        "application/pdf"
    )
    file_result = agent_query(get_file_query_string)
    file_records = query_result_helpers.to_recs(file_result)
    try:
      file_record = query_result_helpers.ensure_1(file_records)
    except exceptions.InvalidStateException as e:
      raise exceptions.InvalidStateException(
        f"Piece with uri <{piece_uri}> has zero or multiple files and cannot be processed correctly. Erorr message: {e}"
      )

    get_file_query_string = construct_get_file_query(
        file_record["uri"],
    )
    file_result = agent_query(get_file_query_string)
    file_records = query_result_helpers.to_recs(file_result)
    try:
      file_record = query_result_helpers.ensure_1(file_records)
    except exceptions.InvalidStateException as e:
      raise exceptions.InvalidStateException(
        f"File with uri <{file_record['uri']}> has incorrect attributes in the database and cannot be processed correctly."
      )
    file_path = file_record["physicalFile"]
    file_name = fs_sanitize_filename(doc_record["name"] + "." + file_record["extension"])
    file_name = file_name.strip()  # SH fails on uploads containing leading whitespace

    file_path = file_path.replace("share://", "/share/")
    if os.path.isfile(file_path):
        return {"path": file_path, "name": file_name}
    else:
        raise exceptions.InvalidStateException(
            f"Piece with uri <{piece_uri}> has zero files and cannot be processed correctly"
        )


def persist_signinghub_document_to_triplestore(signinghub_document_id, signinghub_package_id, piece_uri):
    signinghub_document_uri = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    sh_document_muid = generate_uuid()

    update_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
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
    agent_update(query_string)
    return signinghub_document_uri


def upload_piece_to_sh(sh_session, piece_uri, sh_package_id=None, piece_type=None):
    file = get_file_path_of_piece(piece_uri)
    file_name = file["name"]
    file_path = file["path"]

    if sh_package_id is None:
        sh_package = sh_session.add_package({
            # package_name: "New Package", # Defaults to "Undefined"
            "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
        })
        sh_package_id = sh_package["package_id"]

    # When signing a "bekrachtiging", we want to attach the decreet
    # (if it exists) to the bekrachtiging PDF. We don't want to store
    # this new PDF + attachment, we only want to send it to SigningHub
    if piece_type == BEKRACHTIGING_TYPE_URI:
        decreet = get_decreet_of_bekrachtiging(piece_uri)
        if decreet:
            decreet_file = get_file_path_of_piece(decreet["uri"])
            with Pdf.open(file["path"]) as pdf:
                filespec = AttachedFileSpec.from_filepath(pdf, decreet_file["path"])
                filespec.filename = f"{decreet['title']}.pdf"
                pdf.attachments[f"{decreet['title']}.pdf"] = filespec

                with BytesIO() as bytes_stream:
                    pdf.save(bytes_stream)
                    bytes_stream.seek(0)
                    file_content = bytes_stream.read()
        else:
            with open(file_path, "rb") as f:
                file_content = f.read()
    else:
        with open(file_path, "rb") as f:
            file_content = f.read()

    sh_document = sh_session.upload_document(
        sh_package_id,
        file_content,
        file_name,
        SH_SOURCE,
        convert_document=False)
    sh_document_id = sh_document["documentid"]

    sh_document_uri = persist_signinghub_document_to_triplestore(sh_document_id,
                                                                 sh_package_id,
                                                                 piece_uri)

    return sh_document_uri, sh_package_id, sh_document_id


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


def get_decreet_of_bekrachtiging(piece_uri):
    get_doc_query_string = construct_get_decreet_of_bekrachtiging(piece_uri)
    doc_result = agent_query(get_doc_query_string)
    doc_records = query_result_helpers.to_recs(doc_result)
    if len(doc_records) == 1:
        return doc_records[0]
    else:
        return None
