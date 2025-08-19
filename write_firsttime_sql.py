#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import sys
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv


load_dotenv();



########################
def write_llm_gauge_info_first_sql( total_mileage ):
    PGHOST      = os.environ.get("PGHOST")
    PGUSER      = os.environ.get("PGUSER")
    PGPASSWORD  = os.environ.get("PGPASSWORD")  
    PGPORT      = os.environ.get("PGPORT")
    PGDATABASE  = os.environ.get("PGDATABASE")

    DB_CONFIG = {
        "dbname": PGDATABASE,
        "user":   PGUSER,
        "password": PGPASSWORD,
        "host": PGHOST,
        "port": PGPORT
    }
    
    #     insert_query = "INSERT INTO fuel_readings  (odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons)  VALUES (%s, %s, %s, %s,%s,%s);"

    #set up the insert
    #in theory it should work but the api does not allow it.
    # insert_query = "INSERT INTO fuel_readings  ( total_mileage )  VALUES (%s);"
    insert_query = "INSERT INTO fuel_readings  (odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons)  VALUES (%s, %s, %s, %s,%s,%s);"

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
  
        #do the insert - with autocommit - so no explicit commit
        with conn, conn.cursor() as cur:
            cur.execute(insert_query, ('', 0, total_mileage,'',0,0) )

      
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    






########################
def main():


    #print( odometer_file, trip_milage, total_mileage, gas_pump_file, dollars, gallons)
 
    start_milage = 274363
    write_llm_gauge_info_first_sql(start_milage)
 

if __name__ == "__main__":
    main()
