def read_objectstorage_object_content(log, client, namespace, bucket_name, object_name):

    try:
        log.info(
            "attempting to read {} from {} in {}".format(
                object_name, bucket_name, namespace
            )
        )
        object_data = client.get_object(namespace, bucket_name, object_name)
        if object_data.status == 200:
            log.info("{} from {} received".format(object_name, bucket_name))
            return object_data.data.text
    except Exception as e:
        log.error("error reading object from object-storage : {}".format(e))
    return None


def write_objectstorage_object_content(
    log, client, object_content, object_name, namespace, bucket_name
):
    try:
        log.info(
            "attempting to write {} to {} in {}".format(
                object_name, bucket_name, namespace
            )
        )
        put_object_response = client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name,
            put_object_body=object_content,
        )
        return put_object_response
    except Exception as e:
        log.error("error writing object to object-storage : {}".format(e))
    return None


def delete_objectstorage_object(log, client, namespace, bucket_name, object_name):
    try:
        log.info(
            "attempting to delete {} from {} in {}".format(
                object_name, bucket_name, namespace
            )
        )
        object_data = client.delete_object(namespace, bucket_name, object_name)
        if object_data.status == 200:
            log.info("{} from {} deleted".format(object_name, bucket_name))
            return True
    except Exception as e:
        log.error("error deleting object from object-storage : {}".format(e))
    return False