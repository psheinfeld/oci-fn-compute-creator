def read_json_first_key(log, json_object):
    try:
        return (list(json_object.keys()))[0]
    except Exception as e:
        log.error("error reading first key : {}".format(e))


def read_json_object_property(log,
                              json_object,
                              param_path,
                              default_value=None):
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
                temp = temp[int(part.replace("[", "").replace("]", ""))]
                is_list = False

            is_list = True if type(temp) is list else False

            if part == path_parts[-1]:
                # log.debug(
                #     "path : {}, type : {}, value : {}".format(
                #         param_path, type(temp), temp
                #     )
                # )
                return temp

    except Exception as e:
        log.error("error geting attribute {} for {} object : {}".format(
            param_path, type(json_object), e))
        return default_value


def write_json_object_property(log, json_object, param_path, value):
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
        log.error("error writing attribute {} for {} object : {}".format(
            param_path, type(json_object), e))
        return None
