from logging import Logger
from databaseconnector import dbconnectors_postgresql
from typing import List
import os
import shutil
import configparser

from fastapi import UploadFile, responses

"""
Constructor method that initializes logger and db instance variables.
"""
class datahandler():
    dataFolder="./SharedDataFiles/"
    logger=None
    db=None
    def __init__(self, logger: Logger, dbconnector: dbconnectors_postgresql) -> None:
        self.logger = logger
        self.db = dbconnector
        
    """
    Method that creates a folder for the given username.
    """
    def createFolder(self, username: str):
        userfolder = self.dataFolder + username
        self.logger.debug("Creating folder " + userfolder)
        try:
            if not os.path.exists(userfolder):
                os.makedirs(userfolder)
            return True
        except:
            return False
        
    """
    Method that removes the folder for the given username.
    """
    def removeFolder(self, username: str):
        userfolder = self.dataFolder + username
        self.logger.debug("Removing folder " + userfolder)
        try:
            if os.path.exists(userfolder):
                shutil.rmtree(userfolder)
            return True
        except:
            return False
        
    """
    Method that stores the given list of files in a folder for the given username.
    """
    def storeFiles(self, username: str, files: List[UploadFile]):
        for file in files:
            destfile = self.dataFolder + username + "/" + str(file.filename)
            self.logger.debug("Uploading file " + destfile)
            try:
                with open(destfile, 'wb') as f:
                    while contents := file.file.read(1024 * 1024):
                        f.write(contents)
            except Exception:
                os.remove(destfile + str(file.filename))
                return responses.JSONResponse(status_code=500, content={"Error":f"There was an error uploading the file(s): {[file.filename for file in files]}"}), False
            finally:
                file.file.close()
        return {"message": f"Successfuly uploaded {[file.filename for file in files]}"}, True

    """
    Method that returns the full  path to a file specified by username and filename parameters.
    """
    def getFilePath(self, username: str, filename: str):
        destfile = self.dataFolder + username + "/" + filename
        return destfile

    """
    Method that deletes a file by the username and filename parameters.
    """
    def removeFile(self, username: str, filename: str):
        destfile = self.dataFolder + username + "/" + filename
        self.logger.debug("deleting file " + destfile)
        try:
           os.remove(destfile)
           return True
        except Exception:
            return "Error while deliting file " + filename + " of user " + username, False
        
    """
    Method that retrieves the database credentials.
    """
    def getDatabaseConfig(self, configfilepath: str):
        dbconfig = configparser.ConfigParser()
        dbconfig.read(configfilepath)
        return dbconfig
