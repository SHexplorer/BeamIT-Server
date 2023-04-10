import logging
import sys
from fastapi import FastAPI
import uvicorn
import argparse
import os

from databaseconnector import dbconnectors_postgresql
from datahandler import datahandler

app = FastAPI()

"""
Method to check for TLS-certificates and databaseconnection and start main:app. 
"""
if __name__ == '__main__':
    logger = logging.getLogger("initlog")
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('-cert')
    parser.add_argument('-key')
    args = parser.parse_args()

    db = dbconnectors_postgresql(logger=logger)
    dh = datahandler(logger=logger, dbconnector=db)

    if not args.cert or not args.key:
        if os.path.exists("beamit-tls.pem") and os.path.exists("beamit-tls.key"):
            args.cert = "beamit-tls.pem"
            args.key = "beamit-tls.key"

    dbconfig = dh.getDatabaseConfig('db.conf')
    if not db.initdb(host="localhost", port=5432, dbname=dbconfig['DBCONFIG']['name'], user=dbconfig['DBCONFIG']['user'], password=dbconfig['DBCONFIG']['password']):
        print("Database error, exiting...")
        sys.exit(1)
    db.closedb()
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=2, ssl_certfile=args.cert, ssl_keyfile=args.key)