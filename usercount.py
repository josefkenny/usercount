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

# do_upload = True
# # Run without uploading, if specified
# if '--no-upload' in sys.argv:
#     do_upload = False

# do_fetch = True
# # Run without fetching, if specified
# if '--no-fetch' in sys.argv:
#     do_fetch = False

# # Check mastostats.csv exists, if not, create it
# if not os.path.isfile("mastostats.csv"):
#     print("mastostats.csv does not exist, creating it...")

#     # Create CSV header row
#     with open("mastostats.csv", "w") as myfile:
#         myfile.write("timestamp,usercount,tootscount\n")
#     myfile.close()

# Returns the parameter from the specified file


def get_parameter(parameter, file_path):
    # Check if secrets file exists
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


# # Load secrets from secrets file
# secrets_filepath = "secrets/secrets.txt"
# uc_client_id = get_parameter("uc_client_id",     secrets_filepath)
# uc_client_secret = get_parameter("uc_client_secret", secrets_filepath)
# uc_access_token = get_parameter("uc_access_token",  secrets_filepath)

# Load configuration from config file
config_filepath = "config.txt"
mastodon_hostname = get_parameter(
    "mastodon_hostname", config_filepath)  # E.g., mastodon.social

# # Initialise Mastodon API
# mastodon = Mastodon(
#     client_id=uc_client_id,
#     client_secret=uc_client_secret,
#     access_token=uc_access_token,
#     api_base_url='https://' + mastodon_hostname,
# )

# Initialise access headers
# headers = {'Authorization': 'Bearer %s' % uc_access_token}


###############################################################################
# GET THE DATA
###############################################################################

# Get current timestamp
ts = int(time.time())


# Get the /about/more page from the servers
# page = requests.get('https://' + mastodon_hostname + '/api/v1/instance')
# current_id = page.json()['stats']['user_count']
# num_toots = page.json()['stats']['status_count']

# print("Number of users: %s " % current_id)
# print("Number of toots: %s " % num_toots)

###############################################################################
# LOG THE DATA
###############################################################################

# Append to CSV file
# with open("mastostats.csv", "a") as myfile:
#     myfile.write(str(ts) + "," + str(current_id) + "," + str(num_toots) + "\n")

other_mastodon_hostname = get_parameter(
    "other_mastodon_hostname", config_filepath)
other_hosts = other_mastodon_hostname.split(',')
hosts_data = [('tooot.im', 'mastostats.csv')] + \
    [(h, "mastostats." + h + ".csv") for h in other_hosts]

# for h in other_hosts:
#     try:
#         h_page = requests.get('https://' + h + '/api/v1/instance')
#         h_current_id = h_page.json()['stats']['user_count']
#         h_num_toots = h_page.json()['stats']['status_count']
#         print(h, h_current_id, h_num_toots)
#         with open("mastostats." + h + ".csv", "a") as myfile:
#             myfile.write(str(ts) + "," + str(h_current_id) +
#                          "," + str(h_num_toots) + "\n")
#     except:
#         print("had an error on " + h)
###############################################################################
# WORK OUT THE TOOT TEXT
###############################################################################

# df = DataFrame(np.random.randn(5, 3), columns=['A', 'B', 'C'])


def stats_to_image(siteName, csvName, ax):
    print(siteName, csvName)
    df = pd.read_csv(csvName, names=['timestamp', 'usercount', 'tootscount'],
                     skiprows=1, index_col='timestamp', on_bad_lines='skip')
    df.index = pd.to_datetime(df.index, unit='s')
    fromtime = df.index.max() - dt.timedelta(days=7)
    df = df.resample('1h').ffill()
    for c in ['usercount', 'tootscount']:
        df[c + 'Deriv'] = df[c].diff()
    df = df[(df.index >= fromtime)]

    # ax = axs[i]
    ax3 = ax.twinx()
    ax3.spines['right'].set_position(('axes', 1.1))
    ax3.set_frame_on(True)
    ax3.patch.set_visible(False)
    # fig.subplots_adjust(right=0.75)

    df.usercount.plot(ax=ax, style='b-', xlabel='', ylabel=siteName)
    df.usercountDeriv.plot(ax=ax, style='r-', secondary_y=True, xlabel='')
    df.tootscountDeriv.plot(ax=ax3, style='g-', xlabel='')

    ax3.legend([ax.get_lines()[0], ax.right_ax.get_lines()[0], ax3.get_lines()[0]],
               ['usercount', 'usercountDeriv', 'tootscountDeriv'])
    # ax.set_title(siteName)


fig, axs = plt.subplots(int(len(hosts_data) / 2), 2,
                        constrained_layout=True)
for (i, (hostname, csvname)) in enumerate(hosts_data):
    stats_to_image(hostname, csvname, axs[int(i/2), i % 2])
plt.show()
exit()


# fig, ax = plt.subplots()
# ax3 = ax.twinx()
# ax3.spines['right'].set_position(('axes', 1.15))
# ax3.set_frame_on(True)
# ax3.patch.set_visible(False)
# fig.subplots_adjust(right=0.7)
# df.usercount.plot(ax=ax, legend=True)
# df.usercountDeriv.plot(ax=ax3, legend=True)
# df.tootscountDeriv.plot(ax=ax3, legend=True, secondary_y=True)
# print(df)
# print(df.diff())
# print(df.index.to_series().diff().dt.total_seconds())
# print(df['usercount'].diff() / df.index.to_series().diff().dt.total_seconds())
# (df['usercount'].diff() / df.index.to_series().diff().dt.total_seconds())[(df.index >= fromtime)].plot()
# (df['tootscount'].diff() / df.index.to_series().diff().dt.total_seconds())[(df.index >= fromtime)].plot(secondary_y=True)

dfh = df.resample('1h').mean().diff()
dfh = dfh[(dfh.index >= fromtime)]
df = df[(df.index >= fromtime)]
print(dfh)
# exit()

# fig, ax = plt.subplots()
# rspine = ax3.spines['right']
# rspine.set_position(('axes', 1.15))
# ax3.set_frame_on(True)
# ax3.patch.set_visible(False)
# fig.subplots_adjust(right=0.7)

# df.usercount.plot(ax=ax, style='b-')
# same ax as above since it's automatically added on the right
# dfh.usercount.plot(ax=ax, style='r-', secondary_y=True)
dfh.tootscount.plot(ax=df.usercount.plot(style='b-'),
                    style='g-', secondary_y=True)

# add legend --> take advantage of pandas providing us access
# to the line associated with the right part of the axis
# ax3.legend([ax.get_lines()[0],
#             ax.right_ax.get_lines()[0],
#             ax3.get_lines()[0]],
#         #    df.columns
#            # , bbox_to_anchor=(1.5, 0.5)
#            )
plt.show()
exit()


# df[:] = df[:].clip(0)
# df['tootscount'] = df['tootscount'].resample('1h') #.diff()
# print(df)
# print(df.resample('1h').mean()) #.diff())  # .diff()

dfh.plot(y='tootscount', secondary_y=True, ax=dfh.plot(y='usercount'))
plt.show()
exit()
df = df[(df.index >= df.index.max() - dt.timedelta(days=7))]

# pd.set_option('display.max.columns', None)
ax = df.plot(y='usercount')
df.plot(y='tootscount', secondary_y=True, ax=ax)
plt.show()
exit()

# Load CSV file
with open('mastostats.csv') as f:
    usercount_dict = [{k: int(v) for k, v in row.items()}
                      for row in csv.DictReader(f, skipinitialspace=True)]

# Returns the timestamp,usercount pair which is closest to the specified timestamp


def find_closest_timestamp(input_dict, seek_timestamp):
    a = []
    for item in input_dict:
        a.append(item['timestamp'])
    return input_dict[min(range(len(a)), key=lambda i: abs(a[i]-seek_timestamp))]


# Calculate difference in times
hourly_change_string = ""
daily_change_string = ""
weekly_change_string = ""

one_hour = 60 * 60
one_day = one_hour * 24
one_week = one_hour * 168

# Hourly change
if len(usercount_dict) > 2:
    one_hour_ago_ts = ts - one_hour
    one_hour_ago_val = find_closest_timestamp(usercount_dict, one_hour_ago_ts)
    hourly_change = current_id - one_hour_ago_val['usercount']
    print("Hourly change %s" % hourly_change)
    if hourly_change > 0:
        hourly_change_string = "+" + \
            format(hourly_change, ",d") + " in the last hour\n"

# Daily change
if len(usercount_dict) > 24:
    one_day_ago_ts = ts - one_day
    one_day_ago_val = find_closest_timestamp(usercount_dict, one_day_ago_ts)
    daily_change = current_id - one_day_ago_val['usercount']
    print("Daily change %s" % daily_change)
    if daily_change > 0:
        daily_change_string = "+" + \
            format(daily_change, ",d") + " in the last day\n"

# Weekly change
if len(usercount_dict) > 168:
    one_week_ago_ts = ts - one_week
    one_week_ago_val = find_closest_timestamp(usercount_dict, one_week_ago_ts)
    weekly_change = current_id - one_week_ago_val['usercount']
    print("Weekly change %s" % weekly_change)
    if weekly_change > 0:
        weekly_change_string = "+" + \
            format(weekly_change, ",d") + " in the last week\n"


###############################################################################
# CREATE AND UPLOAD THE CHART
###############################################################################

# Generate chart
call(["gnuplot", "generate.gnuplot"])
imagenames = ['graph.png']
for servername in other_hosts:
    graphname = "graph." + servername + ".png"
    csvname = "mastostats." + servername + ".csv"
    cmd = "servername=\'" + servername + "\'"
    cmd += ";graphname=\'" + graphname + "\'"
    cmd += ";csvname=\'" + csvname + "\'"
    call(["gnuplot", "-e", cmd, "generate.gnuplot"])
    imagenames.append(graphname)

images = [Image.open(x) for x in imagenames]
widths, heights = zip(*(i.size for i in images))

new_im = Image.new('RGB', (max(widths), sum(heights)))

y_offset = 0
for im in images:
    new_im.paste(im, (0, y_offset))
    y_offset += im.size[1]

new_im.save('graphall.png')

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
