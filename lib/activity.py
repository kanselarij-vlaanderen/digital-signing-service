from datetime import datetime
from pytz import timezone
from flask import g
from helpers import query, update, generate_uuid
from ..queries.activity import construct_insert_signing_prep_activity, \
    construct_insert_signing_activity, \
    construct_get_signing_preps_from_subcase, \
    construct_get_signing_prep_from_subcase_file, \
    construct_get_signing_prep_from_sh_package_id, \
    construct_end_prep_start_signing
from .file import get_file, add_file_to_sh_package
from .mandatee import get_mandatee, get_mandatee_email
from .exceptions import NoQueryResultsException

TIMEZONE = timezone('Europe/Brussels')

SIGNING_PREP_ACT_BASE_URI = "http://example.com/activities/"

SIGNING_ACT_BASE_URI = "http://example.com/activities/"

def create_signing_prep_activity(signing_subcase_uri, file_uri):
    activity = {"uuid": generate_uuid()}
    activity["uri"] = SIGNING_PREP_ACT_BASE_URI + activity["uuid"]
    activity["file"] = file_uri
    file = get_file(file_uri)
    sh_package = g.sh_session.add_package({
        # package_name: "New Package", # Defaults to "Undefined"
        "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
    })
    sh_document = add_file_to_sh_package(file["uri"], sh_package["package_id"])
    act_query_str = construct_insert_signing_prep_activity(activity,
                                                           signing_subcase_uri,
                                                           file_uri,
                                                           sh_package["package_id"],
                                                           sh_document["document_id"])
    update(act_query_str)
    return activity

def get_signing_preps_from_subcase(signing_subcase_uri):
    query_string = construct_get_signing_preps_from_subcase(signing_subcase_uri)
    signing_prep_results = query(query_string)['results']['bindings']
    if not signing_prep_results:
        raise NoQueryResultsException("No signing prep found within subcase <{}>".format(signing_subcase_uri))
    return signing_prep_results

def get_signing_prep_from_sh_package_id(sh_package_id):
    query_string = construct_get_signing_prep_from_sh_package_id(sh_package_id)
    signing_prep_results = query(query_string)['results']['bindings']
    if not signing_prep_results:
        raise NoQueryResultsException("No signing prep found for sh package id '{}'".format(sh_package_id))
    return signing_prep_results[0]

def get_signing_prep_from_subcase_file(signing_subcase_uri, file_uri):
    query_string = construct_get_signing_prep_from_subcase_file(signing_subcase_uri, file_uri)
    signing_prep_results = query(query_string)['results']['bindings']
    if not signing_prep_results:
        raise NoQueryResultsException("No signing prep found within subcase <{}> for file <{}>".format(signing_subcase_uri, file_uri))
    signing_prep = signing_prep_results[0]
    signing_prep["signing"] = [r["signing"] for r in signing_prep_results if r["signing"]] # Many signing activities for one prep activity
    return signing_prep

def add_signing_activity(signing_subcase_uri, file_uri, mandatee_uri):
    signing_prep = get_signing_prep_from_subcase_file(signing_subcase_uri, file_uri)
    mandatee = get_mandatee(mandatee_uri)
    mandatee_email = get_mandatee_email(mandatee_uri)
    g.sh_session.add_users_to_workflow(signing_prep["sh_package_id"], {
        "user_email": mandatee_email,
        "user_name": "{} {}".format(mandatee["first_name"], mandatee["family_name"]), # Not sure how/where this appears, since I expect this to be fetched from SigningHub profile info 
        "role": "SIGNER"
    })
    activity = {"uuid": generate_uuid()}
    activity["uri"] = SIGNING_ACT_BASE_URI + activity["uuid"]
    query_str = construct_insert_signing_activity(activity,
                                                  signing_prep["uri"],
                                                  mandatee_uri)
    update(query_str)
    return activity

def update_activities_signing_started(signing_prep_uri):
    time = datetime.now(TIMEZONE)
    update_status_query = construct_end_prep_start_signing(signing_prep_uri, time)
    update(update_status_query)
