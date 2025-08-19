echo "Gasser - A Fuel Use Tracker that also computes MPG"

echo "Check to see there is a locally running LLM model"
rem check_local_running.bat


echo Create the Directories
rem mkdir images_thumbnails
rem mkdir attachments

rem filesystem initialization
rem echo "clean up the old images"
rem start /wait remove-images.bat

rem database initialization
rem drop and create the database

echo "create the table  fuel_readings"
rem python3 create_gasser_table.py

echo "create the first row with a milage if all the rows are empty"
rem python3 write_firsttime_sql.py

rem echo "Get the two images from gmail"
rem echo "buggy - token revoked"
echo "Manually download the two images into ./attachments"
rem python3 gasser.py


echo "Extract Metadata from the Images  latitude longitude and location"

python3 exif_to_json_and_csv.py --folder ./attachments --csv-out image_metadata_full.csv --json-out image_metadata_full.json


rem echo "Fix the filenames if they do not have dates"
rem echo "This will happen on a manual image download to ./attachments"
rem echo "comment out if dates are not fixed"
rem python3 fix_date_attachement_files.py image_metadata_full.json



echo "Create thumbnails"
python3 create_thumbnails.py

echo "Analyze the cost using OpenAPI pricing"
python3 image_cost_batch.py images_thumbnails prompt_file

echo "Analyze the images"
rem ChatGPT / OpenAI
rem python run_vision_query_chatgpt.py  --dir images_thumbnails --model gpt-4o-mini
rem Local LMstudio  Qwen2.5-VL-7B-Instruct-Q8_0 
python3 run_vision_query_locally.py

echo "Write the results to the database"
python3  write_results_sql.py

echo "Display the information and compute the MPG"
python3  compute_mpg.py 

echo "Update the Database with latitude longitude and location
python3 read_update_metadata.py  image_metadata_full.json

echo "Display the last 10 rows based on the id"
view_table_10.bat
