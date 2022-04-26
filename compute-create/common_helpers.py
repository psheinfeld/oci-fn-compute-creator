from datetime import datetime as dt


def get_daytime_str():
    return str(dt.now().strftime("%Y%m%d-%H%M%S"))