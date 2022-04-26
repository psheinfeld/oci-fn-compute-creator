import json
import oci
from oci_object_storage_helper import *
from json_object_helper import *
from generators import *
from common_helpers import *
from oci_identity_helper import *

import code_constants as cc


def create_volume_config(log, object_storage_client, json_object, namespace,
                         bucket_name, job_path):
    volumes_list = generate_volume_config(log, json_object)
    for vol in volumes_list:
        object_name = job_path + get_daytime_str(
        ) + "-" + generate_random_string() + "-volume.json"
        object_content = json.dumps(vol)
        write_objectstorage_object_content(
            log,
            object_storage_client,
            object_content,
            object_name,
            namespace,
            bucket_name,
        )


def generate_volume_config(log, instance_config):
    config_list = []
    try:
        instance_name = read_json_object_property(log, instance_config,
                                                  cc.COMPUTE_JO_INSTANCE_NAME)
        volumes_list = read_json_object_property(log, instance_config,
                                                 cc.COMPUTE_JO_VOLUMES)
        compartment_id = read_json_object_property(log, instance_config,
                                                   cc.COMPUTE_JO_COMPARTMENT)
        placement = read_json_object_property(log, instance_config,
                                              cc.COMPUTE_JO_PLACEMENT)

        for volume in volumes_list:
            display_name = (instance_name + "-vol-" +
                            str(len(config_list) + 1) + "-" +
                            generate_random_string(6))
            volume_config = {cc.VOLUME: {}}
            volume_config = write_json_object_property(log, volume_config,
                                                       cc.VOLUME_PLACEMENT,
                                                       placement)
            volume_config = write_json_object_property(log, volume_config,
                                                       cc.VOLUME_COMPARTMENT,
                                                       compartment_id)
            volume_config = write_json_object_property(log, volume_config,
                                                       cc.VOLUME_DISPLAY_NAME,
                                                       display_name)
            for k in volume.keys():
                volume_config[cc.VOLUME][k] = volume[k]
            config_list.append(volume_config)

    except Exception as e:
        log.error("error creating volume config : {}".format(e))

    return config_list


def create_volume(log, identity_client,
                  blockstorage_client_composite_operations, json_object):
    try:
        # from config file
        compartment_id = read_json_object_property(log, json_object,
                                                   cc.VOLUME_COMPARTMENT)
        availability_domain_name = read_json_object_property(
            log, json_object, cc.VOLUME_AD)
        display_name = read_json_object_property(log, json_object,
                                                 cc.VOLUME_DISPLAY_NAME)
        size = read_json_object_property(log, json_object, cc.VOLUME_SIZE)
        vpu = read_json_object_property(log, json_object, cc.VOLUME_VPU)
        autotune = read_json_object_property(log, json_object,
                                             cc.VOLUME_AUTOTUNE, "True")
        autotune = True if autotune == "True" else False
        attach_type = read_json_object_property(log, json_object, cc.VOLUME_ATTACH_TYPE)

        #from platform
        availability_domain = get_availability_domain(
            identity_client, compartment_id, availability_domain_name)
        
        freeform_tags = {cc.FREEFORM_TAG_ATTACH_TYPE_KEY: attach_type}
        

        volume_details = oci.core.models.CreateVolumeDetails(
            availability_domain=availability_domain.name,
            compartment_id=compartment_id,
            display_name=display_name,
            size_in_gbs=int(size),
            vpus_per_gb=int(vpu),
            is_auto_tune_enabled=autotune,
            freeform_tags=freeform_tags)

        volume_create_responce = blockstorage_client_composite_operations.create_volume_and_wait_for_state(
            volume_details,
            wait_for_states=[oci.core.models.Volume.LIFECYCLE_STATE_AVAILABLE]
            )

        #todo check responce statuse before return
        return volume_create_responce.data

    except Exception as e:
        log.error("error creating volume : {}".format(e))
        return None


def save_created_volume_to_job(
    log, object_storage_client, volume, namespace, bucket_name,job_path
):
    object_content =   '{"' + cc.VOLUME + '":' + str(volume) + '}'
    #str(instance)
    #print(object_content)
    object_name = job_path + volume.id + ".json"
    put_object_response = write_objectstorage_object_content(
        log, object_storage_client, object_content, object_name, namespace, bucket_name
    )
    return put_object_response