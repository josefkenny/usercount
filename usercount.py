#!/usr/bin/python3
# -*- coding: utf-8 -*-

# from six.moves import urllib
from pandas import DataFrame
from datetime import datetime
from subprocess import call
from mastodon import Mastodon
import time
# import threading
import csv
import os
# import json
import time
# import signal
import sys
import os.path        # For checking whether secrets file exists
import requests       # For doing the web stuff, dummy!

from PIL import Image
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import math

###############################################################################
# INITIALISATION
###############################################################################


def get_parameter(parameter, file_path):
    # Returns the parameter from the specified file

    # Check if file exists
    if not os.path.isfile(file_path):
        print("File %s not found, exiting." % file_path)
        sys.exit(0)

    # Find parameter in file
    with open(file_path) as f:
        for line in f:
            if line.startswith(parameter):
                return line.replace(parameter + ":", "").strip()

    # Cannot find parameter, exit
    print(file_path + "  Missing parameter %s " % parameter)
    sys.exit(0)


###############################################################################
# LOG THE DATA
###############################################################################

def fetch_data_and_write(hosts_data):
    # Get current timestamp
    ts = int(time.time())

    for (i, (hostname, csvname)) in enumerate(hosts_data):
        try:
            stats = requests.get('https://' + hostname +
                                 '/api/v1/instance').json()
            user_count = stats['stats']['user_count']
            num_toots = stats['stats']['status_count']
            print(hostname, user_count, num_toots)
            with open(csvname, "a") as myfile:
                if myfile.tell() == 0:
                    myfile.write("timestamp,usercount,tootscount\n")
                s = str(ts) + "," + str(user_count) + "," + str(num_toots)
                myfile.write(s + "\n")
                # print(s)
        except:
            print("had an error on " + hostname)


###############################################################################
# WORK OUT THE TOOT TEXT
###############################################################################


def stats_to_image(siteName, csvName, ax):
    ax.yaxis.label.set_text(siteName)
    # print(siteName, csvName)
    df = pd.read_csv(csvName, names=['timestamp', 'usercount', 'tootscount'],
                     skiprows=1, index_col='timestamp', on_bad_lines='skip')
    df.index = pd.to_datetime(df.index, unit='s')
    df = df.resample('1h').mean().ffill()
    if (df.shape[0] == 0):
        return 'no data yet'

    s = str(int(df['tootscount'].iloc[-1])) + ' toots'
    lastUsers = int(df['usercount'].iloc[-1])
    s += ', ' + str(lastUsers) + ' accounts'

    if (df.shape[0] >= 2):
        oneWeek = df.index.max() - dt.timedelta(days=7)
        oneDay = df.index.max() - dt.timedelta(days=1)
        oneHour = df.index.max() - dt.timedelta(hours=1)
        for c in ['usercount', 'tootscount']:
            df[c + 'Deriv'] = df[c].diff()

        ax3 = ax.twinx()
        ax3.spines['right'].set_position(('axes', 1.1))
        ax3.set_frame_on(True)
        ax3.patch.set_visible(False)

        dfweek = df[(df.index >= oneWeek)]
        dfweek.usercount.plot(ax=ax, style='b-', xlabel='')
        dfweek.usercountDeriv.plot(
            ax=ax, style='r-', secondary_y=True, xlabel='')
        dfweek.tootscountDeriv.plot(ax=ax3, style='g-', xlabel='')

        ax3.legend([ax.get_lines()[0], ax.right_ax.get_lines()[0], ax3.get_lines()[0]],
                   ['Number of users', 'User hourly increase', 'Toots per hour'])

        try:
            s += ' +' + \
                str(lastUsers - int(df['usercount'][oneWeek])) + ' last week'
            s += ' +' + \
                str(lastUsers - int(df['usercount'][oneDay])) + ' last day'
            s += ' +' + \
                str(lastUsers - int(df['usercount'][oneHour])) + ' last hour'
        except:
            pass

    return s


def generate_graph_and_msg(hosts_data, imageName):
    fig, axs = plt.subplots(int(math.ceil(len(hosts_data) / 3)), 3,
                            constrained_layout=True)
    fig.set_size_inches(24, 12)
    msg = ''
    for (i, (hostname, csvname)) in enumerate(hosts_data):
        s = stats_to_image(hostname, csvname, axs[int(i/3), i % 3])
        msg += hostname + ': ' + s + '\n'
    plt.savefig(imageName, dpi=100)
    return msg


def create_stats_toot(toot_text, mastodon_hostname, file_to_upload):
    # Load secrets from secrets file
    secrets_filepath = "secrets/secrets.txt"
    uc_client_id = get_parameter("uc_client_id",     secrets_filepath)
    uc_client_secret = get_parameter("uc_client_secret", secrets_filepath)
    uc_access_token = get_parameter("uc_access_token",  secrets_filepath)

    # Initialise Mastodon API
    mastodon = Mastodon(
        client_id=uc_client_id,
        client_secret=uc_client_secret,
        access_token=uc_access_token,
        api_base_url='https://' + mastodon_hostname,
    )

    # Upload chart
    print("Uploading %s..." % file_to_upload)
    media_dict = mastodon.media_post(file_to_upload, "image/png")

    print("Uploaded file, returned:")
    print(str(media_dict))

    ###############################################################################
    # T  O  O  T !
    ###############################################################################
    print("Tooting...")
    print(toot_text)

    mastodon.status_post(
        toot_text,
        in_reply_to_id=None,
        media_ids=[media_dict],
        sensitive=False,
        visibility='unlisted')

    print("Successfully tooted!")


# Load configuration from config file
config_filepath = "config.txt"
mastodon_hostname = get_parameter(
    "mastodon_hostname", config_filepath)  # E.g., mastodon.social

host_names_str = get_parameter("other_mastodon_hostname", config_filepath)
other_hosts = host_names_str.split(',')
hosts_data = [(mastodon_hostname, 'mastostats.csv')]
hosts_data += [(h, "mastostats." + h + ".csv") for h in other_hosts]


if '--no-fetch' in sys.argv:
    print("--no-fetch specified, so not fetching data from servers")
else:
    fetch_data_and_write(hosts_data)

msg = generate_graph_and_msg(hosts_data, 'graph.png')
print(msg)

if '--no-upload' in sys.argv:
    print("--no-upload specified, so not upload stats toot to server")
else:
    create_stats_toot(msg, mastodon_hostname, 'graph.png')
