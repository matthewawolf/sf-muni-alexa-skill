from data import stopsDict
from data_lat_lon import stops_dict_coords
from difflib import SequenceMatcher
from geopy.distance import vincenty


def get_closest_stop(route, direction, coords):
    closest_distance = 100  # Start with a arbitrary high distance and then narrow down
    closest_stop = ''
    for s in stops_dict_coords[route][direction]:
        try:
            stop_coords = [stops_dict_coords[route][direction][s][2], stops_dict_coords[route][direction][s][3]]
            dist = vincenty(coords, stop_coords).miles
            if dist <= closest_distance:
                closest_distance = dist
                closest_stop = s
        except KeyError:
                return 'KeyError'

    return [closest_stop, str(stops_dict_coords[route][direction][closest_stop][0]) + ' and ' + str(stops_dict_coords[route][direction][closest_stop][1])]


# For Testing
'''
closest_stop = get_closest_stop('21', 'inbound', (37.77481, -122.440797))
if closest_stop[0] is None or closest_stop[1] is None or closest_stop[0] == '' or closest_stop[1] == '':
    print 'Im Sorry, please try again and request both your route and direction. Also make sure your address is set up on your device.'
else:
    print closest_stop
'''

# OLD LOGIC
'''
def get_stop_id(route, direction, streets):
    crossStreets = str(streets).replace(' streets', '').lower().split()
    print 'cross streets are: ' + str(crossStreets)

    for s in stopsDict[route][direction]:
        match = 0
        if len(stopsDict[route][direction][s]) == 1:
            minRatio= .50
            m = SequenceMatcher(None, str(streets).lower(), str(stopsDict[route][direction][s]).lower())
            ratio = m.ratio()
            print str(streets).lower() + ' compared to ' + str(stopsDict[route][direction][s]).lower() + ' has a ratio of ' + str(ratio)

            # Set a more strict ratio for station to avoid false positives
            if 'STATION' in streets.upper():
                minRatio = .80
            if ratio >= minRatio:
                match += 2
        elif len(stopsDict[route][direction][s]) > 1:
            minRatio = .70
            for i in range(len(stopsDict[route][direction][s])):
                for c in crossStreets:
                    m = SequenceMatcher(None, str(c).lower(), str(stopsDict[route][direction][s][i]).lower())
                    ratio = m.ratio()
                    print str(c).lower() + ' compared to ' + str(stopsDict[route][direction][s][i]).lower() + ' has a ratio of ' + str(ratio)
                    if ratio >= minRatio:
                        match += 1
        if (match >= 2) or match == (len(stopsDict[route][direction][s])):
            print "stop id is: " + str(s)
            return str(s)
            break
        else:
            match = 0




# For Testing
#stop = get_closest_stop('5R', 'inbound', [37.77481, -122.44079699999998])
#print stop



#stop = get_closest_stop('21', 'inbound', '37.77481, -122.440797')
#print stop

'''
