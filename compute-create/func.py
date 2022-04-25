import io
import json
import oci
import random
import string
import logging
from datetime import datetime as dt
from fdk import response

from oci_object_storage_helper import read_objectstorage_object_content
from oci_object_storage_helper import write_objectstorage_object_content
from oci_object_storage_helper import delete_objectstorage_object

from json_object_helper import read_json_object_property
from json_object_helper import write_json_object_property

from oci_instance_helper import launch_compute
from oci_instance_helper import save_Launched_instance

from generators import generate_numeric, generate_random, generate_named


def respond(ctx, message="OK"):
    return response.Response(
        ctx,
        response_data=json.dumps({"message": message}),
        headers={"Content-Type": "application/json"},
    )


def create_resource(
    log,
    identity_client,
    compute_client,
    compute_client_composite_operations,
    json_object,
    namespace,
    bucket_name,
):

    try:
        compute = read_json_object_property(log, json_object, "compute")
        if compute:
            return launch_compute(
                log,
                identity_client,
                compute_client,
                compute_client_composite_operations,
                json_object,
            )
    except Exception as e:
        log.error("error creating resource : {}".format(e))
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
            if "[]" not in base:
                continue

            # numeric
            if not (convention.get("numerical") is None):
                names = names + generate_numeric(log, base, convention.get("numerical"))
            # random
            if not (convention.get("random") is None):
                names = names + generate_random(log, base, convention.get("random"))
            # named
            if not (convention.get("named") is None):
                names = names + generate_named(log, base, convention.get("named"))

    except Exception as e:
        log.error("error reading values to generate : {}".format(e))

    # empty return
    if len(names) == 0:
        return template["template"]

    # one by one return
    position = 0
    while position < len(names):
        yield write_json_object_property(log, template, prop, names[position])[
            "template"
        ]
        position = position + 1


def generate_from_template(
    log, object_storage_client, json_object, namespace, bucket_name
):
    for template in json_object:
        for generated in generate(log, template):
            log.info("generated : {}".format(generated))
            object_name = (
                str(dt.now().strftime("%Y%m%d-%H%M-"))
                + "".join(random.choice(string.ascii_lowercase) for _ in range(8))
                + "-compute.json"
            )
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
    log.info("Executing function code")

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

    # auth objects
    signer = oci.auth.signers.get_resource_principals_signer()
    # signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    object_storage_client = oci.object_storage.ObjectStorageClient(
        config={}, signer=signer
    )
    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(
        compute_client
    )

    # read new object
    object_file_content = read_objectstorage_object_content(
        log, object_storage_client, namespace, bucket_name, object_name
    )
    if not object_file_content:
        return respond(ctx)
    try:
        json_object = json.loads(object_file_content)
    except Exception as e:
        log.error("error reading json file : {}".format(e))
        return respond(ctx)

    # {} is a single object
    if type(json_object) is dict:
        instance = create_resource(
            log,
            identity_client,
            compute_client,
            compute_client_composite_operations,
            json_object,
            namespace,
            bucket_name,
        )
        if instance:
            save_result = save_Launched_instance(
                log, object_storage_client, instance, namespace, bucket_name
            )
            delete_objectstorage_object(
                log, object_storage_client, namespace, bucket_name, object_name
            )

        return respond(ctx)

    # [{}] or [{},{},...] is a multi template of compute to create
    if type(json_object) is list:
        generate_from_template(
            log, object_storage_client, json_object, namespace, bucket_name
        )
        delete_objectstorage_object(
            log, object_storage_client, namespace, bucket_name, object_name
        )
        return respond(ctx)

    return respond(ctx)
