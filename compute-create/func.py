
import io
import json
import oci
import logging
import random
import string
from datetime import datetime as dt
from fdk import response


def read_objectstorage_object_content(log,client,namespace, bucket_name, object_name):

    try:
        log.info("attempting to read {} from {} in {}".format(object_name,bucket_name,namespace))
        object_data = client.get_object(namespace, bucket_name, object_name)
        if object_data.status == 200:
            log.info("{} from {} received".format(object_name,bucket_name))
            return object_data.data.text
    except Exception as e:
        log.error("error reading object from object-storage : {}".format(e))
    return None


def write_objectstorage_object_content(log, client, object_content, object_name, namespace, bucket_name):
    try:
        log.info("attempting to write {} to {} in {}".format(object_name,bucket_name,namespace))
        put_object_response = client.put_object(namespace_name=namespace,bucket_name=bucket_name,object_name=object_name,put_object_body=object_content)
        return put_object_response
    except Exception as e:
        log.error("error writing object to object-storage : {}".format(e))
    return None

def respond(message="OK"):
    return response.Response(
        ctx, response_data=json.dumps(
            {"message": message}),
        headers={"Content-Type": "application/json"}
    )
    # print(message)


def get_availability_domain(identity_client, compartment_id,availability_domain_name):
    list_availability_domains_response = oci.pagination.list_call_get_all_results(
        identity_client.list_availability_domains,
        compartment_id
    )
    for ad in list_availability_domains_response.data:
        if availability_domain_name.lower() in ad.name.lower():
            return ad
    return None


def get_shape(compute_client, compartment_id, availability_domain,shape_name):
    list_shapes_response = oci.pagination.list_call_get_all_results(
        compute_client.list_shapes,
        compartment_id,
        availability_domain=availability_domain.name
    )

    for shape in list_shapes_response.data:
        if shape_name.lower() == shape.shape.lower():
            return shape
    return None
    
def get_image_by_id(compute, image_id):
    try:
        image = (compute.get_image(image_id)).data
        return image
    except Exception as e:
        print(e)
        return (None)

def get_launch_instance_details(compartment_id, availability_domain, shape, ocpus, memory_in_gbs, image_id, subnet_id,instance_name,cloud_init, ssh_public_key):

    instance_metadata = {
        'ssh_authorized_keys': ssh_public_key,
        'some_metadata_item': 'some_item_value',
        'user_data': cloud_init
    }

    instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
        image_id=image_id
    )
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=subnet_id
    )
    launch_instance_details = oci.core.models.LaunchInstanceDetails(
        display_name=instance_name,
        compartment_id=compartment_id,
        availability_domain=availability_domain.name,
        shape=shape.shape,
        metadata=instance_metadata,
        source_details=instance_source_via_image_details,
        create_vnic_details=create_vnic_details,
        shape_config={"memory-in-gbs": int(memory_in_gbs), "ocpus": int(ocpus) }
    )
    return launch_instance_details

def launch_instance(log,compute_client_composite_operations, launch_instance_details):
    launch_instance_response = compute_client_composite_operations.launch_instance_and_wait_for_state(
        launch_instance_details,
        wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_RUNNING]
    )
    instance = launch_instance_response.data

    log.info('Launched Instance: {}'.format(instance.id))
    return instance


def launch_compute(log,identity_client,compute_client,compute_client_composite_operations, json_object, namespace, bucket_name):
    try:
        #from config file
        compartment_id = read_json_object_property(log,json_object,"compute.compartment_id")
        availability_domain_name = read_json_object_property(log,json_object,"compute.placement.availability_domain_name")
        shape_name = read_json_object_property(log,json_object,"compute.shape.shape_name")
        memory_in_gbs = read_json_object_property(log,json_object,"compute.shape.memory_in_gbs")
        ocpus = read_json_object_property(log,json_object,"compute.shape.ocpus") 
        image_id = read_json_object_property(log,json_object,"compute.image_id")
        instance_name = read_json_object_property(log,json_object,"compute.instance_name")
        default_vnic_subnet_id = read_json_object_property(log,json_object,"compute.vnics.[0].subnet_id")
        ssh_public_key = read_json_object_property(log,json_object,"compute.ssh_public_key")
        cloud_init = read_json_object_property(log,json_object,"compute.cloud_init")

        # #from platform
        availability_domain = get_availability_domain(identity_client, compartment_id, availability_domain_name)
        shape = get_shape(compute_client, compartment_id, availability_domain,shape_name)
        launch_instance_details = get_launch_instance_details(compartment_id, availability_domain, shape, ocpus, memory_in_gbs, image_id, default_vnic_subnet_id,instance_name,cloud_init, ssh_public_key)

        # #launch
        instance = launch_instance(log,compute_client_composite_operations, launch_instance_details)
        return instance
    
    except Exception as e:
        log.error("error launching instance : {}".format(e))
        return []

def generate_numeric(log,template,prop,num_convention):
    try:
        base = read_json_object_property(log,template,prop)

        if "[]" not in base:
            return [base]

        padding = int(num_convention["padding"])
        start = int(num_convention["start"])
        stop = int(num_convention["stop"])+1
        step = int(num_convention["step"])
    except Exception as e:
        log.error("error generating numerical values : {}".format(e))
        return []
    
    return [base.replace("[]",str(num).rjust(padding, '0')) for num in range(start,stop,step)]



def read_json_object_property(log,json_object,param_path,default_value=None):
    try:
        path_parts = param_path.split(".")
        temp = json_object
        is_list = False
        for part in path_parts:
            if type(temp) is dict:
                temp = temp[part]
            else:
                if not is_list:
                    temp = getattr(temp, part)

            if is_list:
                temp = temp[int(part.replace("[","").replace("]",""))]
                is_list = False
            
            is_list = True if type(temp) is list else False
                
            if part == path_parts[-1]:
                log.debug("path : {}, type : {}, value : {}".format(param_path,type(temp),temp))
                return temp

    except Exception as e:
        log.error("error geting attribute {} for {} object : {}".format(param_path, type(json_object), e))
        return default_value



def write_json_object_property(log,json_object,param_path,value):
    try:
        path_parts = param_path.split(".")
        temp = json_object
        for part in path_parts:
            if type(temp) is dict:
                temp = temp[part]
            else:
                temp = getattr(temp, part)
            if part == path_parts[-2]:
                temp[path_parts[-1]] = value
                return json_object
    except Exception as e:
        log.error("error writing attribute {} for {} object : {}".format(param_path, type(json_object), e))
        return None


#generates array of names
def generate(log, template):
    names = []
    
    try:
        values = template["values"]
        for value in values:
            prop = value["prop"]
            convention = value["convention"]
            #numeric, todo named and random
            if not (convention.get('numerical') is None):
                names = names + generate_numeric(log,template,prop,convention.get('numerical'))          

    except Exception as e:
        log.error("error reading values to generate : {}".format(e))

    #empty return
    if len(names) == 0:
        return template["template"]
    
    #one by one return
    position = 0
    while position < len(names):
        yield write_json_object_property(log,template,prop,names[position])["template"]
        position = position + 1
    #return [write_json_object_property(log,template,prop,name)["template"] for name in names]


def generate_from_template(log,object_storage_client,json_object,namespace, bucket_name):
    for template in json_object:
        for generated in generate(log, template):
            log.info("generated : {}".format(generated))
            object_name = str(dt.now().strftime("%Y%m%d-%H%M-")) + ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + "-compute.json"
            object_content = json.dumps({"compute": generated})
            log.info("object_name : {}".format(object_name))
            put_object_response = write_objectstorage_object_content(log, object_storage_client, object_content, object_name, namespace, bucket_name)


def handler(ctx, data: io.BytesIO=None):
    log = logging.getLogger()
    log.info("Executing function code")
    
    #get event information
    try:
        body = json.loads(data.getvalue())
        object_name = body["data"]["resourceName"]
        bucket_name = body["data"]["additionalDetails"]["bucketName"]
        namespace = body["data"]["additionalDetails"]["namespace"]

        log.info("object_name : {}".format(object_name))
        log.info("bucket_name : {}".format(bucket_name))
        log.info("namespace : {}".format(namespace))

    except Exception as e:
        log.error("error reading object-storage event : {}".format(e))
        return respond()

    #auth objects
    signer = oci.auth.signers.get_resource_principals_signer()
    object_storage_client = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(compute_client)

    #read new object
    object_file_content = read_objectstorage_object_content(log,object_storage_client,namespace, bucket_name, object_name)
    if not object_file_content:
        return respond()
    try:
        json_object = json.loads(object_file_content)
    except Exception as e:
        log.error("error reading json file : {}".format(e))
        return respond()

    # {} is a single object
    if type(json_object) is dict:
        launch_compute(log,identity_client,compute_client,compute_client_composite_operations, json_object, namespace, bucket_name)
        return respond()
    
    # [{}] or [{},{},...] is a multi template of compute to create
    if type(json_object) is list:
        generate_from_template(log,object_storage_client,json_object,namespace, bucket_name)
        return respond()

    return respond()
