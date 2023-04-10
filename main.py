import logutil
from databaseconnector import dbconnectors_postgresql
from datahandler import datahandler
import re

from fastapi import FastAPI, UploadFile, responses, Request, Form, BackgroundTasks
import secrets


# Initializing logger, database connector, data handler and FastAPI application
logger = logutil.init("info")
db = dbconnectors_postgresql(logger=logger)
dh = datahandler(logger=logger, dbconnector=db)
app = FastAPI()

"""
Function to execute on application startup.
"""
@app.on_event("startup")
async def startup_event():
    logger.info("-")
    logger.info("BeamIT-Server starting...")
    # Retrieving database configuration from file and initializing the database connection
    dbconfig = dh.getDatabaseConfig('db.conf')
    db.initdb(host="localhost", port=5432, dbname=dbconfig['DBCONFIG']['name'], user=dbconfig['DBCONFIG']['user'], password=dbconfig['DBCONFIG']['password'])
    logger.info("BeamIT-Server has started")

"""
Function to execute on application shutdown.
"""
@app.on_event("shutdown")
async def shutdown_event():
    db.closedb()
    logger.info("Server stopped")
    
"""
Function to handle root URL request.
"""
@app.get("/")
async def root(request: Request):
    logger.debug("Root Adress was accessed")
    return responses.RedirectResponse(url=(request.url._url + "docs"))


# User ----------------------------------------------------------------------------------------------------

"""
Function to handle user registration request.
"""
@app.post("/user/register")
async def user_register(username: str = Form(), password: str = Form()):
    logger.info("Registering new user \"" + username + "\"...")
    response, result = db.addUser(username=username, password=password)
    if result:
        if dh.createFolder(username=username):
            return {"message": response, "successfull": True}
        else:
            return {"message": "Error occurred, could not add user!", "successfull": False}
    else:
        return {"message": response, "successfull": False}
    
"""
Function to handle user unregistration request.
"""
@app.post("/user/unregister")
async def user_unregister(username: str = Form(), devicename: str = Form(), devicetoken: str = Form()):
    # Checking if the device token is valid for the given user and device name
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        response, result = db.removeUser(username=username)
        if result:
            if dh.removeFolder(username=username):
                return {"message": response, "successfull": True}
            else:
                return {"message": "Error occurred, could not remove user!", "successfull": False}
        else:
            return {"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}

"""
Function to log in as a user with a password.
"""
@app.post("/user/login")
async def user_login(username: str = Form(), password: str = Form(), devicename: str = Form()):
    # Check if login is successful using the login method from the database module
    if db.login(username=username, password=password):
        # If login is successful, generate a token using the secrets module and add the device to the database
        token = "T-" + secrets.token_urlsafe(1024) + "##"
        response, result = db.addDevice(username=username, devicename=devicename, devicetoken=token)
        if result == True:
            return {"message": {'username' : username, 'devicename' : devicename, 'token' : token }, "successfull": True}
        else:
            return {"message": response, "successfull": False}
    # Return an error message if login was unsuccessful
    else:
        return {"message": "Login failed. Please check username and password", "successfull": False}


# Device ---------------------------------------------------------------------------------------------------

"""
Function for removing a device from a user's account.
"""
@app.post("/device/remove")
async def device_remove(username: str = Form(), devicename: str = Form(), devicetoken: str = Form(), targetDevice: str = Form()):
    # Check if device token is valid for given user and device name
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        response, result = db.removeDevice(username=username, targetDevice=targetDevice)
        if result:
            return {"message": response, "successfull": True}
        else:
            return {"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}

"""
Function to return a list of devices for a given user.
"""
@app.post("/device/list")
async def device_list(username: str = Form(), devicename: str = Form(), devicetoken: str = Form()):
    # Check if the given device token is valid for the given user and device name
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        # Get a list of devices for the given user
        response, result = db.getDevices(username=username)
        if result:
            return {"message": response, "successfull": True}
        else:
            return {"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}

"""
Function to rename a device for a given user.
"""
@app.post("/device/rename")
async def device_rename(username: str = Form(), devicename: str = Form(), devicetoken: str = Form(), devicenameNew: str = Form()):
    # Check if the given device token is valid for the given user and device name
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        response, result = db.renameDevice(username=username, deviceNameOld=devicename, deviceNameNew=devicenameNew)
        if result:
            return {"message": response, "successfull": True}
        else:
            return {"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}


## Sending and Receiving--------------------------------------------------------------------------------------

"""
Function to upload and store shared data under consideration of the data type.
"""
@app.post("/beamit/share")
async def beamit_upload(username: str = Form(), devicename: str = Form(), devicetoken: str = Form(), targetDevices: str = Form(), autoOpen: bool = Form(), encrypted: bool = Form(), files: list[UploadFile] | None = None, text: str | None = Form(default=None), url: str | None = Form(default=None)):
    # Check if the device token is valid for the given device name and username.
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        targetDevicesregex = "^\{([a-zA-Z0-9-_, ]{4,20})*\}$"
        if not re.match(targetDevicesregex, targetDevices):
            return {"message": "List of devicenames is not valid. Devicenames must be a List of devices, e.g. {devicename1, devicename2}.", "successfull": False}
        # Split targetDevices string into a list and check if each device exists
        targetDevicesList = targetDevices.replace(" ", "").strip('}{').split(',')
        for target in targetDevicesList:
            if not db.checkDeviceNameExists(username=username, devicename=target):
                return {"message": 'Device "' + target + '" does not exist! Request will not be executed!', "successfull": False}
        # If only files are present in the request, store them and create a file share
        if files != None and text == None and url == None:
            response, result = dh.storeFiles(username, files)
            if result:
                for file in files:
                    db.newFileShare(username=username, targetDevices=targetDevices, filename=file.filename, autoOpen=autoOpen, encrypted=encrypted)
                return {"message": response, "successfull": True}
            else:
                return {"message": response, "successfull": False}
        # If only text is present in the request, create a text share
        elif files == None and text != None and url == None: 
            return {"message": "", "successfull": db.newTextShare(username=username, targetDevices=targetDevices, text=text, autoOpen=autoOpen, encrypted=encrypted)}
        # If only a URL is present in the request, create a URL share
        elif files == None and text == None and url != None: 
            return {"message": "", "successfull": db.newUrlShare(username=username, targetDevices=targetDevices, url=url, autoOpen=autoOpen, encrypted=encrypted)}
        # If more than one sharedata is present in the request, return an error message
        else:
            return {"message": "More than one ShareData detected - check shared Data and send again", "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}

"""
Function to check if the provided user, device name, and device token combination is valid and if available data exists for that user and device.
"""
@app.post("/beamit/checkAvailableData")
async def beamit_check(username: str = Form(), devicename: str = Form(), devicetoken: str = Form()):
    # Check if the provided device user combination is valid using the checkDeviceToken function
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        response, result = db.checkAvailableData(username=username, devicename=devicename)
        if result:
            return {"message": response, "successfull": True}
        else:
            return{"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}

"""
Function to receive data from a device for a specific user and device combination.
"""
@app.post("/beamit/receive")
async def beamit_receive(background_tasks: BackgroundTasks, username: str = Form(), devicename: str = Form(), devicetoken: str = Form(), timestamp: str = Form(), ):
    # Check if the provided device user combination is valid using the checkDeviceToken function
    if db.checkDeviceToken(username=username, devicename=devicename, devicetoken=devicetoken):
        response, result = db.getShare(username=username, devicename=devicename, timestamp=timestamp)
        if result:
            if response[0][3] == "file":
                filename = response[0][4]
                background_tasks.add_task(func=dh.removeFile, username=username, filename=filename)
                return responses.FileResponse(dh.getFilePath(username=username, filename=filename), media_type='application/octet-stram', filename=filename)
            else:
                return {"message": response, "successfull": True}
        else:
            return {"message": response, "successfull": False}
    else:
        return {"message": "Device-User-Combination not vaild!", "successfull": False}
        