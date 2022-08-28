from array import array
from distutils.command.build import build
from distutils.command.build_clib import build_clib
from importlib.metadata import requires
from operator import truediv
import re
from typing import Any
from urllib import request
from flask import Flask
from flask_restful import Resource, Api, reqparse
from typing_extensions import Required
import pandas as pd
import ast
import gspread
import json
import numpy as np

app = Flask(__name__)
api = Api(app)

# connects to google sheets API
# Connects to google sheets API using credential
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
sa = gspread.service_account('credentials.json', scope)
sh = sa.open("output")
wks = sh.worksheet("Sheet1")


def createRowNames():
    wks.update('A1', 'ObjectID')
    wks.update('B1', 'ObjectType')
    wks.update('C1', 'Data')
    wks.update('D1', 'Plateaus')


# creates row names for google sheet
createRowNames()

id = wks.acell('E1').value


# Counter autoincrements ID for grabbing object by ID
# make sure to put id to 1 not 0
def increaseID():
    id = int(wks.acell('E1').value)
    id = id + 1
    wks.update('E1', id)
    return id


f = open('feature2.json')
data = json.load(f)


# creates new limit line on google sheet
class NewLimitObject:

    def __init__(self, data, id):
        self.id = id
        self.data = data

        wks.update('A' + id, id)
        wks.update('B' + id, 'Building Limit')
        wks.update('C' + id, data)


# creates new plateau line on google sheet
class NewPlateauObject:

    def __init__(self, plateau, plateauData, id):
        self.id = id
        self.data = data

        wks.update('A' + id, id)
        wks.update('B' + id, 'Plateau')
        wks.update('C' + id, plateauData)
        wks.update('D' + id, plateau)


# verifies provided Data
# makes sure that building limits and height plateaus as well as the object type 'polygon' are given
def checkInput(data):
    build_temp = []
    height_temp = []
    build_area = 0
    height_area = 0
    buildLen = len(data['building_limits']['features'])
    heightLen = len(data['height_plateaus']['features'])

    for item in data.keys():
        if item != 'building_limits' and item != 'height_plateaus':
            # checks if 'building limits' and 'height_plateaus' exist
            valid = False
            break
        else:
            valid = True

    if valid:
        if data['building_limits']['type'] == 'FeatureCollection' and data['height_plateaus'][
            'type'] == 'FeatureCollection':
            # checks if both inputs are feature collections
            pass
        else:
            valid = False

    if buildLen != heightLen:
        # checks if height_plateaus and building_limits have the same amount of data points
        valid = False
    else:
        # calculates total area of height plateaus and building limits and checks if they are equal
        # if height plateau is outside of building limit, error is given
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
    if height_area != build_area:
        print('the building_limit area does not match with the height plateaus')
        valid = False

    elif height_area == build_area:
        print('total area sizes are the same! Good!')
        # checks for gaps or building limit exceeds
        if not np.array_equal(build_temp, height_temp):
            valid = False
            print('There are gaps or building limit exceedings')

    return valid


def createPlateaus(data):
    plateauToImport = data['height_plateaus']['features']
    lenPlateauToImport = len(data['height_plateaus']['features'])
    for items in range(lenPlateauToImport):
        id = increaseID()
        plateaus = getPlateaus(data)
        plateaus = plateaus[items]
        plateauData = plateauToImport[items]['geometry']['coordinates']
        NewPlateauObject(str(plateaus), str(plateauData), str(id))


def createLimits(data):
    limitsToImport = data['building_limits']['features']
    lenBuildingToImport = len(data['building_limits']['features'])
    for items in range(lenBuildingToImport):
        id = increaseID()
        limitData = limitsToImport[items]['geometry']['coordinates']
        NewLimitObject(str(limitData), str(id))


def getPlateaus(data):
    elevations = []
    for i in range(len(data['height_plateaus']['features'])):
        x = data['height_plateaus']['features'][i]['properties']['elevation']
        elevations.append(x)
    return elevations


def newInput(data):
    result = checkInput(data)
    if not result:
        print(
            'Please check your input. The object Type should be "FeatureCollection", the individual Object Type should be "Polygon" and height plateaus as well as building limits are required')
        # Add Error 409
    elif result:
        createLimits(data)
        createPlateaus(data)


# main method
    newInput(data)

class getData(Resource):
    # allows user to upload new json
    def get(self):
        data = wks.get_all_values()
        return {'All Objects': data}, 200


class postData(Resource):
    # API get request
    # def get(self):
    #     data = wks.get_all_values()
    #     return {'All Objects': data}, 200

    # puts information

    def post(self):
        parser = reqparse.RequestParser()
        # parser.add_argument('item', required=True, type=int)
        # parser.add_argument('id', required=True, type=int)
        # parser.add_argument('name', required=True, type=int)
        items = parser.parse_args(newInput(data))

        print(data)
        return newInput(data), 201
        # if condition for error

# class updateData(Resource):
#     # Update data
#     def put(self,item, id, name):
#         parser = reqparse.RequestParser()
#         parser.add_argument('item', required=True, type=int)
#         parser.add_argument('id', required=False, type=int)
#         parser.add_argument('name', required=False, type=int)
#       #  items = parser.parse_args(newInput(data))
#         newInput(data)
#         return data, 201
#         # if condition for error



# different endpoints
api.add_resource(postData, '/data')  # api request for data in database
api.add_resource(getData, '/allData')  # upload new entries
# api.add_resource(updateData,'/data/<item>')

if __name__ == "__main__":
    app.run(debug=True)
