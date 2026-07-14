import csv
import pprint
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from data import *




def get_stop_id_fuzzy(route, direction, streets):
    # Create a list to search through, but remove street types for improved fuzzy matching
    # Will need a loop to take more of this out
    crossStreets = str(streets).replace(' st', '').lower().split()

    for s in stopsDict[route][direction]:
        match = 0
        for i in range(len(stopsDict[route][direction][s])):
            for c in crossStreets:
                ratio = fuzz.partial_token_set_ratio(str(c).lower(), str(stopsDict[route][direction][s][i]).lower())
                print str(c).lower() + ' compared to ' + str(stopsDict[route][direction][s][i]).lower() + ' has a ratio of ' + str(ratio)
                if fuzz.partial_token_set_ratio(str(c).lower(), str(stopsDict[route][direction][s][i]).lower()) >= 80:
                    match += 1
        if match >= 2:
            return str(s)
            break
        else:
            print 'match not found\n'
            match = 0


myStop = get_stop_id_fuzzy('N', 'inbound', ' 4th king street')
print 'Your stop is ' + str(myStop)





'''
# BASIS #
stop_id = 0
for x in stopMap:
    stop = stopMap[x]
    if stop[0] == route and stop[1] == direction and stop[2] == streets:
        stop_id = x
    print 'stop'
'''
