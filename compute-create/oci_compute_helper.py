import oci

def get_shape(compute_client, compartment_id, availability_domain, shape_name):
    list_shapes_response = oci.pagination.list_call_get_all_results(
        compute_client.list_shapes,
        compartment_id,
        availability_domain=availability_domain.name,
    )

    for shape in list_shapes_response.data:
        if shape_name.lower() == shape.shape.lower():
            return shape
    return None


def get_image_by_id(compute_client, image_id):
    try:
        image = (compute_client.get_image(image_id)).data
        return image
    except Exception as e:
        print(e)
        return None
