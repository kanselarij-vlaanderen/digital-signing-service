from flask import g
from helpers import query, update, generate_uuid
from ..queries.activity import construct_insert_signing_prep_activity, construct_insert_signing_activity
from .document import get_file_for_document
from .file import add_file_to_sh_package

SIGNING_PREP_ACT_BASE_URI = "http://example.com/activities/"

SIGNING_ACT_BASE_URI = "http://example.com/activities/"

def create_signing_prep_activity(signing_subcase_uri, document_uri):
    activity = {"uuid": generate_uuid()}
    activity["uri"] = SIGNING_PREP_ACT_BASE_URI + activity["uuid"]
    file = get_file_for_document(document_uri)
    sh_package = g.sh_session.add_package({
        # package_name: "New Package", # Defaults to "Undefined"
        "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
    })
    sh_document = add_file_to_sh_package(file["uri"], sh_package["package_id"])
    act_query_str = construct_insert_signing_prep_activity(activity,
                                                           signing_subcase_uri,
                                                           document_uri,
                                                           sh_package["package_id"],
                                                           sh_document["document_id"])
    update(act_query_str)
    return activity

def add_signing_activity(signing_prep_uri, mandatee_uri):
    activity = {"uuid": generate_uuid()}
    activity["uri"] = SIGNING_ACT_BASE_URI + activity["uuid"]
    # TODO: query for mandatee's e-mail, register signer at sh, then persist here
    query_str = construct_insert_signing_activity(activity,
                                                  signing_prep_uri,
                                                  mandatee_uri)
    update(query_str)
    return activity
