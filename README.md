# gasser 

## A CAG Agent Proof oF Concept program to read from two photos: a gas pump and an odometer
   
-  Setup a Python Virtual Environment
-  Read and Extract the metadata (EXIF) from images in an imaage directory
-  Send the Images to a Local LLM model using LM Studio 
-  (Optionally) Send the images to a a foundational LLM model using ChatGPT
-  Calculate MPG
-  Later:  Geocode and Draw a Map

## Testing
Tested Under Windows 11 pro
Should run well under Linux - change the .bat files to .sh files
Powershell under Windows is a good idea as well instead of .bat files



## Overall
Reactions: 
Surprised it could do all this.
   Using Model qwen2.5-vl-7b-instruct@q8_0 --gpu=max 
   see below: check_local_running.bat 

## Pre-Configuration

```
Choose an OS
  Windows 11 

Install your graphics card drivers
  Mine: AMD Raedon 780m iGPU.

Install Gmail Oauth
  you will get a file and when you activate it it will turn into token.json.
    client_secret.json _> token.json  

Install a project directory
example:
 \user\steve\projects
 cd projects
 
Create a Python virtual environment for gasser 
 python -m venv gasser-env

 activate it
 \Scripts\activate

  how to deactivate it - when you need to 
  deactivate

Clone the project
  git clone https://github.com/steve100/gasser.git

Install LM Studio
  https://lmstudio.ai/download?os=win32

  Allow LM Studio to accept API
  command line: lms server start
  gui: use the developer tab .. but it is a bit difficult to find.

 Make sure Ollama is not running as a service
  There will be a llama in your service tray 

 
 Obtain an OpenAI Key if you want to use OpenAI aka ChatGPT
   Free API Keys are NOT available at this time 
   Limit your account to $20 so you do not spend too much money
   https://community.openai.com/t/how-do-i-get-my-api-key/29343

Install PostgreSQL 
   I left the default userid/password/database in .env and pg.bat
   You need to assign a password to user postgres

   Version I used
   psql -version
   psql (17.5)

   Download location
    https://www.postgresql.org/download/windows/

   Video tutorial
   https://youtu.be/GpqJzWCcQXY

   Udemy course
   https://www.udemy.com/course/complete-python-postgresql-database-course/
    

   sets the windows code page
   set-code-page.bat 
   
   sets the comand line environment variables (* optional)
   pg.bat
   
   sets the python environment variables
   .env

Install Pgadmin the PostgreSQL GUI editor
   Download location
   https://www.pgadmin.org/download/pgadmin-4-windows/

   documentation:
   https://www.pgadmin.org/docs/pgadmin4/development/getting_started.html
```

## Configuration:
```
   Create the table fuel_readings (*done once)
    create_gasser_table.py

  Set the code page               (*optional, needed once)
  Set the environment variables
    set-code-page.bat
    pg.bat

   Sets the first entry into the database
    psql < start_mileage.sql

   View the table
    view_table_10.bat  

   Remove the Images
    remove-images.bat

   Manually download the images into ./attachements
    oauth key isn't working for me now.

  Load the model and check if it is running
    check_local_running.bat

  Edit for what you need to run
    dogasser.bat

  Seperate Commands
    View the table
    view_table_10.bat  

  Estimated OpenAI price for the prompt
    python3 image_cost_batch.py  ./attachments prompt_file
    python3 image_cost_batch.py  ./images_thumbnails prompt_file

  Check picture dimentions
    # hard coded to ./attachements for now
    python3 check_picture_dimentions.py 

  Handy command to delete row -- set x to a number
  Say you accidently get a row you do not like with developing new function
   psql
   delete from fuel_readings where id  = x; 
```

        




## Other
```
Make sure the Python Virtual Environment is installed correctly.
It does not have to be in your project directory


Put your API_key and LLM information into the Python .env file
edit .env
It needs to look like this:
OPENAI_API_KEY=yourkeyhere


API_URL_LOCAL = "http://localhost:1234/v1/chat/completions"
API_URL_OPENAI = "https://api.openai.com/v1/chat/completions"
```




Errata:
   More testing of images is needed.
   More work needs to be done for missing a fill up.


   The .env could have image and output directories.


```
