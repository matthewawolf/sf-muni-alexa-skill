from flask import Flask
from flask_ask import Ask, request, session, question, statement, context, delegate
from geopy import geocoders
from findStops import *
import requests
import os
import logging

app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger('flask_ask').setLevel(logging.DEBUG)



@ask.launch
def launch():
    return question("Hello, What route and direction do you want to know about? For example, you can say Alexa, ask SF Muni when is the next 38 inbound?")


def logIFTT(event_type, value1, value2, value3):
    webhook_key = os.environ.get('IFTTT_WEBHOOK_KEY')
    if not webhook_key:
        return

    headers = {'Content-Type': 'application/json'}
    data = '{"value1":"' + str(value1) + '","value2":"' + str(value2) + '","value3":"' + str(value3) + '"}'
    requests.post(
        'https://maker.ifttt.com/trigger/muni-' + event_type + 'request/with/key/' + webhook_key,
        headers=headers, data=data)


def get_dialog_state:
    return session['dialogState']

def get_mins(arrival_mins):
    place = 0
    minutes = ''

    if type(arrival_mins) == int:
        if arrival_mins < 1:
            minutes += "less than one minute,  "
            place += 1
        else:
            minutes = arrival_mins
    else:
        for a in arrival_mins:
            if a < 1:
                minutes += "less than one minute,  "
                place += 1
            else:
                if place == len(arrival_mins) - 2:
                    minutes += str(a) + ' . and '
                    place += 1
                elif place == len(arrival_mins) - 1:
                    minutes += str(a) + ' '
                    place += 1
                else:
                    minutes += str(a) + ' . '
                    place += 1
    return minutes

# Prompts the user for the route and the direction
def update_slots(slot_type):

    if slot_type == 'route':
        text = ' I didn\'t get that, what was the route?'
        slot = 'routes'
    elif slot_type == 'direction':
        text = 'Is that inbound or outbound?'
        slot = 'directions'




@ask.intent('GetTime', mapping={"direction": "directions", "route": "routes"})
def gettime(route, direction):
    messages = []
    mins = []
    destinations = []
    arrival_mins = []
    messages_text = ''
    mins_str = ''
    multi_directions = False

    # Preserve the original request logging when a private webhook key is configured.
    logIFTT('request', route, direction, 'raw input')


    if direction is None:
        print 'direction is none'
        info = route.split(" ")
        route = info[0]
        if info[1].startswith('in'):
            direction = 'inbound'
        elif info[1].startswith('out'):
            direction = 'outbound'
        else:
            return question(' The route is ' + route + ' but I can\'t determine the direction.')
            dialog_state = get_dialog_state()
            if dialog_state != "COMPLETED":
                return delegate(speech=None)


            update_slots('direction')
        # An Alternative here is to create an array, and use a while loop until the array has only two values
            # Where the first is the route and the second one I can run fuzzywuzzy on.



    # Make sure that both a route AND a direction are sent. Since sometimes they end up conflated, ask for both
    #if (route is None or route == '') or (direction is None or direction == ''):
    #    update_slots('route')
    #    update_slots('direction')
    #    logIFTT('request', route, direction, 'updated slots')
    #    print 'The new route is ' + route
    #    print 'The new direction is ' + direction



    # If the above works, this is no longer needed
    # if type(route) is None or route == '':
    #    print 'Route is none'
    #    return question('You need both a route and a direction to get Muni predictions. Please try again.')
    #if type(direction) is None or direction == '':
    #    print 'Direction is none'
    #    return question('You need both a route and a direction to get Muni predictions, Please try again')

    # Error handling from speech input when alexa hears the wrong thing (e.g. 'in bound' instead of 'inbound')
    #if direction.strip().startswith('in'):
    #    direction = 'inbound'
    #elif direction.strip().startswith('out'):
    #    direction = 'outbound'



    # GET ADDRESS
    try:
        url = "https://api.amazonalexa.com/v1/devices/{}/settings/address".format(context.System.device.deviceId)
        try:
            token = context.System.user.permissions.consentToken
        except AttributeError:
            return question('There was an issue getting your address. Please meke sure you have your address in your Alexa app and have enabled permissions for the skill')
            print 'An AttributeError has occured'
        header = {'Accept': 'application/json', 'Authorization': 'Bearer {}'.format(token)}
        address = requests.get(url, headers=header)
        if address.status_code == 200:
            address = address.json()
    except TypeError:
        return question('You must enable permissions for this skill to retrieve your location from the Alexa app on your mobile device ')
        print 'A TypeError has occurred'


    # If there is no Address Setup in the users App
    if address['addressLine1'] is None or address['addressLine1'] == '':
        print 'The user has not entered the full address'
        return statement('This skill requires an address to be set up in your Alexa App. To add an address, open the Alexa app on your phone, go to settings, and edit your device location.')

    # GET COORDINATES
    g = geocoders.GoogleV3(api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))
    address = "{}, {}, {}".format(address['addressLine1'].encode('utf-8'), address['city'].encode('utf-8'), address['postalCode'].encode('utf-8'))
    coordinates = g.geocode(address, timeout=10)
    # GET STOP ID
    #  Find the nearest stop for those coordinates and the specified route/direction
    closest_stop = get_closest_stop(route, direction, (coordinates.latitude, coordinates.longitude))

    if closest_stop[0] is None or closest_stop[1] is None or closest_stop[0] == '' or closest_stop[1] == '' or closest_stop == 'KeyError':
        return question('Im Sorry, please try again and request both your route and direction. Also make sure your address is set up on your device.')
        dialog_state = get_dialog_state()
        if dialog_state != "COMPLETED":
            return delegate(speech=None)

    stop_id = closest_stop[0]
    cross_streets = closest_stop[1]

    # OLD LOGIC: used for cross streets given but no address/coords given
    '''
    # Add logic for all combinations - maybe just handle this by for any NONE information reprompt for it?
    # Location + Route + Direction
    # Location + Route (Add reprompt, inbound, outbound or both)
    # Location + Direction (add reprompt for route or 'all')
    # Streets + Route + Direction
    # Streets + Route  (Add reprompt, inbound, outbound or both)
    # Streets + Direction (add reprompt for route or 'all')
    # Route + Directions
    # Directions (add reprompt for route or 'all')
    # Route (Add reprompt, inbound, outbound or both)
    # None

    # FOR LOGGING
    if type(route) is None:
        print 'Route is None'
    elif type(direction) is None:
        print 'Direction is None'
    elif type(streets) is None:
        print 'Streets is None'


    # Get the route
    if route is not None:
        route = str(route)
        # Error handling from speech input where alexa sometimes conflates the route and direction.
        if route.strip().endswith('inbound'):
            route = route.replace('inbound', '')
            direction = 'inbound'
        elif route.strip().endswith('indown'):
            route = route.replace('indown', '')
            direction = 'inbound'
        elif route.strip().endswith('outbound'):
            route = route.replace('outbound', '')
            direction = 'outbound'
        elif route.strip().endswith('outdown'):
            route = route.replace('outdown', '')
            direction = 'outbound'


        # Error handling from speech input when alexa hears the wrong thing (extra spaces)
        if route.strip().endswith('indown'):
            route = route.replace('indown', '')
            direction = 'inbound'
        elif route.strip().endswith('outdown'):
            route = route.replace('outdown', '')
            direction = 'outbound'

    print str(route)

    # Get the direction
    if direction is not None:
        direction = str(direction).strip()
        if direction.lower() == 'indown':
            direction = 'inbound'
        elif direction.lower() == 'outdown':
            direction == 'outbound'
    print str(direction)

    # Get the stop_id
    if streets is not None:
        streets = str(streets)
        stop_id = get_stop_id(str(route).upper(), direction, streets)
        print str(stop_id)

        if stop_id is None:
            streets_list = str(streets).replace(' streets', '').lower().split()
            no_stop_streets = ''
            for s in streets_list:
                no_stop_streets += s + ' and '

            return statement('I\'m sorry, I couldn\'t find the stop for ' + no_stop_streets + ', please try again')
    '''

    # Get the JSON response with the next buses for the stop
    r = requests.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&terse&a=sf-muni&r=' + route.upper() + '&s=' + stop_id)
    predictions = r.json()

    # Check to see if there are predictions for the request
    for k in predictions['predictions']:
        if k == 'dirTitleBecauseNoPredictions':
            return statement("I'm sorry. There are no predictions for the " + route.upper() + ' ' + direction + " from " + cross_streets + " at this time. Please try again later.")
            break
        elif k == "Error":
            return statement("I'm sorry. There was an error getting your information. Please try again later.")
            break

    # Get the title of the route and a list of all of the arrival predictions.
    try:
        # Check to see if there is more than one destination on this line
        # If there are multiple destinations, this will be a dictionary
        if isinstance(predictions['predictions']['direction'][0], dict):
            multi_directions = True
            for d in predictions['predictions']['direction']:
                destinations.append(d['title'])
                try:
                    if isinstance(d['prediction'][0], dict):
                        for p in d['prediction']:
                            m, s = divmod(int(p['seconds']), 60)
                            mins.append(m)
                        arrival_mins.append(mins[:])
                        mins[:] = []
                except KeyError:
                    m, s = divmod(int(d['prediction']['seconds']), 60)
                    arrival_mins.append(m)
    # If there are not multiple destinations, get the predictions for the single destination
    except KeyError:
        destinations.append(predictions['predictions']['direction']['title'])
        try:
            if isinstance(predictions['predictions']['direction']['prediction'][0], dict):
                for p in predictions['predictions']['direction']['prediction']:
                    m, s = divmod(int(p['seconds']), 60)
                    mins.append(m)
                arrival_mins.append(mins[:])
                mins[:] = []
        except KeyError:
            m, s = divmod(int(predictions['predictions']['direction']['prediction']['seconds']), 60)
            arrival_mins.append(m)

    # Build the output string
    mins_str = 'The closest stop is ' + cross_streets + '. '
    if multi_directions:
        mins_str += 'There are ' + str(len(destinations)) + ' destinations for the ' + str(route).upper() + ' ' + direction + ' at this stop. '
    for d in range(len(destinations)):
        mins_str += ' The next ' + str(route).upper() + ' ' + str(destinations[d]) + ' will arrive in ' + str(get_mins(arrival_mins[d])) + ' minutes.'

    # If there are messages, get the important
    if len(messages) > 0:
        try:
            # If there is more than one message it creates a list of messages. Otherwise it must be treated like a dict.
            if isinstance(predictions['predictions']['message'][0], dict):
                for m in predictions['predictions']['message'][0]:
                    if predictions['predictions']['message'][m]['priority'] == 'Normal' or \
                                    predictions['predictions']['message'][m]['priority'] == 'High':
                        messages.append(str(predictions['predictions']['message'][m]['text']))
        except KeyError, m:
            if predictions['predictions']['message']['priority'] == 'Normal' or predictions['predictions']['message']['priority'] == 'High':
                messages.append(str(predictions['predictions']['message']['text']))

        # Build the string for the messages, if there are any
        if len(messages) == 0:
            messages_text = ''
        elif len(messages) > 0:
            if len(messages) > 1:
                isare = 'are'
                msg = 'messages'
            else:
                isare = 'is'
                msg = 'message'
            messages_text = ' There ' + isare + ' also ' + str(len(messages)) + ' ' + msg + '. '

            # Go through the messages and attach each one
            for m in messages:
                messages_text += m + '. '

    output = mins_str + messages_text
    card_output = str(output).replace('.', ',')
    return statement(output).simple_card(title='SF Muni Predictions', content=card_output)


@ask.intent('AMAZON.HelpIntent')
def help():
    return question('Welcome to SF Muni. You can get the upcoming bus times by asking. When is the next, route number, direction. For example you can say: Alexa, ask SF Muni when is the next 5R inbound. The skill will automatically find the closest stop to you. You will need your address setup under settings in your Alexa App. To add your address, open the Alexa app on your device, go to settings, and edit the device location ')


@ask.session_ended
def session_ended():
    return '', 200


if __name__ == '__main__':
    app.run()
