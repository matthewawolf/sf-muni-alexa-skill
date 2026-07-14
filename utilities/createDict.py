# This file was used to create a map of route to direction and then all of the stops (with corresponding streets) within that direction.



import csv
from collections import defaultdict
from pprint import pprint
import copy


stopsDict = {}
temp_outbound = {}  # defaultdict()
temp_inbound = {}   # defaultdict()
temp_dict = {}      # defaultdict()

### BUGS BUGS BUGS ###
# Not finding some of the stops (e.g. 31BX Stop 4347 Outbound


with open('almost_clean_modified2.csv') as f:
    # Route	Stop	Direction	Street 1	Street 2	Street 3
    reader = csv.reader(f)
    next(f)
    current_route = ''
    for row in reader:
        # Get the route for the first row
        if current_route == '':
            current_route = str(row[0]).strip()

        # If it is not the same route, start a new nested dictionary
        if current_route != row[0]:
            # Create one dictionary composed of both inbound and outbound stops
            temp_dict.update({'inbound': temp_inbound})
            temp_dict.update({'outbound': temp_outbound})
            stopsDict[current_route] = copy.deepcopy(temp_dict) # deepcopy copies the actual dictionary not just the reference

            # Clear everything for the next route
            temp_dict.clear()
            temp_outbound.clear()
            temp_inbound.clear()
            current_route = str(row[0]).strip()

        # If we are still processing the same route, get the direction and streets and add to the appropriate temp
        # dictionary. We need this because some stops can be BOTH inbound and outbound making the keys not unique
        elif current_route == row[0]:
            if row[5] == '':
                streets = [str(row[3]).strip(), str(row[4]).strip()]
            else:
                streets = [str(row[3]).strip(), str(row[4]).strip(), str(row[5]).strip()]

            if row[2] == '0': # outbound
                temp_outbound.update({row[1]: streets},)
            elif row[2] == '1': # inbound
                temp_inbound.update({row[1]: streets},)

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

# Find the stops that are missing, if any by comparing the checksum to the source file
sourceStops = []
with open('almost_clean_modified2.csv') as f:
    reader = csv.reader(f)
    next(f)
    for r in reader:
        sourceStops.append([r[0], r[2], r[1]])

deltas = []
for sl in stopsList:
    if sl not in sourceStops:
        deltas.append(sl)

with open('deltas.txt', 'wt') as out:
    pprint(sl, stream=out)



print "done"


# Write to a file
with open('output.txt', 'wt') as out:
    pprint(stopsDict, stream=out)




'''
# To make list of lists:
        streets = []
        if row[5] == '':
            streets = [str(row[3]).strip(), str(row[4]).strip()]
        else:
            streets = [str(row[3]).strip(), str(row[4]).strip(), str(row[5]).strip()]
        newRow = [str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip(), streets]
        print newRow
        stopsList.append(newRow)

'''