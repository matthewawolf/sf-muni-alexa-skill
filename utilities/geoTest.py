from geopy import geocoders, GoogleV3
import os


def get_coordinates():
    g = geocoders.GoogleV3(api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))
    address = "1 South Van Ness Avenue, San Francisco, California"
    coordinates = g.geocode(address)
    print(address)
    print(coordinates.latitude, coordinates.longitude)
    return [coordinates.latitude, coordinates.longitude]


place = get_coordinates()
