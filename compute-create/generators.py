import random
import string

import code_constants as cc

def generate_random_string(length = cc.COLLISION_RESISTENCE_LEVEL):
    return "".join(
        random.choice(string.ascii_lowercase) for _ in range(length))

def generate_job_path(path=""):
    return cc.OS_JOBS_PREFIX + "/" + path + generate_random_string(cc.COLLISION_RESISTENCE_LEVEL*2) + "/"

def generate_numeric(log, base, numerical_convention):
    try:
        padding = int(numerical_convention["padding"])
        start = int(numerical_convention["start"])
        stop = int(numerical_convention["stop"]) + 1
        step = int(numerical_convention["step"])
    except Exception as e:
        log.error("error generating numerical values : {}".format(e))
        return []

    return [
        base.replace("[]",
                     str(num).rjust(padding, "0"))
        for num in range(start, stop, step)
    ]


def generate_random(log, base, random_convention):
    try:
        length = int(random_convention["len"])
        size = int(random_convention["size"])
        string_type = random_convention["type"]
    except Exception as e:
        print(e)
        return []

    return [
        base.replace(
            "[]", "".join(
                random.choice(string.ascii_lowercase) for _ in range(length)))
        for X in range(size)
    ]


def generate_named(log, base, names):
    return [base.replace("[]", x) for x in names]
