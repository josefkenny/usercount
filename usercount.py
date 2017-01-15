#!/usr/bin/python

import requests
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
import os.path      # For checking whether secrets file exists

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



# Load secrets from file, in format
# uc_client_id: "<Client ID>"
# uc_client_secret: "<Client Secret>"
# uc_access_token: "<Access Token>"

secrets_filepath = "secrets/secrets.txt"

uc_client_id     = get_parameter("uc_client_id",     secrets_filepath)
uc_client_secret = get_parameter("uc_client_secret", secrets_filepath)
uc_access_token  = get_parameter("uc_access_token",  secrets_filepath)

# Load configuration from file

config_filepath = "config.txt"

mastodon_hostname = get_parameter("mastodon_hostname", config_filepath) # E.g., mastodon.social


# Initialise mastodon API
mastodon = Mastodon(
    client_id = uc_client_id,
    client_secret = uc_client_secret,
    access_token = uc_access_token
)

# Initialise access headers
headers={ 'Authorization': 'Bearer %s'%uc_access_token }

requestDelay = 3

steps = 0

stepsize = 250


# Returns the timestamp,usercount pair which is closest to the specified timestamp
def find_closest_timestamp( input_dict, seek_timestamp ):
    a = []
    for item in input_dict:
        a.append( item['timestamp'] )

    return input_dict[ min(range(len(a)), key=lambda i: abs(a[i]-seek_timestamp)) ]



# Returns true if the specified user_id exists
def user_exists( user_id ):
    print("Checking %s"%user_id)
    url = 'https://' + mastodon_hostname + '/api/v1/accounts/' + str(user_id)

    # Loop until we get a non-error result (including server & connection errors)
    while True:
        try:
            time.sleep(requestDelay)
            response = requests.get(url, headers=headers)
            print("Response: \n\n" + response.text)
            break
        except requests.exceptions.RequestException as e:
            print("Error getting user_id %s"%user_id + " exception: " + e)
        
    if ("Record not found" not in response.text):
        return True
    return False

# Load 'highest known ID' from the last line of usercount.csv
# timestamp,usercount
with open('usercount.csv') as f:
  last = None
  for line in (line for line in f if line.rstrip('\n')):
    last = line

highest_known_id = int( last.split(",",1)[1] )

current_id = highest_known_id

while stepsize > 1:
    steps += 1
    print "Testing user %d"%(current_id + stepsize)
    if user_exists( current_id  + stepsize ):
        current_id = current_id + stepsize
        print "User exists at %d"%current_id
        print ""
        continue
    else:
        stepsize = stepsize / 2
        print "No user at %d"%(current_id + stepsize)
        print "Changing stepsize to %d"%stepsize
        print ""
        continue



ts = int(time.time())

print "Timestamp: %d"%ts
print "Newest mastodon.social user: %d"%current_id
print "Found the highest user in %d steps"%steps


# Append to CSV file
with open("usercount.csv", "a") as myfile:
    myfile.write(str(ts) + "," + str(current_id) + "\n")

# Load CSV file
with open('usercount.csv') as f:
    usercount_dict = [{k: int(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]


# Calculate difference in times
hourly_change_string = ""
daily_change_string = ""
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


# Generate chart
call(["gnuplot", "generate.gnuplot"])


# Upload chart
file_to_upload = 'graph.png'
print "Uploading %s..."%file_to_upload
media_dict = mastodon.media_post(file_to_upload)

print "Uploaded file, returned:"
print str(media_dict)

# Finally, do the toot
#
# 16,560 mastodon.social accounts
# +12 in the last hour
# +563 in the last 24 hours
# 
# (plus image URL)

toot_text = format(current_id, ",d") + " accounts \n"
toot_text += hourly_change_string
toot_text += daily_change_string
toot_text += weekly_change_string

print "Tooting..." 
print toot_text

mastodon.status_post(toot_text, in_reply_to_id=None, media_ids=[media_dict] )

print "Successfully tooted!"
