from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import random
import pandas as pd
import pymysql
import json
import random
from math import sin, cos, sqrt, atan2, radians, pi


"""Importing the key-value pairs of db credentials stored in secrets.json file in utils folder"""
with open("./utils/secrets.json") as f:
    df_json = json.load(f)['db_config']


@csrf_exempt
def populateSellerTable(request):
    """This function populates the property table.
       Latitude and Longitude are taken from a csv file whose reference is shared in a Readme file.
       Bedroom, Price and Bathroom field's values are generated randomly.
       Price is a multiple of 100 between $100 to $1100.
       Bedrooms and bathrooms can take any value between 1 to 11."""

    global df_json
    
    # Reference for csv: https://support.spatialkey.com/spatialkey-sample-csv-data/
    # Input CSV has 2 columns, latitude and longitude.
    df = pd.read_csv("/Users/AjayB/Desktop/latlong.csv")

    try: # Establish a database connection and populate the table.
        conn = pymysql.Connect(df_json["host"],df_json["user"],df_json["password"],df_json['db'], port=df_json.get('port', 3306))
        cursor = conn.cursor()
        for index, row in df.iterrows():
            latitude, longitude = row['latitude'], row['longitude']
            price = random.randint(1,11)*100
            bedrooms = random.randint(1,11)
            bathrooms = random.randint(1,11)
            sellerDataInsertQuery = "INSERT into sellerdata (latitude, longitude, price, bedrooms, bathrooms)  \
                            values ({}, {}, {}, {}, {});".format(latitude, longitude, price, bedrooms, bathrooms)
            print(sellerDataInsertQuery)
            cursor.execute(sellerDataInsertQuery)
        
        conn.commit()
        conn.close()

    except Exception as e:
        print(e)
        return JsonResponse({
            'success': False,
            'message': json.dumps(e)
            })

    return JsonResponse({
        'success': True,
        'message': 'Seller Table Populated successfully.'
        })


def matchDistance(latitudeDB, longitudeDB, latitudeUser, longitudeUser):
    """This function takes in latitude and longitude values and returns a score.
       score has min value 10 and max value 30 depending on distanceInMiles value"""
    radiusOfEarth = 6371.0

    dlon = abs(longitudeDB - longitudeUser)
    dlat = abs(latitudeDB - latitudeUser)

    a = sin(dlat / 2)**2 + cos(latitudeDB) * cos(latitudeUser) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distanceInMiles = radiusOfEarth * c * 0.621371

    if distanceInMiles <= 2:
        return 30
    elif distanceInMiles > 2 and distanceInMiles <= 4:
        return 25
    elif distanceInMiles > 4 and distanceInMiles <= 6:
        return 20
    elif distanceInMiles > 6 and distanceInMiles <= 8:
        return 15
    else:
        return 10

def matchBedroomCount(minBedrooms, maxBedrooms, dbBeds):
    """This function takes in bedroom values and returns a score.
       score has min value 10 and max value 20.
       Same function works for Bathroom as well"""
    if None in (minBedrooms, maxBedrooms):
        if minBedrooms is None:
            if abs(dbBeds - maxBedrooms) == 0:
                return 20
            elif abs(dbBeds - maxBedrooms) == 1:
                return 15
            else:
                return 10
        else:
            if abs(dbBeds - minBedrooms) == 0:
                return 20
            elif abs(dbBeds - minBedrooms) == 1:
                return 15
            else:
                return 10
    else:
        if dbBeds in range(minBedrooms, maxBedrooms + 1):
            return 20
        elif dbBeds in (minBedrooms - 1, maxBedrooms + 1):
            return 15
        else:
            return 10

def matchBudgetPercentage(minBudget, maxBudget, price):
    """This function takes in Price values and returns a score.
       score has min value 10 and max value 30."""
    if None in (minBudget, maxBudget):
        if minBudget is None:
            if abs(price - maxBudget)/price <= 0.1 :
                return 30
            elif abs(price - maxBudget)/price <= 0.15:
                return 20
            elif abs(price - maxBudget)/price <= 0.2:
                return 15
            else:
                return 10

        else:
            if abs(price - minBudget)/price <= 0.1 :
                return 30
            elif abs(price - minBudget)/price <= 0.15:
                return 20
            elif abs(price - minBudget)/price <= 0.2:
                return 15
            else:
                return 10
    else:
        if price in range(minBudget, maxBudget + 1):
            return 30

        elif price in range(int(minBudget - 0.1*minBudget), int(maxBudget + 0.1*maxBudget)):
            return 20
        elif price in range(int(minBudget - 0.2*minBudget), int(maxBudget + 0.2*maxBudget)):
            return 15
        else:
            return 10

@csrf_exempt
def searchResult(request):
    """This function takes in the inputs from user and returns the data of sellers in decreasing order of score"""
    
    conn = pymysql.Connect(df_json["host"],df_json["user"],df_json["password"],df_json['db'], port=df_json.get('port', 3306))
    cursor = conn.cursor()
    displayDictionary = {}
    properties = json.loads(request.body.decode())

    ''' Taking in the properties from the user into variable'''
    latitude = properties.get('latitude', None)
    longitude = properties.get('longitude', None)
    min_budget = properties.get('minBudget', None)
    max_budget = properties.get('maxBudget', None)
    min_bedrooms = properties.get('minBedrooms', None)
    max_bedrooms = properties.get('maxBedrooms', None)
    min_bathrooms = properties.get('minBathrooms', None)
    max_bathrooms = properties.get('maxBathrooms', None)
    radius = 16093
    radiusOfEarth = 6371*1000
    cursor = conn.cursor()

    # formula for calculating max latitude. Refernce: https://www.movable-type.co.uk/scripts/latlong-db.html
    min_latitude = latitude - radius/radiusOfEarth*180/pi
    max_latitude = latitude + radius/radiusOfEarth*180/pi
    min_longitude = longitude - radius/radiusOfEarth*180/pi / cos(latitude*pi/180)
    max_longitude = longitude + radius/radiusOfEarth*180/pi / cos(latitude*pi/180)

    # Budget preprocessing
    if None not in (min_budget, max_budget):
        min_budget_range = min_budget - 0.25*min_budget
        max_budget_range = max_budget + 0.25*max_budget

    elif min_budget is None:
        min_budget_range = max_budget - 0.25*max_budget
        max_budget_range = max_budget + 0.25*max_budget

    else:
        min_budget_range = min_budget - 0.25*min_budget
        max_budget_range = min_budget + 0.25*min_budget 

    # Bathroom preprocessing
    if None not in (min_bathrooms, max_bathrooms):
        min_bathroom_range = min_bathrooms - 2
        max_bathroom_range = max_bathrooms + 2

    elif min_bathrooms is None:
        min_bathroom_range = max_bathrooms - 2
        max_bathroom_range = max_bathrooms + 2

    else:
        min_bathroom_range = min_bathrooms - 2
        max_bathroom_range = min_bathrooms + 2

    # Bedroom preprocessing
    if None not in (min_bedrooms, max_bedrooms):
        min_bedroom_range = min_bedrooms - 2
        max_bedroom_range = max_bedrooms + 2

    elif min_bedrooms is None:
        min_bedroom_range = max_bedrooms - 2
        max_bedroom_range = max_bedrooms + 2

    else:
        min_bedroom_range = min_bedrooms - 2
        max_bedroom_range = min_bathrooms + 2

    # Query to filter the data
    cursor.execute(f"select * from sellerdata where \
                    latitude between {min_latitude} and {max_latitude} and \
                    longitude between {min_longitude} and {max_longitude} and \
                    price between {min_budget_range} and {max_budget_range} and \
                    bedrooms between {min_bedroom_range} and {max_bedroom_range} and \
                    bathrooms between {min_bathroom_range} and {max_bathroom_range};")


    allRows = cursor.fetchall()
    return_object = []

    # for eachRow 'i' among all the rows filetered from the table:
    # 'i' is a tuple. (immutable array of objects)
    for i in allRows:
        matchPercentage = 0
        distancePercentage = matchDistance(i[2], i[3], latitude, longitude)
        bedroomPercentage = matchBedroomCount(min_bedrooms, max_bedrooms, i[5])
        bathroomPercentage = matchBedroomCount(min_bathrooms, max_bathrooms, i[6])
        budgetPercentage = matchBudgetPercentage(min_budget, max_budget, int(i[4]))

        totalPercentage = distancePercentage + bedroomPercentage + bathroomPercentage + budgetPercentage
        if totalPercentage > 40:
            # Modify the tuple to append the score and then add into the dictionary
            i += (totalPercentage,)
            return_object.append(i)

    responseData = sorted(return_object, key = lambda x: x[-1], reverse=True)
    responseDict = {}
    for i in responseData:
        responseDict[i[0]] = {}
        responseDict[i[0]]['isAvailable'] = 'Yes' if i[1]==1 else 'No'
        responseDict[i[0]]['latitude'] = i[2]
        responseDict[i[0]]['longitude'] = i[3]
        responseDict[i[0]]['price'] = '$'+str(i[4])
        responseDict[i[0]]['bedrooms'] = i[5]
        responseDict[i[0]]['bathrooms'] = i[6]
        responseDict[i[0]]['matchPercentage'] = i[7]

    return JsonResponse({
        'success': True,
        'data': responseDict
        })


