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

##########################
def read_results_llm():
       # Default filename if not provided
    default_file = "results_llm.json"
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(default_file)

    # Ensure file exists
    if not json_path.exists():
        print(f"Error: File '{json_path}' not found.")
        sys.exit(1)

    # Load JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)

    # Pretty-print the entire JSON
    print("\n--- Full JSON Content ---")
    print(json.dumps(data, indent=2))

    # Example: Access and print specific values
    print("\n--- Extracted Values ---")
    odo = data.get("odometer_image", {})
    gas = data.get("gas_pump_image", {})

    print(f"Odometer file: {odo.get('file')}")
    print(f"Trip value: {odo.get('top_value_trip')}")
    print(f"Total mileage: {odo.get('bottom_value_total_mileage')}")

    print(f"Gas pump file: {gas.get('file')}")
    print(f"Dollars: {gas.get('top_value_dollars')}")
    print(f"Gallons: {gas.get('bottom_value_gallons')}")

    return (odo.get('file'), odo.get('top_value_trip')    , odo.get('bottom_value_total_mileage'), \
            gas.get('file'), gas.get('top_value_dollars') , gas.get('bottom_value_gallons') )

########################
def write_llm_gauge_info_sql( odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons):
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

    print("odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons")
    print (odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons)
    
    #set up the insert
    insert_query = "INSERT INTO fuel_readings  (odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons)  VALUES (%s, %s, %s, %s,%s,%s);"

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
  
        #do the insert - with autocommit - so no explicit commit
        with conn, conn.cursor() as cur:
            cur.execute(insert_query, (odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons) )

      
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
    odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons= read_results_llm()

    #print( odometer_file, trip_milage, total_mileage, gas_pump_file, dollars, gallons)
 
    write_llm_gauge_info_sql( odometer_file, trip_value, total_mileage, gaspump_file, dollars, gallons)
 

if __name__ == "__main__":
    main()
