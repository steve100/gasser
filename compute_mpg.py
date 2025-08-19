#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv


load_dotenv();



########################
def compute_mpg_info( ):
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
    

    query = "select * from fuel_readings order by id desc limit 2; "

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
  
        #server side cursor
        cur = conn.cursor()
        cur.execute(query)
        
        #this is current gas fill up
        row = cur.fetchone()

        if row:
            id         = row[0]
            total_mileage_current = row[3]
            gallons    = row[6]
            dollars    = row[5]
            file_name1 = row[1]
            datestr    = file_name1[:22]

      
        #this the previous gas fill up
        row2= cur.fetchone()
        if row2:
            total_mileage_previous = row2[3]
              

    
        trip_mileage = total_mileage_current - total_mileage_previous
        mpg  = trip_mileage / gallons

        #round to two decimal places
        mpg  = round(mpg, 2)

        print(f"id:          {id}")
        print(f"date:        {datestr}")
        print(f"trip_milage: {trip_mileage}")
        print(f"gallons:     {gallons}")
        print(f"dollars:     {dollars}")
        print(f"mpg:         {mpg}")
        
        price_per_gal = round(dollars / gallons, 3)


        #now lets update the mpg record
        # Example update
        cur.execute("""
            UPDATE fuel_readings
            SET mpg = %s, price_per_gal = %s 
            WHERE id = %s
        """, (mpg, price_per_gal, id))

        # even though we autocommit .. a commit can't hurt
        conn.commit()  # <-- Required to make changes permanent
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        sys.exit(1)
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
    
         





########################
def main():


    #print( odometer_file, trip_milage, total_mileage, gas_pump_file, dollars, gallons)

    compute_mpg_info()
 

if __name__ == "__main__":
    main()