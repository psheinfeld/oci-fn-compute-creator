import io
import json
import oci
import random
import string
import logging
from datetime import datetime as dt
from fdk import response

from oci_object_storage_helper import *
from json_object_helper import *
from oci_instance_helper import *
from generators import *
from oci_volume_helper import *
from common_helpers import *

import code_constants as cc


def respond(ctx, message="OK"):
    return response.Response(
        ctx,
        response_data=json.dumps({"message": message}),
        headers={"Content-Type": "application/json"},
    )


def create_vnics_config(log, object_storage_client, json_object,
                                 namespace, bucket_name, job_path):
    object_content = read_json_object_property(log, json_object,cc.COMPUTE_VNICS)
    object_content = json.dumps(object_content)
    object_name = job_path + cc.OCID_PREFIX + cc.VNICS + ".json"
    put_object_response = write_objectstorage_object_content(
        log, object_storage_client, object_content, object_name, namespace,
        bucket_name)


def create_resource(log, object_storage_client,
                    blockstorage_client_composite_operations, identity_client,
                    compute_client, compute_client_composite_operations,
                    json_object, namespace, bucket_name, json_object_path):

    try:
        resource_type = read_json_first_key(log, json_object)
        if resource_type == cc.COMPUTE:

            # compute create job path
            instance_name = read_json_object_property(
                log, json_object, cc.COMPUTE_JO_INSTANCE_NAME)
            job_path = generate_job_path(instance_name)

            # generate and save block volume object
            create_volume_config(log, object_storage_client, json_object,
                                 namespace, bucket_name, job_path)
            
            create_vnics_config(log, object_storage_client, json_object,
                                 namespace, bucket_name, job_path)

            # create new instance
            new_compute = launch_compute(
                log,
                identity_client,
                compute_client,
                compute_client_composite_operations,
                json_object,
                job_path
            )

            if new_compute:
                save_result = save_Launched_instance_to_job(
                    log, object_storage_client, new_compute, namespace,
                    bucket_name, job_path)

            return save_result

        if resource_type == cc.VOLUME:
            new_volume = create_volume(log, identity_client,
                                   blockstorage_client_composite_operations,
                                   json_object)
            #save result
            save_result = save_created_volume_to_job(log,
                                                     object_storage_client,
                                                     new_volume, namespace,
                                                     bucket_name,
                                                     json_object_path)

            return save_result

    except Exception as e:
        log.error("error creating resource : {}".format(e))
        return None

    return None


# generates array of names
def generate(log, template):
    names = []

    try:
        values = template["values"]
        for value in values:
            prop = value["prop"]
            convention = value["convention"]
            base = read_json_object_property(log, template, prop)
            if cc.TEMPLATE_PLACEHOLDER not in base:
                log.error("no {} found in value {} at path {} ".format(cc.TEMPLATE_PLACEHOLDER,base,prop))
                continue

            # numeric
            if not (convention.get("numerical") is None):
                names = names + generate_numeric(log, base,
                                                 convention.get("numerical"))
            # random
            if not (convention.get("random") is None):
                names = names + generate_random(log, base,
                                                convention.get("random"))
            # named
            if not (convention.get("named") is None):
                names = names + generate_named(log, base,
                                               convention.get("named"))

    except Exception as e:
        log.error("error reading values to generate : {}".format(e))

    # empty return
    if len(names) == 0:
        return template["template"]

    # one by one return
    position = 0
    while position < len(names):
        yield write_json_object_property(log, template, prop,
                                         names[position])["template"]
        position = position + 1


def generate_from_template(log, object_storage_client, json_object, namespace,
                           bucket_name):
    for template in json_object:
        for generated in generate(log, template):
            log.info("generated : {}".format(generated))
            object_name = (str(dt.now().strftime("%Y%m%d-%H%M-")) + "".join(
                random.choice(string.ascii_lowercase)
                for _ in range(8)) + "-compute.json")
            object_content = json.dumps({"compute": generated})
            log.info("object_name : {}".format(object_name))
            put_object_response = write_objectstorage_object_content(
                log,
                object_storage_client,
                object_content,
                object_name,
                namespace,
                bucket_name,
            )


def handler(ctx, data: io.BytesIO = None):
    log = logging.getLogger()
    log.info("Executing compute-create function code")

    # get event information
    try:
        body = json.loads(data.getvalue())
        eventID = body["eventID"]
        object_name = body["data"]["resourceName"]
        bucket_name = body["data"]["additionalDetails"]["bucketName"]
        namespace = body["data"]["additionalDetails"]["namespace"]

        log.info("eventID : {}".format(eventID))
        log.info("object_name : {}".format(object_name))
        log.info("bucket_name : {}".format(bucket_name))
        log.info("namespace : {}".format(namespace))

    except Exception as e:
        log.error("error reading object-storage event : {}".format(e))
        return respond(ctx)

    #stop runnning for objects with OCID:
    if cc.OCID_PREFIX in object_name:
        return respond(ctx)
    
    # auth objects
    signer = oci.auth.signers.get_resource_principals_signer()
    # signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    object_storage_client = oci.object_storage.ObjectStorageClient(
        config={}, signer=signer)
    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(
        compute_client)
    blockstorage_client = oci.core.BlockstorageClient(config={}, signer=signer)
    blockstorage_client_composite_operations = oci.core.BlockstorageClientCompositeOperations(
        blockstorage_client)

    # read new object
    object_file_content = read_objectstorage_object_content(
        log, object_storage_client, namespace, bucket_name, object_name)
    if not object_file_content:
        return respond(ctx)
    try:
        json_object = json.loads(object_file_content)
    except Exception as e:
        log.error("error reading json file : {}".format(e))
        return respond(ctx)

    # {} is a single object
    if type(json_object) is dict:
        json_object_path = object_name[:object_name.rfind("/") + 1]
        creation_result = create_resource(
            log, object_storage_client,
            blockstorage_client_composite_operations, identity_client,
            compute_client, compute_client_composite_operations, json_object,
            namespace, bucket_name, json_object_path)

        delete_objectstorage_object(
            log, object_storage_client, namespace, bucket_name, object_name
        )

        return respond(ctx)

    # [{}] or [{},{},...] is a multi template of compute to create
    if type(json_object) is list:
        generate_from_template(log, object_storage_client, json_object,
                               namespace, bucket_name)
        delete_objectstorage_object(
            log, object_storage_client, namespace, bucket_name, object_name
        )
        return respond(ctx)

    return respond(ctx)
