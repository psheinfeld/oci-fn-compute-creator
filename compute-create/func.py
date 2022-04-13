
import io
import json
import oci
import logging

from fdk import response


def read_objectstorage_object(log,namespace, bucket_name, object_name):
    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)

    try:
        log.info("attempting to read {} from {} in {}".format(object_name,bucket_name,namespace))
        object_data = client.get_object(namespace, bucket_name, object_name)
        if object_data.status == 200:
            log.info("{} from {} received".format(object_name,bucket_name))
            return (True,json.dumps(str(object_data.data.text)))
    except Exception as e:
        log.error("error reading object from object-storage : {}".format(e))
    return (False,"")

def create_compute(log,compute_config):
    log.info("attempting to ctreate instance : {} ".format())



def get_launch_instance_details(log,compute_config):
    compartment_id = compute_config.compartment_id
    availability_domain_name = compute_config.availability_domain_name
    shape = compute_config.shape
    image_id = compute_config.image
    subnet_id = compute_config.subnet
    ssh_public_key = compute_config.ssh_authorized_keys
    instance_name = compute_config.instance_name

    instance_metadata = {
        'ssh_authorized_keys': ssh_public_key,
        'some_metadata_item': 'some_item_value'
    }

    # instance_metadata['user_data'] = oci.util.file_content_as_launch_instance_user_data(
    #     'examples/launch_instance/user_data.sh'
    # )

    # Extended metadata differs from normal metadata in that it can support nested maps/dicts. If you are providing
    # these, you should consider whether defined and freeform tags on an instance would better meet your use case.
    # instance_extended_metadata = {
    #     'string_key_1': 'string_value_1',
    #     'map_key_1': {
    #         'string_key_2': 'string_value_2',
    #         'map_key_2': {
    #             'string_key_3': 'string_value_3'
    #         },
    #         'empty_map_key': {}
    #     }
    # }

    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=image_id
    )
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=subnet_id
    )
    launch_instance_details = oci.core.models.LaunchInstanceDetails(
        display_name=instance_name,
        compartment_id=compartment_id,
        availability_domain=availability_domain_name,
        shape=shape.shape,
        metadata=instance_metadata,
        extended_metadata=instance_extended_metadata,
        source_details=instance_source_via_image_details,
        create_vnic_details=create_vnic_details
    )
    return launch_instance_details



def handler(ctx, data: io.BytesIO=None):
    log = logging.getLogger()
    log.info("Executing function code")
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

    #read new file
    compute_config = read_objectstorage_object(log,namespace, bucket_name, object_name)
    if compute_config[0] :
        compute_config = compute_config[1]

    return response.Response(
        ctx, response_data=json.dumps(
            {"message": "done"}),
        headers={"Content-Type": "application/json"}
    )
    