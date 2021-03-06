import io
import json
import logging
from posixpath import split
import oci

from fdk import response

import code_constants as cc
from oci_object_storage_helper import *


def is_volume_ocid(ocid) -> bool:
    return True if (ocid.split("."))[1] == cc.VOLUME else False

def is_vnics_ocid(ocid) -> bool:
    return True if (ocid.split("."))[1] == cc.VNICS else False

def extract_id(resource: str) -> str:
    resource = resource.replace(".json", "")
    resource = resource[resource.rfind("/") + 1:]
    return resource


def respond(ctx, message="OK"):
    return response.Response(
        ctx,
        response_data=json.dumps({"message": message}),
        headers={"Content-Type": "application/json"},
    )


def get_compute_instance(log, compute_client, instance_id):
    try:
        return (compute_client.get_instance(instance_id)).data

    except Exception as e:
        log.error("error getting compute : {}".format(e))
        return None


def attach_volume(log, compute_client_composite_operations,
                  blockstorage_client, instance, volume_id):
    log.info("attaching volume : {}".format(volume_id))

    #get attach type from tag
    try:
        volume = (blockstorage_client.get_volume(volume_id)).data
        fftags = volume.freeform_tags
        attach_type = fftags[cc.FREEFORM_TAG_ATTACH_TYPE_KEY]
    except Exception as e:
        log.error("error getting free form tags : {}".format(e))
        return None
    log.info("attach_type : {}".format(attach_type))

    #oci.core.models.AttachVolumeDetails
    try:
        attach_volume_details = oci.core.models.AttachVolumeDetails(
            instance_id=instance.id, volume_id=volume.id, type=attach_type)
        attach_volume_responce = compute_client_composite_operations.attach_volume_and_wait_for_state(
            attach_volume_details,
            wait_for_states=[
                oci.core.models.VolumeAttachment.LIFECYCLE_STATE_ATTACHED
            ])
        return attach_volume_responce.data

    except Exception as e:
        log.error("error attaching {} to {} via {} : {}".formate(volume.id,instance.id,attach_type,e))
        return None

def get_CreateVnicDetails(vnic,instance_name,id):
    try:
        details = oci.core.models.CreateVnicDetails(
            subnet_id=vnic[cc.VNIC_SUBNET],
            assign_public_ip = True if vnic[cc.VNIC_ASSIGN_PUBLIC] == cc.CONFIG_TRUE_VALUE else False,
            #hostname_label = instance_name,
            display_name = "vnic"+ str(id) + "-" + instance_name,
            skip_source_dest_check = True if vnic[cc.VNIC_SKIP_DEST_CHECK] == cc.CONFIG_TRUE_VALUE else False,
            assign_private_dns_record = True if vnic[cc.VNIC_ASSIGN_DNS] == cc.CONFIG_TRUE_VALUE else False
        )
    except Exception as e:
        details = oci.core.models.CreateVnicDetails(
            subnet_id=vnic[cc.VNIC_SUBNET],
        )
    return details

def attach_vnics(log, compute_client_composite_operations,
                          object_storage_client, compute_instance, namespace, bucket_name, object_name):
    object_file_content = read_objectstorage_object_content(
        log, object_storage_client, namespace, bucket_name, object_name)
    if not object_file_content:
        return []
    try:
        json_object = json.loads(object_file_content)
    except Exception as e:
        log.error("error reading json file : {}".format(e))
        return []
    
    attach_vnics = []
    for vnic in json_object[1:]:
        create_vnic_details = get_CreateVnicDetails(vnic,compute_instance.display_name,len(attach_vnics)+1)
        attach_vnic_details = oci.core.models.AttachVnicDetails(
            create_vnic_details = create_vnic_details,
            instance_id = compute_instance.id
        )
        attachment = compute_client_composite_operations.attach_vnic_and_wait_for_state(
            attach_vnic_details = attach_vnic_details,
            wait_for_states=[oci.core.models.VnicAttachment.LIFECYCLE_STATE_ATTACHED]
        )
        attach_vnics.append(attachment.data)
    
    return attach_vnics




def handler(ctx, data: io.BytesIO = None):
    log = logging.getLogger()
    log.info("Executing compute-attach-devices function code")

    try:
        # get event information
        body = json.loads(data.getvalue())
        eventID = body["eventID"]
        resourceName = body["data"]["resourceName"]
        resourceId = body["data"]["resourceId"]
        compartmentId = body["data"]["compartmentId"]
        availabilityDomain = body["data"]["availabilityDomain"]

        #get function config
        bucket_name = (ctx.Config())["bucket_name"]
        namespace = (ctx.Config())["namespace"]

        log.info("eventID : {}".format(eventID))
        log.info("resourceName : {}".format(resourceName))
        log.info("resourceId : {}".format(resourceId))
        log.info("compartmentId : {}".format(compartmentId))
        log.info("availabilityDomain : {}".format(availabilityDomain))
        log.info("bucket_name : {}".format(bucket_name))
        log.info("namespace : {}".format(namespace))

    except Exception as e:
        log.error("error reading event : {}".format(e))
        return respond(ctx)

    signer = oci.auth.signers.get_resource_principals_signer()
    # signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    object_storage_client = oci.object_storage.ObjectStorageClient(
        config={}, signer=signer)
    # identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(
        compute_client)
    blockstorage_client = oci.core.BlockstorageClient(config={}, signer=signer)

    try:
        compute_instance = get_compute_instance(log, compute_client,
                                                resourceId)
        fftags = compute_instance.freeform_tags
        job_path = fftags[cc.FREEFORM_TAG_JOB_KEY]
    except Exception as e:
        log.error("error getting free form tags : {}".format(e))
        return respond(ctx)

    log.info("job_path : {}".format(job_path))

    #read all files in job folder
    objects_list = list_objectstorage_objects_by_prefix(
        log, object_storage_client, namespace, bucket_name, job_path)
    attached_volumes = []
    attached_vnics = []
    for resource in objects_list:
        resource_id = extract_id(resource.name)
        if is_volume_ocid(resource_id):
            attachment = attach_volume(log, compute_client_composite_operations,
                          blockstorage_client, compute_instance, resource_id)
            attached_volumes.append(attachment)
        if is_vnics_ocid(resource_id):
            attached_vnics = attach_vnics(log, compute_client_composite_operations,
                          object_storage_client, compute_instance, namespace, bucket_name, resource.name)
    
    #save all + ip + mac
    for atch in attached_volumes:
        log.info(atch)
    for atch in attached_vnics:
        log.info(atch)


