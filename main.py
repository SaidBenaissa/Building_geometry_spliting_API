from array import array
# from distutils.command.build import build
# from distutils.command.build_clib import build_clib
from importlib.metadata import requires
from operator import truediv
from typing import Any
from flask import Flask
from flask import request
from flask_restful import Resource, Api, reqparse
from typing_extensions import Required
import gspread
import json
import numpy as np


app = Flask(__name__)
api = Api(app)

data = ''


# Connects to google sheets API 
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
sa = gspread.service_account('credentials.json', scope)
sh = sa.open("output_final")
wks = sh.worksheet("Sheet1")

# Creates method definition the column names in the google sheet
def createColNames():
    wks.update('A1', 'ObjectID')
    wks.update('B1', 'ObjectType')
    wks.update('C1', 'Data')
    wks.update('D1', 'Plateaus')


# Creates row names for google sheet (CreatColNames() call)
createColNames()

id = wks.acell('E1').value

# Counter auto-increments ID for grabbing object by ID
def increaseID():
    id = int(wks.acell('E1').value)
    id = id + 1
    wks.update('E1', id)
    return id

# Creates new limit line on google sheet
class NewLimitObject:

    def __init__(self, data, id):
        self.id = id
        self.data = data
        # Uploads values to google sheet
        wks.update('A' + id, id)
        wks.update('B' + id, 'Building Limit')
        wks.update('C' + id, data)

# Creates new plateau line on google sheet
class NewPlateauObject:

    def __init__(self, plateau, plateauData, id):
        self.id = id
        self.data = data
        # uploads values to google sheet
        wks.update('A' + id, id)
        wks.update('B' + id, 'Plateau')
        wks.update('C' + id, plateauData)
        wks.update('D' + id, plateau)

# Verifies provided Data - makes sure that building limits and height plateaus as well as the indidvidual object type is 'polygon'
def checkInput(data):
    build_temp = []
    height_temp = []
    build_area = 0
    height_area = 0

    valid = 0
    # This first for loop checks if the keys ‘building limits’ as well as ‘height plateaus’ exist in the data that has been input.
    for item in data.keys():
        if item != 'building_limits' and item != 'height_plateaus':
            # Checks if 'building limits' and 'height_plateaus' keys exist
            valid = 1
            break
        else:
            valid = 0

    # This part of the code checks if the type of the input is a collection of features for both, building limits and height plateaus
    if valid == 0:
        if data['building_limits']['type'] == 'FeatureCollection' and data['height_plateaus']['type'] == 'FeatureCollection':
            # Checks if both inputs are feature collections
            pass  # valid data like valid =0
        else:
            valid = 2

        buildLen = len(data['building_limits']['features'])
        # print(buildLen)
        heightLen = len(data['height_plateaus']['features'])
        if buildLen != heightLen:
            # Checks if height_plateaus and building_limits have the same amount of data points because they are not equal - need to much up
            valid = 3
        else:
            # As said on the task theBlimits and HeitghPlateaus have on the site.
            # The next part retrieves all individual coordinates and stores them in a temporary array.
            #  At the end the sum is calculated and compared between height plateaus and building limit.
            # (calculates total area of height plateaus and building limits and checks if they are equal)
            for items in data['building_limits']['features']:
                for items2 in items['geometry']['coordinates']:
                    for items3 in items2:
                        build_area = build_area + (items3[0] + items3[1])
                        build_temp.append(items3[0])
                        build_temp.append(items3[1])

            for items in data['height_plateaus']['features']:
                for items2 in items['geometry']['coordinates']:
                    for items3 in items2:
                        height_area = height_area + (items3[0] + items3[1])
                        height_temp.append(items3[0])
                        height_temp.append(items3[1])

        # logs
        # print(build_temp)
        # print("------------")
        # print(height_temp)

        if height_area != build_area:
            # Checks of building limit area matches height plateau area
            valid = 4

        # This following method checks for gaps by comparing the values within the 2 coordinate arrays.
        elif height_area == build_area:
            # Checks for gaps or building limit exceedings
            if not np.array_equal(build_temp, height_temp):
                valid = 5

    return valid

# We the have two methods that extract all building limits as well as all height plateaus.
# At the end of this function a new object is created With the object creation the data is being written to the google sheet
# Extracts data from json and creates NewPlateauObject if exist
def createPlateaus(data):
    plateauToImport = data['height_plateaus']['features']
    lenPlateauToImport = len(data['height_plateaus']['features'])
    #  plateaus = getPlateaus(data)
    for items in range(lenPlateauToImport):
        id = increaseID()
        plateaus = getPlateaus(data)  # old
        plateaus = plateaus[items]
        # plateauData = plateauToImport[items]
        plateauData = plateauToImport[items]['geometry']['coordinates']
        # this line used Google API for writing data on googlesheet try not used a lot to avoid api quota limit
        # Uncomment the next link for local data test
        NewPlateauObject(str(plateaus), str(plateauData), str(id))

# Extracts data from json and creates NewLimitObject on Google Sheet
def createLimits(data):
    limitsToImport = data['building_limits']['features']
    lenBuildingToImport = len(data['building_limits']['features'])
    for items in range(lenBuildingToImport):
        id = increaseID()
        # limitData = limitsToImport[items]
        limitData = limitsToImport[items]['geometry']['coordinates']
        # This line used Google API for writing buildingLimits data on googlesheet try not used a lot to avoid api quota limit
        # Uncomment the next link for local data test
        NewLimitObject(str(limitData), str(id))

# Extracts data from json and creates HeightPlateaus on Google Sheet 
def getPlateaus(data):
    elevations = []
    for i in range(len(data['height_plateaus']['features'])):
        x = data['height_plateaus']['features'][i]['properties']['elevation']
        elevations.append(x)
    return elevations


def newInput(data):
    # checkInput return the value `valid` that represent error type or pass
    result = checkInput(data)

    # The result of "valid" is then returned to ‚newInput‘ and interpreted accordingly to the value it returned.
    # Based on this the json data is then either uploaded or an error is returned to the user
    if result == 1:
        return 'Key(s) Missing! Building limit or height Plateau key is missing'
    elif result == 2:
        return 'The input Type is required to be a Feature Collection'
    elif result == 3:
        return 'The quantity of items in building limits is not equal to the one of height plateau'
    elif result == 4:
        return 'The total area of the building limits is not equal to the total area of the height plateaus'
    elif result == 5:
        return 'There are gaps between building limits or height plateaus outisde of building limits'
    elif result == 0:
        createLimits(data)
        createPlateaus(data)
        return 'Data succesfully uploaded'
    return result

# # If you want to use a local input data use the folowing block
# f = open('./local_input/ValidData.json')
# ldata = json.load(f)
# lInput = newInput(ldata)
# print(lInput)

# # APIs requests 
class api_requests(Resource):
    # Get all data splited
    def get(self):
        data = wks.get_all_values()
        return {'All Objects': data}, 200

    # POST - data (BuildingLimits and Heigth plateaus) and return splited data.
    # post request to upload new data to specific row in spreadsheet.
    def post(self):
        # parser = reqparse.RequestParser()
        arguments = request.data # Here input data sent via post request
        reply = newInput(json.loads(arguments))
        return reply, 201


# API - /data endpoints to expose data
api.add_resource(api_requests, '/data')  # api request for data in database

# Just an additional for home page
@app.route("/")
def homePage():
    return "<p> Please add '/data' to your URL for (POST, GET) request to test the API! </p>"


if __name__ == "__main__":
    app.run(debug=True)
