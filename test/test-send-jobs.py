#!/usr/bin/env python3

import requests
import json, jsonpickle
import os
import sys
import base64
import glob


#
# Use localhost & port 5000 if not specified by environment variable REST
#
REST = sys.argv[1]
if not REST:
    raise Exception("No host ip argument passed")

##
# The following routine makes a JSON REST query of the specified type
# and if a successful JSON reply is made, it pretty-prints the reply
##

def mkReq(reqmethod, endpoint, data, verbose=True):
    print(f"Response to http://{REST}/{endpoint} request is {type(data)}")
    jsonData = jsonpickle.encode(data)
    if verbose and data != None:
        print(f"Make request http://{REST}/{endpoint} with json {data.keys()}")
    response = reqmethod(f"http://{REST}/{endpoint}", data=jsonData, headers={'Content-type': 'application/json'})
    if response.status_code == 200:
        return response
    else:
        print( f"ERROR: response code is {response.status_code}, raw response is {response.text}")
        return response.text


for video in glob.glob("data/inputs/*.mp4"):
    print(f"Sending request for {video}")
    mkReq(requests.post, "api/jobs", data={ "video": base64.b64encode( open(video, "rb").read() ).decode('utf-8')})
    queue = mkReq(requests.get, "api/queue", data=None)
    status = mkReq(requests.get, "api/status", data=None)
    print(f"Job Queue Contains: {queue.json}")
    print(f"Job Status Hash Contains: {status}")

sys.exit(0)
