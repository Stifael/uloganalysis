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
TOPICS_REQUIRED = []


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


def get_vehiclestatus_from_file(f):
    """
    return dataframe and ulog for topics
    """

    ulog = pyulog.ULog(f, TOPICS_REQUIRED)

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


# def main():
# args = parser.parse_args()
# check_directory(args.filename)

# with PdfPages("px4_vehicle_status.pdf") as pdf:

#     df, ulog = get_vehiclestatus_from_file(args.filename)
#     if df is None:
#         print("Required topics not present")
#         return
