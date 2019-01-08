"""
Get general ulog info
"""
import pyulog
import numpy as np
import datetime


def get_ulog(filepath, topics):

    ulog = pyulog.ULog(filepath, topics)

    if not ulog.data_list:
        print("\033[93m" + "Not a single desired topic present" + "\033[0m")
        return None

    tmp = topics.copy()

    for topic in ulog.data_list:
        if topic.name in tmp:
            idx = tmp.index(topic.name)
            tmp.pop(idx)

    if len(tmp) > 0:
        print(
            "\033[93m"
            + "The following topics do not exist in the provided ulog file: "
            + "\033[0m"
        )
        print(tmp)
        return None

    return ulog


def get_starttime(ulog):
    m1, s1 = divmod(int(ulog.start_timestamp / 1e6), 60)
    h1, m1 = divmod(m1, 60)
    return "{:d}:{:02d}:{:02d}".format(h1, m1, s1)


def get_duration(ulog):
    m2, s2 = divmod(
        int((ulog.last_timestamp - ulog.start_timestamp) / 1e6), 60
    )
    h2, m2 = divmod(m2, 60)
    return "{:d}:{:02d}:{:02d}".format(h2, m2, s2)


def get_date(ulog):
    gps_data = ulog.get_dataset("vehicle_gps_position")
    indices = np.nonzero(gps_data.data["time_utc_usec"])
    if len(indices[0]) > 0:
        return datetime.datetime.fromtimestamp(
            gps_data.data["time_utc_usec"][0] / 1000000
        )
    else:
        return None


def get_param(ulog, parameter_name, default):
    if parameter_name in ulog.initial_parameters.keys():
        return ulog.initial_parameters[parameter_name]
    else:
        return default


def add_param(ulog, parameter_name, dataframe):
    dataframe["parameter_name"] = get_param(ulog, parameter_name, 0)
    if len(ulog.changed_parameters) > 0:
        for time, name, value in ulog.changed_parameters:
            if name == parameter_name:
                dataframe[dataframe[parameter_name]]
