import psycopg2
import pwcrypt
import re
from typing import List

class dbconnectors_postgresql():
    logger = None
    connection = None
    usernameregex = "^[a-zA-Z0-9]{4,20}$"
    devicenameregex = "^[a-zA-Z0-9-_.]{4,64}$"
    def __init__(self, logger) -> None:
        self.logger = logger

    """
    Initializes the database connection and creates necessary tables if they do not exist.
    """
    def initdb(self, host, port, dbname, user, password):
        self.logger.debug("Connecting to posgresql database...")
        try:
            self.connection = psycopg2.connect(user=user, host=host, port=port, password=password, dbname=dbname)
            existingtables = self.__execute_read_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            self.logger.debug("Existing Tables: " + str(existingtables))
            # if there are no existing tables, create new ones
            if existingtables == []:
                self.logger.info("New database detected, creating tables...")
                self.__initTables()
                return True
            # if all tables don't exist, the database is corrupt
            if str(existingtables) != "[('User',), ('Device',), ('ShareData',)]":
                self.logger.error("Database corrupt, not all tables exist")
                return False
            else:
                self.logger.debug("Database connected successfully")
                return True
        # handle exceptions related to connection issues
        except psycopg2.Error as e:
            self.logger.error("Could not open database: " + str(e))
            return False
        
    """
    Closes the database connection.
    """     
    def closedb(self):
        try:
            self.connection.close()
            self.logger.debug("Closed database connection")
            return True
        except psycopg2.Error as e:
            self.logger.error("Could not close database: " + str(e))
            return False

    """
    Creates necessary tables in the database.
    """
    def __initTables(self):
        user_table = 'CREATE TABLE "User" ("Username" TEXT NOT NULL, "PasswordHash" TEXT NOT NULL, "PasswordSalt" TEXT NOT NULL, PRIMARY KEY("Username"));'
        device_table = 'CREATE TABLE "Device" ("DeviceName" TEXT NOT NULL, "Username" TEXT NOT NULL, "DeviceToken" TEXT NOT NULL, PRIMARY KEY("DeviceName", "Username"));'
        sharedata_table = 'CREATE TABLE "ShareData" ("Timestamp" TIMESTAMPTZ NOT NULL,"Username" TEXT NOT NULL, "targetDevices" TEXT NOT NULL, "DataType" TEXT NOT NULL, "Data" TEXT NOT NULL, "AutoOpen" BOOLEAN NOT NULL, "Encrypted" BOOLEAN NOT NULL, PRIMARY KEY("Timestamp", "Username"));'
        
        self.__execute_write_query(user_table, [])
        self.__execute_write_query(device_table, [])
        self.__execute_write_query(sharedata_table, [])

    """
    Checks if the username and password are valid and match a user in the database.
    """
    def login(self, username: str, password: str):
        if self.checkUserNameExists(username=username):
            # retrieve user's hashed password and salt
            user = self.__execute_read_query('SELECT "PasswordHash", "PasswordSalt" FROM "User" Where "Username" = %s;', [username])
             # check if the password is correct using the password hash and salt
            if pwcrypt.is_correct_password(user[0][1], user[0][0], password):
                return True
            else:
                return False
        else:
            return False

    """
    Method to add a user to the database.
    """
    def addUser(self, username: str, password: str):
        # Check if username follows the required format
        if not re.match(self.usernameregex , username):
            self.logger.error("Could not add user \"" + username + "\" - invalid combination of characters") 
            return "Username is not valid. Username must be a combination of 4 to 20 uppercase letters, lowercase letters, and numbers", False
        # Check if the username already exists in the database
        if self.checkUserNameExists(username):
            self.logger.debug("User \"" + username + "\" already exists")
            return "User already exists", False
        else:
            try: 
                salt, pw_hash = pwcrypt.hash_new_password(password)
                self.__execute_write_query('INSERT INTO "User" ("Username", "PasswordHash", "PasswordSalt") VALUES (%s, %s, %s);', [username, pw_hash, salt])
                self.logger.debug("Add User \"" + username + "\" successfully")
                return "User registered successfully", True
            except:
                self.logger.error("Could not add user!") 
                return "Error occurred, could not add user!", False
            
    """
    Method to delete an user from the database.
    """
    def removeUser(self, username: str):
        # Check if the user exists in the database
        if not self.checkUserNameExists(username):
            self.logger.debug("User \"" + username + "\" does not exist")
            return "User does not exist", False
        # Remove the user and all their devices from the database
        else:
            try: 
                self.__execute_write_query('DELETE FROM "User" WHERE "Username" = %s', [username])
                self.__execute_write_query('DELETE FROM "Device" WHERE "Username" = %s', [username])
                self.logger.debug("User \"" + username + "\" and Devices removed successfully")
                return "User and Devices removed successfully", True
            except:
                self.logger.error("Error occurred, could not remove user!") 
                return "Error occurred, could not remove user!", False

    """
    Method to add a device.
    """
    def addDevice(self, username: str, devicename: str, devicetoken: str):
        # Check if the device name follows the required format
        if not re.match(self.devicenameregex , devicename):
            self.logger.error("Could not add device \"" + devicename + "\" - invalid combination of characters") 
            return "Devicename is not valid. Devicename must be a combination of 4 to 20 uppercase letters, lowercase letters, and numbers", False
        if self.checkDeviceNameExists(username=username, devicename=devicename):
            self.removeDevice(username=username, targetDevice=devicename)
        # Add the device to the database
        self.__execute_write_query('INSERT INTO "Device" ("DeviceName", "Username", "DeviceToken") VALUES (%s, %s, %s);', [devicename, username, devicetoken])
        self.logger.debug("Add Device \"" + devicename + "\" from \"" + username + "\" successfully")
        return "", True

    """
    Method to delete a device.
    """
    def removeDevice(self, username: str, targetDevice: str):
        # Check if the user exists
        if not self.checkUserNameExists(username):
            self.logger.debug("User \"" + username + "\" does not exist")
            return "User does not exist", False
        else:
            # Check if the device exists
            if not self.checkDeviceNameExists(username, targetDevice):
                self.logger.debug("Device \"" + targetDevice + "\" from user \"" + username + "\" does not exist")
                return "Device does not exist", False
            else:
                try:
                    # Remove the device from the database 
                    self.__execute_write_query('DELETE FROM "Device" WHERE "Username" = %s AND "DeviceName" = %s' , [username, targetDevice])
                    self.logger.debug('Device "' + targetDevice + '" from user "' + username + '" removed successfully')
                    return "Device removed successfully", True
                except:
                    self.logger.error("Could not remove device!") 
                    return "Error occurred, could  not remove device!", False

    """
    Method to give a device a new name.
    """
    def renameDevice(self, username: str, deviceNameOld: str, deviceNameNew: str):
        # Check if the new device name is valid
        if not re.match(self.devicenameregex , deviceNameNew):
            self.logger.error("Could not rename device \"" + deviceNameOld + "\" to \"" + deviceNameNew + "\"- invalid combination of characters") 
            return "Devicename is not valid. New devicename must be a combination of 4 to 20 uppercase letters, lowercase letters, and numbers", False
        # Check if the new device name already exists
        if self.checkDeviceNameExists(username, deviceNameNew):
            self.logger.debug("Could not rename device \"" + deviceNameOld + "\" to \"" + deviceNameNew + "\" - \"" + deviceNameNew + "\" already does not exist!")
            return "Could not rename device \"" + deviceNameOld + "\" to \"" + deviceNameNew + "\" - \"" + deviceNameNew + "\" already does not exist!", False
        try:
            # Rename the device in the database
            if self.__execute_write_query('Update "Device" Set "DeviceName" = %s Where "Username" = %s AND "DeviceName" = %s', [deviceNameNew, username, deviceNameOld]):
                self.logger.debug('Device "' + deviceNameOld + '" from user "' + username + '" renamed to "' + deviceNameNew + '" successfully')
                return "Device renamed successfully", True
            else:
                return "Error", False
        except:
            self.logger.error("Could not remove device!") 
            return "Error occurred, could  not remove device!", False

    """
    Method to get a list of devices associated with a user.
    """
    def getDevices(self, username: str):
        result = self.__execute_read_query('SELECT "DeviceName" FROM "Device" Where "Username" = %s;', [username])
        devices: list = []
        if result:
            for device in result:
                devices.append(device[0])
        return devices, True
        
    """
    Method to check if the device token is valid for the device.
    """
    def checkDeviceToken(self, username: str, devicename: str, devicetoken: str):
        if self.__execute_read_query('Select * FROM "Device" Where "Username" = %s AND "DeviceName" = %s AND "DeviceToken" = %s', [username, devicename, devicetoken]):
            return True
        else:
            return False
        
    """
    Method to create a new file share.
    """
    def newFileShare(self, username: str, targetDevices: List[str], filename: str | None, autoOpen: bool, encrypted: bool):
        return self.__newShare(username=username, targetDevices=targetDevices, dataType="file", data=filename, autoOpen=autoOpen, encrypted=encrypted)
    
    """
    Method to create a new text share.
    """
    def newTextShare(self, username: str, targetDevices: List[str], text: str, autoOpen: bool, encrypted: bool):
        return self.__newShare(username=username, targetDevices=targetDevices, dataType="text", data=text, autoOpen=autoOpen, encrypted=encrypted)
    
    """
    Method to create a new url share.
    """
    def newUrlShare(self, username: str, targetDevices: List[str], url: str, autoOpen: bool, encrypted: bool):
        return self.__newShare(username=username, targetDevices=targetDevices, dataType="url", data=url, autoOpen=autoOpen, encrypted=encrypted)
    
    """
    Method to retrieve all shared data for the given username.
    """
    def checkAvailableData(self, username: str, devicename: str):
        shareData = self.__execute_read_query('Select * FROM "ShareData" Where "Username" = %s', [username])
        devices: list[str]
        responseData: list[tuple] = []
        # Iterate through each shared data entry and check if devicename is present in targetDevices list
        if shareData:
            for entry in shareData:
                devices = entry[2].strip('}{').split(',')
                if devicename in devices:
                    responseData.append(entry)
            return responseData, True
        else:
            return "No shared data for " + devicename, False
        
    """
    Method to retrieve the shared data entry for the given username and timestamp.
    """
    def getShare(self, username: str, devicename: str, timestamp: str):
        shareData = self.__execute_read_query('Select * FROM "ShareData" Where "Username" = %s AND "Timestamp" = %s', [username, timestamp])
        if shareData:
            devices: List[str] = shareData[0][2].strip('}{').split(',')
            # Check if devicename is present in targetDevices list for the given entry
            if devicename in devices:
                devices.remove(devicename)
                if devices == []:
                    if self.__execute_write_query('Delete FROM "ShareData" Where "Username" = %s AND "Timestamp" = %s', [username, timestamp]):
                        return shareData, True
                    else:
                        return "Error occoured", False
                else:
                    if self.__execute_write_query('Update "ShareData" Set "targetDevices" = %s Where "Username" = %s AND "Timestamp" = %s', [devices, username, timestamp]):
                        return shareData, True
                    else:
                        return "Error occoured", False
            else:
                return "No shared data for " + devicename + " with timestamp " + timestamp, False
        else:
            return "No shared data for " + devicename + " with timestamp " + timestamp, False

    """
    Method to create a new row in the "ShareData" table with the given parameters.
    """
    def __newShare(self, username: str, targetDevices: List[str], dataType: str, data: str | None, autoOpen: bool, encrypted: bool):
        if self.__execute_write_query('INSERT INTO "ShareData" ("Timestamp", "Username", "targetDevices", "DataType", "Data", "AutoOpen", "Encrypted") VALUES (NOW(), %s, %s, %s, %s, %s, %s);', [username, targetDevices, dataType, data, autoOpen, encrypted]):
            return True
        else:
            return False

    """
    Method to to check if the given username exists in the "User" table.
    """  
    def checkUserNameExists(self, username: str):
        if self.__execute_read_query('SELECT * FROM "User" Where "Username" = %s;', [username]):
            return True
        else:
            return False
    
    """
    Method to to check if the given devicename exists for the given username in the "Device" table.
    """  
    def checkDeviceNameExists(self, username: str, devicename: str):
        if self.__execute_read_query('SELECT * FROM "Device" Where "Username" = %s AND "DeviceName" = %s;', [username, devicename]):
            return True
        else:
            return False

    """
    Method to execute a write query with the given query and data parameters.
    """
    def __execute_write_query(self, query: str, data):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, data)
            self.connection.commit()
            self.logger.debug("Write query executed successfully: " + query + str(data))
            return True
        except psycopg2.Error as e:
            self.logger.error("Could not execute write DB-Query:" + str(e))
            return False

    """
    Method to execute a read query with the given query and data parameters.
    """
    def __execute_read_query(self, query: str, data=[]):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query, data)
            result = cursor.fetchall()
            self.logger.debug("Read query executed successfully: " + query + " - Response: " + str(result))
            return result
        except psycopg2.Error as e:
            self.logger.error("Could not execute read DB-Query:" + str(e))
            return False
