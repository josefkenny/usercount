#!/usr/bin/python

from six.moves import urllib
from datetime import datetime
from subprocess import call
from mastodon import Mastodon
import time
import threading
import csv
import os
import json
import time
import signal
import sys
import os.path        # For checking whether secrets file exists
import requests       # For doing the web stuff, dummy!

###############################################################################
# INITIALISATION
###############################################################################

do_upload = True
# Run without uploading, if specified
if '--no-upload' in sys.argv:
    do_upload = False

# Check mastostats.csv exists, if not, create it
if not os.path.isfile("mastostats.csv"):    
        print("mastostats.csv does not exist, creating it...")

        # Create CSV header row
        with open("mastostats.csv", "w") as myfile:
            myfile.write("timestamp,usercount,tootscount\n")
        myfile.close()

# Returns the parameter from the specified file
def get_parameter( parameter, file_path ):
    # Check if secrets file exists
    if not os.path.isfile(file_path):    
        print("File %s not found, exiting."%file_path)
        sys.exit(0)

    # Find parameter in file
    with open( file_path ) as f:
        for line in f:
            if line.startswith( parameter ):
                return line.replace(parameter + ":", "").strip()

    # Cannot find parameter, exit
    print(file_path + "  Missing parameter %s "%parameter)
    sys.exit(0)

# Load secrets from secrets file
secrets_filepath = "secrets/secrets.txt"
uc_client_id     = get_parameter("uc_client_id",     secrets_filepath)
uc_client_secret = get_parameter("uc_client_secret", secrets_filepath)
uc_access_token  = get_parameter("uc_access_token",  secrets_filepath)

# Load configuration from config file
config_filepath = "config.txt"
mastodon_hostname = get_parameter("mastodon_hostname", config_filepath) # E.g., mastodon.social

# Initialise Mastodon API
mastodon = Mastodon(
    client_id = uc_client_id,
    client_secret = uc_client_secret,
    access_token = uc_access_token,
    api_base_url = 'https://' + mastodon_hostname,
)

# Initialise access headers
headers={ 'Authorization': 'Bearer %s'%uc_access_token }

###############################################################################
# GET THE DATA
###############################################################################

# Get current timestamp
ts = int(time.time())

# Get the /about/more page from the server
page = requests.get('https://' + mastodon_hostname + '/about/more')

# We could use lxml's html parser, but that requires loads of packages to be
# installed, as it's all C bindings and stuff. So we're gonna do it in a
# really quick and horrible way! 

# Returns the substring of s which is between substring1 and substring2
def get_between(s, substring1, substring2):
    return s[(s.index(substring1)+len(substring1)):s.index(substring2)]

# Remove newlines to make our life easier
pagecontent = page.content.replace("\n", "")

# Get the number of users, removing commas
current_id = int( get_between(pagecontent, "Home to</span><strong>", "</strong><span>users").replace(",", ""))

# Get the number of toots, removing commas
num_toots = int (get_between(pagecontent, "Who authored</span><strong>", "</strong><span>statuses").replace(",", ""))

print("Number of users: %s "% current_id)
print("Number of toots: %s "% num_toots )

###############################################################################
# LOG THE DATA
###############################################################################

# Append to CSV file
with open("mastostats.csv", "a") as myfile:
    myfile.write(str(ts) + "," + str(current_id) + "," + str(num_toots) + "\n")

###############################################################################
# WORK OUT THE TOOT TEXT
###############################################################################

# Load CSV file
with open('mastostats.csv') as f:
    usercount_dict = [{k: int(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]

# Returns the timestamp,usercount pair which is closest to the specified timestamp
def find_closest_timestamp( input_dict, seek_timestamp ):
    a = []
    for item in input_dict:
        a.append( item['timestamp'] )
    return input_dict[ min(range(len(a)), key=lambda i: abs(a[i]-seek_timestamp)) ]

# Calculate difference in times
hourly_change_string = ""
daily_change_string  = ""
weekly_change_string = ""

one_hour = 60 * 60
one_day  = one_hour * 24
one_week = one_hour * 168

# Hourly change
if len(usercount_dict) > 2:
    one_hour_ago_ts = ts - one_hour
    one_hour_ago_val = find_closest_timestamp( usercount_dict, one_hour_ago_ts )
    hourly_change = current_id - one_hour_ago_val['usercount']
    print "Hourly change %s"%hourly_change
    if hourly_change > 0:
        hourly_change_string = "+" + format(hourly_change, ",d") + " in the last hour\n"

# Daily change
if len(usercount_dict) > 24:
    one_day_ago_ts = ts - one_day
    one_day_ago_val = find_closest_timestamp( usercount_dict, one_day_ago_ts )
    daily_change = current_id - one_day_ago_val['usercount']
    print "Daily change %s"%daily_change
    if daily_change > 0:
        daily_change_string = "+" + format(daily_change, ",d") + " in the last day\n"

# Weekly change
if len(usercount_dict) > 168:
    one_week_ago_ts = ts - one_week
    one_week_ago_val = find_closest_timestamp( usercount_dict, one_week_ago_ts )
    weekly_change = current_id - one_week_ago_val['usercount']
    print "Weekly change %s"%weekly_change
    if weekly_change > 0:
        weekly_change_string = "+" + format(weekly_change, ",d") + " in the last week\n"


###############################################################################
# CREATE AND UPLOAD THE CHART
###############################################################################

# Generate chart
call(["gnuplot", "generate.gnuplot"])


if do_upload:
    # Upload chart
    file_to_upload = 'graph.png'

    print "Uploading %s..."%file_to_upload
    media_dict = mastodon.media_post(file_to_upload,"image/png")

    print "Uploaded file, returned:"
    print str(media_dict)

    ###############################################################################
    # T  O  O  T !
    ###############################################################################

    toot_text = format(current_id, ",d") + " accounts \n"
    toot_text += hourly_change_string
    toot_text += daily_change_string
    toot_text += weekly_change_string

    print "Tooting..." 
    print toot_text

    mastodon.status_post(toot_text, in_reply_to_id=None, media_ids=[media_dict] )

    print "Successfully tooted!"
else:
    print("--no-upload specified, so not uploading anything")

