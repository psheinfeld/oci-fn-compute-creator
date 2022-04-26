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

VOLUME_PLACEMENT = "volume.placement"
VOLUME_COMPARTMENT = "volume.compartment_id"
VOLUME_DISPLAY_NAME = "volume.display_name"
VOLUME_AD = "volume.placement.availability_domain_name"
VOLUME_SIZE = "volume.size_in_gbs"
VOLUME_VPU = "volume.vpus_per_gb"
VOLUME_AUTOTUNE = "volume.is_auto_tune_enabled"

OS_JOBS_PREFIX = "jobs"