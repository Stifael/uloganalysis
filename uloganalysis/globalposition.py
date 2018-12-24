import pandas as pd
import numpy as np
import argparse
import os
import pyulog
from uloganalysis import ulogconv as conv
from uloganalysis import mathpandas as mpd
from uloganalysis import plotwrapper as pltw

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

parser = argparse.ArgumentParser(
    description="Script to process global position"
)
parser.add_argument("filename", metavar="file.ulg", help="ulog file")

# To run this script, the following topics are required
TOPICS_REQUIRED = [
    "vehicle_global_position",
    "vehicle_local_position",
    "position_setpoint_triplet",
]


def check_directory(filename):
    if os.path.isfile(filename):
        base, ext = os.path.splitext(filename)
        if ext.lower() not in (".ulg"):
            parser.error("File is not .ulg file")
        else:
            return
    else:
        parser.error("File does not exist")


def get_global_state_setpoint_from_file(f):
    """
    return dataframe and ulog for global position and triplet
    """
    ulog = pyulog.ULog(f, TOPICS_REQUIRED)

    if ulog is None:
        return None, None

    pandadict = conv.createPandaDict(ulog)
    df = conv.merge(pandadict, method="zero")
    # change to seconds
    df.timestamp = (df.timestamp - df.timestamp[0]) * 1e-6

    # only consider dataframe where global reference is provide
    # xy_global is True if xy_glboal == 1, False if xy_global == 0
    df = df[
        (df["T_vehicle_local_position_0__F_xy_global"] > 0.1)
        & (  # xy_global needs to be true
            df["T_vehicle_local_position_0__F_z_global"] > 0.1
        )
        & (  # z_global needs to be true
            df["T_vehicle_global_position_0__F_lat"] >= -80
        )
        & (  # lat needs to be larger than -80
            df["T_vehicle_global_position_0__F_lat"] <= 80
        )
        & (  # lat needs to be smaller than 84
            df["T_vehicle_global_position_0__F_lon"] >= -180
        )
        & (  # lon needs to be larger than -180
            df["T_vehicle_global_position_0__F_lon"] <= 180
        )
        & (  # lon needs to be smaller than 180
            df["T_position_setpoint_triplet_0__F_current_lat"] >= -80
        )
        & (  # lat needs to be larger than -80
            df["T_position_setpoint_triplet_0__F_current_lat"] <= 80
        )
        & (  # lat needs to be smaller than 84
            df["T_position_setpoint_triplet_0__F_current_lon"] >= -180
        )
        & (  # lon needs to be larger than -180
            df["T_position_setpoint_triplet_0__F_current_lat"] <= 180
        )
    ]  # lon needs to be smaller than 180

    return df, ulog


def add_UTM_from_global_target_setpoin(df):

    easting, northing, zone = mpd.series_UTM(
        df["T_position_setpoint_triplet_0__F_current_lat"],
        df["T_position_setpoint_triplet_0__F_current_lon"],
    )

    df["T_position_setpoint_triplet_0__NF_current_easting"] = easting.values
    df["T_position_setpoint_triplet_0__NF_current_northing"] = northing.values
    df["T_position_setpoint_triplet_0__NF_current_zone"] = zone.values


def add_UTM_from_reference(df):
    easting, northing, zone = mpd.series_UTM(
        df["T_vehicle_local_position_0__F_ref_lat"],
        df["T_vehicle_local_position_0__F_ref_lon"],
    )

    df["T_vehicle_local_position_0__NF_ref_easting"] = easting.values
    df["T_vehicle_local_position_0__NF_ref_northing"] = northing.values
    df["T_vehicle_local_position_0__NF_ref_zone"] = zone.values


def add_UTM_setpoint_relative_to_reference(df):
    if "T_position_setpoint_triplet_0__NF_current_easting" not in df:
        add_UTM_from_global_target_setpoin(df)
        print("sp nt present")

    if "T_vehicle_local_position_0__NF_ref_easting" not in df:
        add_UTM_from_reference(df)
        print("ref not present")

    df["T_position_setpoint_triplet_0__NF_current_easting_relative"] = (
        df["T_position_setpoint_triplet_0__NF_current_easting"].values
        - df["T_vehicle_local_position_0__NF_ref_easting"]
    )
    df["T_position_setpoint_triplet_0__NF_current_northing_relative"] = (
        df["T_position_setpoint_triplet_0__NF_current_northing"].values
        - df["T_vehicle_local_position_0__NF_ref_northing"]
    )


def add_UTM_from_global_position(df):
    easting, northing, zone = mpd.series_UTM(
        df["T_vehicle_global_position_0__F_lat"],
        df["T_vehicle_global_position_0__F_lon"],
    )

    df["T_vehicle_global_position_0__NF_easting"] = easting.values
    df["T_vehicle_global_position_0__NF_northing"] = northing.values
    df["T_vehicle_global_position_0__NF_zone"] = zone.values
    # df["T_vehicle_global_position_0__NF_letter"] = letter.values


def add_UTM_position_relative_to_reference(df):
    if "T_vehicle_global_position_0__NF_easting" not in df:
        add_UTM_from_global_position(df)

    df["T_vehicle_global_position_0__NF_easting_relative"] = (
        df["T_vehicle_global_position_0__NF_easting"].values
        - df["T_vehicle_local_position_0__NF_ref_easting"]
    )
    df["T_vehicle_global_position_0__NF_northing_relative"] = (
        df["T_vehicle_global_position_0__NF_northing"].values
        - df["T_vehicle_local_position_0__NF_ref_northing"]
    )


def main():
    args = parser.parse_args()
    check_directory(args.filename)

    with PdfPages("px4_global_to_local.pdf") as pdf:

        df, ulog = get_global_state_setpoint_from_file(args.filename)

        if df is None:
            print("Topics are not present!")
            return

        add_UTM_from_global_target_setpoin(df)
        add_UTM_from_reference(df)
        add_UTM_setpoint_relative_to_reference(df)
        add_UTM_from_global_position(df)
        add_UTM_position_relative_to_reference(df)

        ## global path with setpoint ins UTM
        plt.figure(0, figsize=(20, 13))
        df_tmp = df[
            [
                "T_vehicle_global_position_0__NF_easting_relative",
                "T_vehicle_global_position_0__NF_northing_relative",
            ]
        ].copy()

        plt.plot(
            df["T_position_setpoint_triplet_0__NF_current_easting_relative"],
            df["T_position_setpoint_triplet_0__NF_current_northing_relative"],
            "rD--",
            label="Waypoint",
        )
        plt.plot(
            df["T_vehicle_global_position_0__NF_easting_relative"],
            df["T_vehicle_global_position_0__NF_northing_relative"],
            "g",
            label="Estimation",
        )

        group_easting = df.groupby(
            ["T_position_setpoint_triplet_0__NF_current_easting_relative"]
        )
        waypoints = {"time": [], "east": [], "north": []}
        for g, d in group_easting:
            waypoints["east"].append(g)
            waypoints["time"].append(d["timestamp"][0])
            waypoints["north"].append(
                d[
                    "T_position_setpoint_triplet_0__NF_current_northing_relative"
                ][0]
            )

        waypoints = pd.DataFrame(data=waypoints)
        waypoints = waypoints.sort_values(by="time")
        waypoints = waypoints.reset_index(drop=True)
        plt.text(
            waypoints["east"].iloc[0] + 0.4,
            waypoints["north"].iloc[0],
            "Start",
            color="black",
            fontsize=18,
        )
        plt.legend()
        plt.title("UTM trajectories")
        plt.grid()
        pdf.savefig()
        plt.close(0)

        ## easting and northing setpoints and state
        plt.figure(1, figsize=(20, 13))
        df_tmp = df[
            [
                "timestamp",
                "T_position_setpoint_triplet_0__NF_current_easting_relative",
                "T_position_setpoint_triplet_0__NF_current_northing_relative",
                "T_vehicle_global_position_0__NF_easting_relative",
                "T_vehicle_global_position_0__NF_northing_relative",
            ]
        ].copy()
        df_tmp.plot(x="timestamp", linewidth=0.8)
        pltw.plot_time_series(df_tmp, plt)
        plt.title("UTM setpoint/state-trajectory")
        plt.ylabel("meters")
        plt.xlabel("meters")
        pdf.savefig()
        plt.close(1)
