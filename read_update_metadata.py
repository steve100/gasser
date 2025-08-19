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
#def find_id_by_filename():
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
    
def find_id_by_filename():
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
            file_name1 = row[1]
  
        # even though we autocommit .. a commit can't hurt
        conn.commit()  # <-- Required to make changes permanent

    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        sys.exit(1)

    return id, file_name1, cur 


def load_image_metadata_as_dict(file_path):
    """Load JSON into a dictionary keyed by FileName, with duplicate detection."""
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)  # list of dicts

    data_dict = {}
    for rec in data_list:
        filename = rec["FileName"]
        if filename in data_dict:
            raise ValueError(
                f"Duplicate FileName found in JSON: {filename}\n"
                f"Original entry: {data_dict[filename].get('FilePath')}\n"
                f"Duplicate entry: {rec.get('FilePath')}"
            )
        data_dict[filename] = rec

    return data_dict

if __name__ == "__main__":
    # Read the Database to get the id and the filename to update
    id, fn , cur = find_id_by_filename()

    # Get filename from command-line or use default
    json_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("image_metadata_full.json")

    if not json_file.exists():
        print(f"Error: File '{json_file}' not found.")
        sys.exit(1)

    try:
        image_metadata = load_image_metadata_as_dict(json_file)
        print(f"Loaded {len(image_metadata)} records from {json_file}")
        for filename, metadata in image_metadata.items():
            print(f"File: {filename}")
            print(f"  Location: {metadata['Location']}")
            print(f"  GPSLatitudeFixed:  {metadata['GPSLatitudeFixed']}")
            print(f"  GPSlongitudeFixed: {metadata['GPSLongitudeFixed']}")

            location = {metadata['Location']}
            lat = {metadata['GPSLatitudeFixed']}
            lng = {metadata['GPSLongitudeFixed']}

            if fn == filename:
                print ("found it:")
                print (id)
                print (location)
                print (lat)
                print (lng)
       
                location = next(iter(location))  # get the single value from the set
                location = str(location)       # ensure it's a string
   
                lat = next(iter(lat))  # get the single value from the set
                lat = float(lat)       # ensure it's a float

                lng = next(iter(lng))  # get the single value from the set
                lng = float(lng)       # ensure it's a float
   


                #now lets update the lat,lng,location for  record id 
                cur.execute("""
                    UPDATE fuel_readings
                    SET lat = %s , lng = %s, location = %s
                    WHERE id = %s
                   
                """, (lat, lng,location,id))





    except ValueError as e:
        print("ERROR:", e)
