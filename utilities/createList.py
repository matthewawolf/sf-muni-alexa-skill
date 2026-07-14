# This file was used to make a list of unique street names

import csv
from collections import defaultdict
from pprint import pprint
import copy


stopsDict = {}
temp_outbound = {}  # defaultdict()
temp_inbound = {}   # defaultdict()
temp_dict = {}      # defaultdict()

locations = set()


'''
with open('w3.csv') as f:
    # Route	Stop	Direction	Street 1	Street 2	Street 3
    reader = csv.reader(f)
    for row in reader:
       locations.update(row)
'''


with open('stops.csv') as f:
#stop_id | stop_code |  stop_name |  stop_lat | stop_lon
    reader = csv.reader(f)
    for row in reader:
        locations.update(row)


    print locations






with open('ll.txt', 'wt') as out:
    for l in locations:
        pprint(l, stream=out)