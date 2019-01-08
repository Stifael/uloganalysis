import pandas as pd
import numpy as np
import argparse
import os
import pyulog
from uloganalysis import ulogconv as conv
from uloganalysis import mathpandas as mpd
from uloganalysis import plotwrapper as pltw
from uloganalysis import loginfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


parser = argparse.ArgumentParser(description="Script to process attitude")
parser.add_argument("filename", metavar="file.ulg", help="ulog file")

# To run this scipt, the following topics are
TOPICS_REQUIRED = ["vehicle_local_position", "vehicle_local_position_setpoint"]


def check_directory(filename):
    if os.path.isfile(filename):
        base, ext = os.path.splitext(filename)
        if ext.lower() not in (".ulg"):
            parser.error("File is not .ulg file")
        else:
            return
    else:
        parser.error("File does not exist")


def get_required_topics():
    return TOPICS_REQUIRED


def get_position_state_setpoint_from_file(f):
    """
    return dataframe and ulog for position/setpoint topic
    """
    ulog = loginfo.get_ulog(f, TOPICS_REQUIRED)

    if ulog is None:
        return None, None

    pandadict = conv.createPandaDict(ulog)
    df = conv.merge(pandadict)
    # change to seconds
    df.timestamp = (df.timestamp - df.timestamp[0]) * 1e-6
    return df, ulog


def print_pdf(df, pdf, topic_1, topic_2, title, y_label, iterator):
    # desired and measured x position
    plt.figure(iterator, figsize=(20, 13))
    df_tmp = df[["timestamp", topic_1, topic_2]].copy()
    df_tmp.plot(x="timestamp", linewidth=0.8)
    pltw.plot_time_series(df_tmp, plt)
    plt.title(title)
    plt.ylabel(y_label)
    pdf.savefig()
    plt.close(iterator)


def add_horizontal_distance(df):
    abs_horizontal_dist = pd.Series(
        np.zeros(df.shape[0]),
        index=df["timestamp"],
        name="T_vehicle_local_position_0__NF_abs_horizontal_dist",
    )

    abs_horizontal_dist = mpd.series_pythagoras(
        df["T_vehicle_local_position_0__F_x"],
        df["T_vehicle_local_position_0__F_y"],
    )
    df[
        "T_vehicle_local_position_0__NF_abs_horizontal_dist"
    ] = abs_horizontal_dist.values


def main():
    args = parser.parse_args()
    check_directory(args.filename)

    with PdfPages("px4_position.pdf") as pdf:

        df, ulog = get_position_state_setpoint_from_file(args.filename)

        if df is None:
            print("Required topics not present")
            return

        add_horizontal_distance(df)

        # TODO: make print_pdf adapt to different numbers of messages
        # desired and measured x position
        print_pdf(
            df,
            pdf,
            "T_vehicle_local_position_0__F_x",
            "T_vehicle_local_position_setpoint_0__F_x",
            "x position",
            "meters",
            0,
        )

        # desired and measured y position
        print_pdf(
            df,
            pdf,
            "T_vehicle_local_position_0__F_y",
            "T_vehicle_local_position_setpoint_0__F_y",
            "y position",
            "meters",
            1,
        )

        # desired and measured z position
        print_pdf(
            df,
            pdf,
            "T_vehicle_local_position_0__F_z",
            "T_vehicle_local_position_setpoint_0__F_z",
            "z position",
            "meters",
            2,
        )

        # horizontal distance to home
        print_pdf(
            df,
            pdf,
            "T_vehicle_local_position_0__NF_abs_horizontal_dist",
            "T_vehicle_local_position_0__NF_abs_horizontal_dist",
            "absolute horizontal distance",
            "meters",
            3,
        )

        print("PDF was created")
