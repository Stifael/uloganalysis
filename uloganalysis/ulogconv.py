"""
Convert ulog file to different data structure
"""

import pyulog
import pandas as pd
import re


def createPandaDict(ULog):
    """
    Convert ulog to dictionary of topic based panda-dataframes.
    rename topic-name such that each topic starts with `T_` and ends with instance ID.
        i.e. vehicle_local_position and instance 0 -> T_vehicle_local_position_0
    rename topic-fields such that vector indicices are replaced with underline and each field stars
    with letter F for denoting fields
        i.e.: fieldmsg[0] -> F_fieldmsg_0; fieldmsg[1] -> F_fieldmsg_1
    """

    # column replacment
    col_rename = {"[": "_", "]": "", ".": "_"}
    col_rename_pattern = re.compile(
        r"(" + "|".join([re.escape(key) for key in col_rename.keys()]) + r")"
    )

    pandadict = {}
    for msg in ULog.data_list:
        msg_data = pd.DataFrame.from_dict(msg.data)
        msg_data.columns = [
            col_rename_pattern.sub(lambda x: col_rename[x.group()], col)
            for col in msg_data.columns
        ]
        ncol = {}
        for col in msg_data.columns:
            if col == "timestamp":
                ncol[col] = col
            else:
                ncol[col] = "F_" + col
        msg_data.rename(columns=ncol, inplace=True)
        msg_data.index = pd.TimedeltaIndex(
            msg_data["timestamp"] * 1e3, unit="ns"
        )
        pandadict["T_{:s}_{:d}".format(msg.name, msg.multi_id)] = msg_data

    return pandadict


def merge_asof(pandadict, on=None, direction=None):
    """
    uses pandadit merge_asof
    @params pandadict: dictionary of panda-dataframes
    @params on: Topic that defines timestamp
    @params direction: see pandas merge_asof
    """
    if on is None:
        raise IOError("Must pass a topic name to merg on")
    if direction is None:
        direction = "backwards"

    combineTopicFieldName(pandadict)
    m = pd.DataFrame(data=pandadict[on].timestamp, columns=["timestamp"])
    for topic in pandadict:
        m = pd.merge_asof(m, pandadict[topic], on="timestamp")
    m.index = pd.TimedeltaIndex(m.timestamp * 1e3, unit="ns")
    return m


def merge(pandadict, columns_zero_order_hold=None):
    """
    pandas merge method applied to pandadict
    @params pandadict: a dictionary of pandas dataframe
    @params column_zero_order_hold: by default merge will use linear
            interpolation. column_zero_order_hold specifies which messages
            of pandadict are interpolated with zero-order-hold method.
    """

    combineTopicFieldName(pandadict)
    skip = True
    for topic in pandadict:
        if skip:
            m = pandadict[topic]
            skip = False
        else:
            m = pd.merge_ordered(
                m, pandadict[topic], on="timestamp", how="outer"
            )
    m.index = pd.TimedeltaIndex(m.timestamp * 1e3, unit="ns")

    # apply zero order hold for some selected topics
    if columns_zero_order_hold is not None:
        m[columns_zero_order_hold] = m[columns_zero_order_hold].fillna(
            method="ffill"
        )

    # apply interpolation to the whole dataframe (only NaN values get interpolated,
    # thus the zero order hold values from before do not get overwritten)
    m = m.interpolate(method="linear")

    # drop all values that are still NaN
    m.dropna()

    return m


def combineTopicFieldName(pandadict):
    """
    Adds topic name to field-name except for timestamp field
    """
    for topic in pandadict.keys():
        ncol = {}
        for col in pandadict[topic].columns:
            if col == "timestamp":
                ncol[col] = col
            else:
                ncol[col] = topic + "__" + col
        pandadict[topic].rename(columns=ncol, inplace=True)
    return
