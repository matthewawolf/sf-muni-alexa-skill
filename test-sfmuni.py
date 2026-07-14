from flask import Flask
from flask_ask import Ask, request, session, question, statement
import requests
import logging
import time
import json
import os
from findStops import *



def get_alexa_location():
    URL =  "https://api.amazonalexa.com/v1/devices/{DEVICE_ID}/settings/address".format(context.System.device.deviceId)
    TOKEN =  context.System.user.permissions.consentToken
    HEADER = {'Accept': 'application/json','Authorization': 'Bearer {}'.format(TOKEN)}
    r = requests.get(URL, headers=HEADER)
    if r.status_code == 200:
        return(r.json())


def logIFTT(event_type, value1, value2, value3):
    webhook_key = os.environ.get('IFTTT_WEBHOOK_KEY')
    if not webhook_key:
        return

    headers = {'Content-Type': 'application/json'}
    data = '{"value1":"' + str(value1) + '","value2":"' + str(value2) + '","value3":"' + str(value3) + '"}'
    requests.post(
        'https://maker.ifttt.com/trigger/muni-' + event_type + 'request/with/key/' + webhook_key,
        headers=headers, data=data)


# Build the string for the next arrivals
def getMins(arrivalMins):
    place = 0
    minutes = ''

    if type(arrivalMins) == int:
        if arrivalMins < 1:
            minutes += "less than one minute,  "
            place += 1
        else:
            minutes = arrivalMins
    else:
        for a in arrivalMins:
            if a < 1:
                minutes += "less than one minute,  "
                place += 1
            else:
                if place == len(arrivalMins) - 2:
                    minutes += str(a) + ' . and '
                    place += 1
                elif place == len(arrivalMins) - 1:
                    minutes += str(a) + ' '
                    place += 1
                else:
                    minutes += str(a) + ' . '
                    place += 1
    return minutes


def gettime(route, direction, streets):
    messages = []
    mins = []
    destinations = []
    arrivalMins = []
    messagesText = ''
    minsStr = ''
    multiDirections = False
    stop_id = ''

    logIFTT('request', route, direction, streets)

    # Get the route
    if route is not None:
        route = str(route)
        #Error hanbdling from speech input where alexa sometimes conflates the route and direction.
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
    print str(route)

    # Get the direction
    if direction is not None:
        direction = str(direction).strip()
        if direction.lower() == 'indown':
            direction = 'inbound'
        elif direction.lower() == 'outdown':
            direction == 'outbound'

    # Get the stop_id
    if streets is not None:
        streets = str(streets)
        stop_id = get_stop_id(str(route).upper(), direction, streets)
        if stop_id is None:
            streetsList = str(streets).replace(' streets', '').lower().split()
            noStopStreets = ''
            for s in streetsList:
                noStopStreets += s + ' and '

            logIFTT('fail', route, direction, streets)
            return statement('I\'m sorry, I couldn\'t find the stop for ' + noStopStreets +', please try again')


    # Get the JSON response with the next buses for the stop
    print ('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&terse&a=sf-muni&r=' + route.upper() + '&s=' + stop_id)
    r = requests.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&terse&a=sf-muni&r=' + route.upper() + '&s=' + stop_id)
    predictions = r.json()
    print predictions




    # Check to see if there are predictions for the rewquest
    for k in predictions['predictions']:
        if k =='dirTitleBecauseNoPredictions':
            return statement("I'm sorry. There are no predictions for the " + route.upper() + ' ' + direction + " from your stop at this time. Please try again later.")
            break
        elif k == "Error":
            return statement("I'm sorry. There was an error getting your information. Please try again later.")
            break





    # Get the title of the route and a list of all of the arrival predictions.
    try:
        # Check to see if there is more than one destination on this line
        # If there are multiple destinations, this will be a dictionary
        if isinstance(predictions['predictions']['direction'][0], dict):
            multiDirections = True
            for d in predictions['predictions']['direction']:
                destinations.append(d['title'])
                try:
                    if isinstance(d['prediction'][0],dict):
                        for p in d['prediction']:
                            m, s = divmod(int(p['seconds']), 60)
                            mins.append(m)
                        arrivalMins.append(mins[:])
                        mins[:] = []
                except KeyError, e:
                    m, s = divmod(int(d['prediction']['seconds']), 60)
                    arrivalMins.append(m)
    # If there are not multiple destinations, get the predictions for the single destination
    except KeyError, e:
        destinations.append(predictions['predictions']['direction']['title'])
        try:
            if isinstance(predictions['predictions']['direction']['prediction'][0], dict):
                for p in predictions['predictions']['direction']['prediction']:
                    m, s = divmod(int(p['seconds']), 60)
                    mins.append(m)
                arrivalMins.append(mins[:])
                mins[:] = []
        except KeyError, e:
            m, s = divmod(int(predictions['predictions']['direction']['prediction']['seconds']), 60)
            arrivalMins.append(m)


    # Build the output string
    if multiDirections:
        minsStr = 'There are ' + str(len(destinations)) + ' destinations for the ' + str(route).upper() + ' ' + direction + ' at this stop. '
    for d in range(len(destinations)):
        minsStr += ' The next ' + str(route).upper() + ' ' + str(destinations[d]) + ' will arrive in ' + str(getMins(arrivalMins[d])) + ' minutes.'


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
            messagesText = ''
        elif len(messages) > 0:
            if len(messages) > 1:
                isare = 'are'
                msg = 'messages'
            else:
                isare = 'is'
                msg = 'message'
            messagesText = ' There ' + isare + ' also ' + str(len(messages)) + ' ' + msg + '. '

            # Go through the messages and attach each one
            for m in messages:
                messagesText += m + '. '


    logIFTT('success', route, direction, streets)

    output = minsStr + messagesText
    cardOutput = str(output).replace('.', ',')
    return statement(output).simple_card(title='SF Muni Predictions', content=cardOutput)



# Tests
#myTimes = gettime('10', 'outbound', 'washington buchanan')
myTimes = gettime('21', 'inbound', 'baker and hayes')
#myTimes = gettime('F', 'inbound', 'MARKET 7TH')
#myTimes = gettime('N', 'inbound', 'powell')
#myTimes = gettime('KT', 'outbound', 'embarcadero')
#print myTimes.render_response()



# Works for single not multiple destinations, keeping for documentation.
'''
if len(predictions['predictions']['direction']) > 2:  # This indicates that there is more than one destination.
    for d in len(predictions['predictions']['direction']):
        destinations.append(d['title'])
        for p in d['prediction']:
            m, s = divmod(int(p['seconds']), 60)
            mins.append(m)
        arrivalMins.append(mins)
else: # if there is only one destination
    destinations.append(predictions['predictions']['direction']['title'])
    for p in predictions['predictions']['direction']['prediction']:
        m, s = divmod(int(p['seconds']), 60)
        mins.append(m)
    arrivalMins.append(mins)
'''

# Old message builder that works.
'''
if len(predictions['predictions']['message']) > 0:
    for m in range(len(predictions['predictions']['message'])):
        try:
            if predictions['predictions']['message'][m]['priority'] == 'Normal' or \
                            predictions['predictions']['message'][m]['priority'] == 'High':
                messages.append(str(predictions['predictions']['message'][m]['text']))
        # Otherwise there is only one message
        except KeyError, e:
            if predictions['predictions']['message']['priority'] == 'Normal' or \
                            predictions['predictions']['message']['priority'] == 'High':
                    messages.append(str(predictions['predictions']['message']['text']))
'''

# New message builder that works
'''
# If there are messages, get the important ones
try:
    # If there is more than one message it creates a list of messages. Otherwise it must be treated like a dict.
    if isinstance(predictions['predictions']['message'][0], dict):
        for m in predictions['predictions']['message'][0]:
            if predictions['predictions']['message'][m]['priority'] == 'Normal' or predictions['predictions']['message'][m]['priority'] == 'High':
                messages.append(str(predictions['predictions']['message'][m]['text']))
except KeyError, m:
    if predictions['predictions']['message']['priority'] == 'Normal' or predictions['predictions']['message']['priority'] == 'High':
        messages.append(str(predictions['predictions']['message']['text']))

# Build the string for the messages, if there are any
if len(messages) == 0:
    messagesText = ''
elif len(messages) > 0:
    if len(messages) > 1:
        isare = 'are'
        msg = 'messages'
    else:
        isare = 'is'
        msg = 'message'
    messagesText = ' There ' + isare + ' also ' + str(len(messages)) + ' ' + msg + '. '

    # Go through the messages and attach each one
    for m in messages:
        messagesText += m + '. '
'''
