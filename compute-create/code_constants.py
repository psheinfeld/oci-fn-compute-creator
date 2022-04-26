"""
logical flow:

template object : [{"values":[],"template":{}}, ...]

compute object : {"compute":{}} 

instance object : {"instance":{}} , name instance "...ocid..."
volume object : {"volume":{}} 
vnic object : {"vnic":{}}

"""

OCID_PREFIX = "ocid1."

COLLISION_RESISTENCE_LEVEL = 10

COMPUTE = "compute"
INSTANCE = "instance"
VOLUME = "volume"
VNIC = "vnic"

COMPUTE_JO_INSTANCE_NAME = "compute.instance_name"
COMPUTE_JO_VOLUMES = "compute.volumes"
COMPUTE_JO_AD = "compute.placement.availability_domain_name"
COMPUTE_JO_COMPARTMENT = "compute.compartment_id"
COMPUTE_JO_PLACEMENT = "compute.placement"


FREEFORM_TAG_JOB_KEY  = "job_path"
FREEFORM_TAG_ATTACH_TYPE_KEY  = "attach_type"

VOLUME_PLACEMENT = "volume.placement"
VOLUME_COMPARTMENT = "volume.compartment_id"
VOLUME_DISPLAY_NAME = "volume.display_name"
VOLUME_AD = "volume.placement.availability_domain_name"
VOLUME_SIZE = "volume.size_in_gbs"
VOLUME_VPU = "volume.vpus_per_gb"
VOLUME_AUTOTUNE = "volume.is_auto_tune_enabled"
VOLUME_ATTACH_TYPE = "volume.attach_type"

OS_JOBS_PREFIX = "jobs"