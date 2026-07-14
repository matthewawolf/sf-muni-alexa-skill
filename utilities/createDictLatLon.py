# This file was used to create a map of route to direction and then all of the stops (with corresponding streets) within that direction.



import csv
from collections import defaultdict
from pprint import pprint
import copy


stopsDict = {}
temp_outbound = {}  # defaultdict()
temp_inbound = {}   # defaultdict()
temp_dict = {}      # defaultdict()
counter = 0

### BUGS BUGS BUGS ###
# Not finding some of the stops (e.g. 31BX Stop 4347 Outbound


with open('maybe_working.csv') as f:
    # Route     Direction   Street1     Street2      Stop ID     Lat     Lon
    reader = csv.reader(f)
    next(f)
    current_route = ''
    for row in reader:
        # Get the route for the first row
        if current_route == '':
            current_route = str(row[0]).strip()
            counter += 1

        # If it is not the same route, start a new nested dictionary
        if current_route != str(row[0]).strip():
            # Create one dictionary composed of both inbound and outbound stops
            temp_dict.update({'inbound': temp_inbound})
            temp_dict.update({'outbound': temp_outbound})
            stopsDict[current_route] = copy.deepcopy(temp_dict) # deepcopy copies the actual dictionary not just the reference
            counter += 1

            # Clear everything for the next route
            temp_dict.clear()
            temp_outbound.clear()
            temp_inbound.clear()
            current_route = str(row[0]).strip()

        # If we are still processing the same route, get the direction and streets and add to the appropriate temp
        # dictionary. We need this because some stops can be BOTH inbound and outbound making the keys not unique
        else:
            streets = [str(row[2]).strip(), str(row[3]).strip(), str(row[5]), str(row[6])]
            if row[1] == '0': # outbound
                temp_outbound.update({str(row[4]).strip(): streets},)
            elif row[1] == '1': # inbound
                temp_inbound.update({str(row[4]).strip(): streets},)

pprint(stopsDict)

del temp_dict
del temp_inbound
del temp_outbound
del streets
del row
del current_route


# Perform a checksum of the number of stops
# Loop through the entire dictionary and count the number of stops (not unique stops)
stopCount = 0
stopsList = []
dir = ''
for key in stopsDict.keys():
    for key_inner in stopsDict[key].keys():
        for k2 in stopsDict[key][key_inner].keys():
            if key_inner == 'inbound':
                dir = '1'
            elif key_inner == 'outbound':
                dir = '0'
            stopsList.append([key, dir, k2])


with open('outputll.txt', 'wt') as out:
    pprint(stopsDict, stream=out)
