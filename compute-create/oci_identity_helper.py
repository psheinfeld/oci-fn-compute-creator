import oci

def get_availability_domain(identity_client, compartment_id, availability_domain_name):
    list_availability_domains_response = oci.pagination.list_call_get_all_results(
        identity_client.list_availability_domains, compartment_id
    )
    for ad in list_availability_domains_response.data:
        if availability_domain_name.lower() in ad.name.lower():
            return ad
    return None