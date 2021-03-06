import oci

from oci_object_storage_helper import *
from json_object_helper import *
from oci_instance_helper import *
from oci_identity_helper import *
from oci_compute_helper import *
from generators import *

import code_constants as cc


def save_Launched_instance(log, object_storage_client, instance, namespace,
                           bucket_name):
    region = instance.region
    compartment_id = instance.compartment_id
    object_content = str(instance)
    print(object_content)
    object_name = region + "/" + compartment_id + "/" + instance.id + ".json"
    put_object_response = write_objectstorage_object_content(
        log, object_storage_client, object_content, object_name, namespace,
        bucket_name)
    return put_object_response


def save_Launched_instance_to_job(log, object_storage_client, instance,
                                  namespace, bucket_name, job_path):
    object_content = '{"' + cc.INSTANCE + '":' + str(instance) + '}'
    #str(instance)
    #print(object_content)
    object_name = job_path + instance.id + ".json"
    put_object_response = write_objectstorage_object_content(
        log, object_storage_client, object_content, object_name, namespace,
        bucket_name)
    return put_object_response

def get_CreateVnicDetails(vnic,instance_name):
    try:
        details = oci.core.models.CreateVnicDetails(
            subnet_id=vnic[cc.VNIC_SUBNET],
            assign_public_ip = True if vnic[cc.VNIC_ASSIGN_PUBLIC] == cc.CONFIG_TRUE_VALUE else False,
            hostname_label = instance_name,
            display_name = "vnic0-" + instance_name,
            skip_source_dest_check = True if vnic[cc.VNIC_SKIP_DEST_CHECK] == cc.CONFIG_TRUE_VALUE else False,
            assign_private_dns_record = True if vnic[cc.VNIC_ASSIGN_DNS] == cc.CONFIG_TRUE_VALUE else False
        )
    except Exception as e:
        details = oci.core.models.CreateVnicDetails(
            subnet_id=vnic[cc.VNIC_SUBNET],
        )
    return details


def get_launch_instance_details(
    compartment_id,
    availability_domain,
    shape,
    ocpus,
    memory_in_gbs,
    image_id,
    default_vnic,
    instance_name,
    cloud_init,
    ssh_public_key,
    job_path,
):

    instance_metadata = {
        "ssh_authorized_keys": ssh_public_key,
        "user_data": cloud_init,
    }
    freeform_tags = {cc.FREEFORM_TAG_JOB_KEY: job_path}

    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=image_id)
    create_vnic_details = get_CreateVnicDetails(default_vnic,instance_name)
    shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(
        memory_in_gbs=int(memory_in_gbs), ocpus=int(ocpus))
    launch_instance_details = oci.core.models.LaunchInstanceDetails(
        display_name=instance_name,
        compartment_id=compartment_id,
        availability_domain=availability_domain.name,
        shape=shape.shape,
        metadata=instance_metadata,
        source_details=instance_source_via_image_details,
        create_vnic_details=create_vnic_details,
        shape_config=shape_config,
        freeform_tags=freeform_tags,
    )
    return launch_instance_details


def launch_instance(log, compute_client_composite_operations,
                    launch_instance_details):
    launch_instance_response = (
        compute_client_composite_operations.launch_instance_and_wait_for_state(
            launch_instance_details,
            wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_RUNNING],
        ))
    instance = launch_instance_response.data

    log.info("Launched Instance: {}".format(instance.id))
    return instance



def launch_compute(
    log,
    identity_client,
    compute_client,
    compute_client_composite_operations,
    json_object,
    job_path,
):

    try:
        # from config file
        compartment_id = read_json_object_property(log, json_object,
                                                   "compute.compartment_id")
        availability_domain_name = read_json_object_property(
            log, json_object, "compute.placement.availability_domain_name")
        shape_name = read_json_object_property(log, json_object,
                                               "compute.shape.shape_name")
        memory_in_gbs = read_json_object_property(
            log, json_object, "compute.shape.memory_in_gbs")
        ocpus = read_json_object_property(log, json_object,
                                          "compute.shape.ocpus")
        image_id = read_json_object_property(log, json_object,
                                             "compute.image_id")
        instance_name = read_json_object_property(log, json_object,
                                                  "compute.instance_name")
        # default_vnic_subnet_id = read_json_object_property(
        #     log, json_object, "compute.vnics.[0].subnet_id")
        default_vnic = read_json_object_property(
             log, json_object, "compute.vnics.[0]")
        ssh_public_key = read_json_object_property(log, json_object,
                                                   "compute.ssh_public_key")
        cloud_init = read_json_object_property(log, json_object,
                                               "compute.cloud_init")

        # #from platform
        availability_domain = get_availability_domain(
            identity_client, compartment_id, availability_domain_name)
        shape = get_shape(compute_client, compartment_id, availability_domain,
                          shape_name)
        launch_instance_details = get_launch_instance_details(
            compartment_id,
            availability_domain,
            shape,
            ocpus,
            memory_in_gbs,
            image_id,
            default_vnic,
            instance_name,
            cloud_init,
            ssh_public_key,
            job_path,
        )

        # launch
        instance = launch_instance(log, compute_client_composite_operations,
                                   launch_instance_details)
        return instance

    except Exception as e:
        log.error("error launching instance : {}".format(e))
        return None
