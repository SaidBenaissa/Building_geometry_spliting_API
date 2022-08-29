from array import array
from distutils.command.build import build
from distutils.command.build_clib import build_clib
from importlib.metadata import requires
from operator import truediv
from typing import Any
from flask import Flask
from flask import request
from flask_restful import Resource, Api, reqparse
from typing_extensions import Required
import pandas as pd
import gspread
import json
import numpy as np



app = Flask(__name__)
api = Api(app)

data =''

#connects to google sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
sa = gspread.service_account('credentials.json', scope)
sh = sa.open("output_final")
wks = sh.worksheet("Sheet1")

#creates the column names in the google sheet
def createColNames():
    wks.update('A1','ObjectID')
    wks.update('B1','ObjectType')
    wks.update('C1','Data')
    wks.update('D1','Plateaus')
    
#creates row names for google sheet
createColNames()

id = wks.acell('E1').value

#Counter autoincrements ID for grabbing object by ID
def increaseID():
    id = int(wks.acell('E1').value)
    id = id +1
    wks.update('E1',id)
    return id

#creates new limit line on google sheet
class NewLimitObject:
 
    def __init__(self,data,id):
        self.id = id
        self.data = data
        #uploads values to google sheet
        wks.update('A'+ id, id)
        wks.update('B'+ id, 'Building Limit')
        wks.update('C'+ id, data)

#creates new plateau line on google sheet
class NewPlateauObject:

    def __init__(self,plateau,plateauData,id):
        self.id = id
        self.data = data
        #uploads values to google sheet
        wks.update('A'+ id, id)
        wks.update('B'+ id, 'Plateau')
        wks.update('C'+ id, plateauData)
        wks.update('D'+ id, plateau)


#verifies provided Data
#makes sure that building limits and height plateaus as well as the indidvidual object type is 'polygon'
def checkInput(data):
    build_temp = []
    height_temp = []
    build_area = 0
    height_area = 0
    
    valid = 0
    
    for item in data.keys():
        if item != 'building_limits' and item != 'height_plateaus':
            #checks if 'building limits' and 'height_plateaus' exist
            valid = 1
            break
        else:
            valid = 0


    if valid == 0:
        if data['building_limits']['type'] == 'FeatureCollection' and data['height_plateaus']['type'] == 'FeatureCollection':
            #checks if both inputs are feature collections
            pass
        else:
            valid = 2
            
        buildLen = len(data['building_limits']['features'])
        heightLen = len(data['height_plateaus']['features'])
        if buildLen != heightLen:
            #checks if height_plateaus and building_limits have the same amount of data points
            valid = 3
        else:
        #calculates total area of height plateaus and building limits and checks if they are equal
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
        #checks of building limit area matches height plateau area         
            valid = 4
    
        elif height_area == build_area:
            #checks for gaps or building limit exceedings
            if not np.array_equal(build_temp,height_temp):
                valid = 5
          

    return valid

#extracts data from json and creates NewPlateauObject
def createPlateaus(data):
     plateauToImport =data['height_plateaus']['features']
     lenPlateauToImport =len(data['height_plateaus']['features'])
     for items in range(lenPlateauToImport):
        id = increaseID()
        plateaus = getPlateaus(data)
        plateaus = plateaus[items]
        plateauData = plateauToImport[items]['geometry']['coordinates']
        NewPlateauObject(str(plateaus),str(plateauData),str(id))

#extracts data from json and creates NewLimitObject
def createLimits(data):
    limitsToImport =data['building_limits']['features']
    lenBuildingToImport =len(data['building_limits']['features'])
    for items in range(lenBuildingToImport):
        id = increaseID()
        limitData = limitsToImport[items]['geometry']['coordinates']
        NewLimitObject(str(limitData),str(id))

def getPlateaus(data):
    elevations = []
    for i in range(len(data['height_plateaus']['features'])):
            x = data['height_plateaus']['features'][i]['properties']['elevation']
            elevations.append(x)
    return elevations

def newInput(data):
    result = checkInput(data)

    #error codes 
    if result == 1:
        return 'Key(s) Missing! Building limit or height Plateau key is missing'
    elif result == 2:
        return 'The input Type is required to be a Feature Collection'
    elif result == 3:
        return 'The quantity of items in building limits is not equal to the one of height plateau'
    elif result == 4:
        return 'The total area of the building limits is not equal to the total area of the height plateaus'
    elif result ==5:
        return 'There are gaps between building limits or height plateaus outisde of building limits'
    elif result == 0:
        createLimits(data)
        createPlateaus(data)
        return 'Data succesfully uploaded'
    return result


class api_requests(Resource):
    #get request that provides all info to 
    def get(self):
        data = wks.get_all_values()
        return {'All Objects': data}, 200

    
    def post(self):
        #post request to upload new data to specific row in spreadsheet
        parser = reqparse.RequestParser()
        arguments = request.data
        reply = newInput(json.loads(arguments))
        return reply, 
        #if condition for error
   
        

#different api endpoints
api.add_resource(api_requests, '/data') #api request for data in database

   
if __name__ == "__main__":
    app.run(debug=True)
