import math
import pandas as pd
import csv
import json
import time
import urllib2

housing = pd.read_csv("housingAddress.csv")
housing.describe()

#http://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&sensor=true
url = 'http://maps.googleapis.com/maps/api/geocode/json?latlng='
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

def getPostalCodeFromAddress(addressComponent):
    addresses = addressComponent['address_components']
    for i in range(len(addresses)):
        addr = addresses[i]
        if ('postal_code' in addr['types']):
            return addr['long_name']
    return None

def getRooftopPostalCode(results):
    for i in range(len(results)):
        geometry = results[i]['geometry']
        if (geometry['location_type'] == 'ROOFTOP'):
            return getPostalCodeFromAddress(results[i])
    return None

def getPostalCode(results):
    rooftopPostalCode = getRooftopPostalCode(results)
    if (rooftopPostalCode != None):
        return rooftopPostalCode
    for i in range(len(results)):
        postalCode = getPostalCodeFromAddress(results[i])
        if (postalCode != None):
            return postalCode
    return None



#Phoenix lat range 33.93  33.29 lon range -112.29 -111.92 37(Google maps)
#(lat, lon)->zipcode dictionary accurate up to 2 dec points
def getLatLonDictionary():
    dictionary = {}
    counterSoFar = 0
    for i in range(65):
        for j in range(38):
            postalCode = None
            lat = round(33.29 + i * .01, 2)
            lon = round(-112.29 + j * .01, 2)
            qry = str(lat) + ',' + str(lon)
            request = urllib2.Request(url + qry, None, headers)
            response = urllib2.urlopen(request).read()
            raw = json.loads(response)
            if raw['results']:
                postalCode = getPostalCode(raw['results'])
                dictionary[lat, lon] = postalCode
                print str(lat) + ',' + str(lon) + ',' + postalCode
            if (counterSoFar % 5 == 0):
                time.sleep(1)
            counterSoFar += 1
    return dictionary


dictionary = getLatLonDictionary()


zipcode = []
for i in range(len(housing.index)):
    lat = round(housing['GeoLat'][i], 2)
    lon = round(housing['GeoLon'][i], 2)
    try:
        zipcode.append(int(dictionary[lat, lon][:5]))
    except:
        zipcode.append(float('NaN'))

df = pd.DataFrame(zipcode, columns = ['ZipCode'])
housing['ZipCode'] = df['ZipCode']

housing.to_csv("inferred_zip.csv")


