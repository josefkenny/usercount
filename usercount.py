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
    # print(siteName, csvName)
    df = pd.read_csv(csvName, names=['timestamp', 'usercount', 'tootscount'],
                     skiprows=1, index_col='timestamp', on_bad_lines='skip')
    df.index = pd.to_datetime(df.index, unit='s')
    df = df.resample('1h').ffill()
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
    dfweek.usercount.plot(ax=ax, style='b-', xlabel='', ylabel=siteName)
    dfweek.usercountDeriv.plot(ax=ax, style='r-', secondary_y=True, xlabel='')
    dfweek.tootscountDeriv.plot(ax=ax3, style='g-', xlabel='')

    ax3.legend([ax.get_lines()[0], ax.right_ax.get_lines()[0], ax3.get_lines()[0]],
               ['Number of users', 'User hourly increase', 'Toots per hour'])

    s = str(int(df['tootscount'].iloc[-1])) + ' toots'
    lastUsers = int(df['usercount'].iloc[-1])
    s += '\n' + str(lastUsers) + ' accounts'
    s += ' +' + str(lastUsers - int(df['usercount'][oneWeek])) + ' last week'
    s += ' +' + str(lastUsers - int(df['usercount'][oneDay])) + ' last day'
    s += ' +' + str(lastUsers - int(df['usercount'][oneHour])) + ' last hour'
    return s


def generate_graph_and_msg(hosts_data, imageName):
    fig, axs = plt.subplots(int(len(hosts_data) / 2), 2,
                            constrained_layout=True)
    fig.set_size_inches(16, 12)
    msg = ''
    for (i, (hostname, csvname)) in enumerate(hosts_data):
        s = stats_to_image(hostname, csvname, axs[int(i/2), i % 2])
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

exit()

# # Load CSV file
# with open('mastostats.csv') as f:
#     usercount_dict = [{k: int(v) for k, v in row.items()}
#                       for row in csv.DictReader(f, skipinitialspace=True)]

# # Returns the timestamp,usercount pair which is closest to the specified timestamp


# def find_closest_timestamp(input_dict, seek_timestamp):
#     a = []
#     for item in input_dict:
#         a.append(item['timestamp'])
#     return input_dict[min(range(len(a)), key=lambda i: abs(a[i]-seek_timestamp))]


# # Calculate difference in times
# hourly_change_string = ""
# daily_change_string = ""
# weekly_change_string = ""

# one_hour = 60 * 60
# one_day = one_hour * 24
# one_week = one_hour * 168

# # Hourly change
# if len(usercount_dict) > 2:
#     one_hour_ago_ts = ts - one_hour
#     one_hour_ago_val = find_closest_timestamp(usercount_dict, one_hour_ago_ts)
#     hourly_change = current_id - one_hour_ago_val['usercount']
#     print("Hourly change %s" % hourly_change)
#     if hourly_change > 0:
#         hourly_change_string = "+" + \
#             format(hourly_change, ",d") + " in the last hour\n"

# # Daily change
# if len(usercount_dict) > 24:
#     one_day_ago_ts = ts - one_day
#     one_day_ago_val = find_closest_timestamp(usercount_dict, one_day_ago_ts)
#     daily_change = current_id - one_day_ago_val['usercount']
#     print("Daily change %s" % daily_change)
#     if daily_change > 0:
#         daily_change_string = "+" + \
#             format(daily_change, ",d") + " in the last day\n"

# # Weekly change
# if len(usercount_dict) > 168:
#     one_week_ago_ts = ts - one_week
#     one_week_ago_val = find_closest_timestamp(usercount_dict, one_week_ago_ts)
#     weekly_change = current_id - one_week_ago_val['usercount']
#     print("Weekly change %s" % weekly_change)
#     if weekly_change > 0:
#         weekly_change_string = "+" + \
#             format(weekly_change, ",d") + " in the last week\n"


###############################################################################
# CREATE AND UPLOAD THE CHART
###############################################################################

# Generate chart
# call(["gnuplot", "generate.gnuplot"])
# imagenames = ['graph.png']
# for servername in other_hosts:
#     graphname = "graph." + servername + ".png"
#     csvname = "mastostats." + servername + ".csv"
#     cmd = "servername=\'" + servername + "\'"
#     cmd += ";graphname=\'" + graphname + "\'"
#     cmd += ";csvname=\'" + csvname + "\'"
#     call(["gnuplot", "-e", cmd, "generate.gnuplot"])
#     imagenames.append(graphname)

# images = [Image.open(x) for x in imagenames]
# widths, heights = zip(*(i.size for i in images))

# new_im = Image.new('RGB', (max(widths), sum(heights)))

# y_offset = 0
# for im in images:
#     new_im.paste(im, (0, y_offset))
#     y_offset += im.size[1]

# new_im.save('graphall.png')

# if do_upload:
#     # Upload chart
#     file_to_upload = 'graphall.png'

#     print("Uploading %s..." % file_to_upload)
#     media_dict = mastodon.media_post(file_to_upload, "image/png")

#     print("Uploaded file, returned:")
#     print(str(media_dict))

#     ###############################################################################
#     # T  O  O  T !
#     ###############################################################################

#     toot_text = format(current_id, ",d") + " accounts \n"
#     toot_text += hourly_change_string
#     toot_text += daily_change_string
#     toot_text += weekly_change_string

#     print("Tooting...")
#     print(toot_text)

#     mastodon.status_post(toot_text, in_reply_to_id=None, media_ids=[
#                          media_dict], sensitive=False, visibility='unlisted')

#     print("Successfully tooted!")
# else:
#     print("--no-upload specified, so not uploading anything")
