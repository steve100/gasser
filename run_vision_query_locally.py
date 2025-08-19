import base64
from openai import OpenAI
import json 
import re 
from pathlib import Path

# Point to your local LMStudio server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

FIRST_PROMPT_TEXT = (
    "is this a fuel gauge with an odometer or is it a digital display showing fuel prices"
    "If it is a digital display for a gas pump I need you to return as json the price and gallons and do not use a $"
    "if it is a odometer I need you to return as json the odometer reading"
    )

model="qwen/qwen2.5-7b-instruct-q8_0" # The model alias in LMStudio


################################################
# 
def parse_answer(answer):
    # Find the JSON block within the response text using regex
    # This looks for anything between '{' and '}'
    json_match = re.search(r'\{.*\}', answer, re.DOTALL)
    
    if not json_match:
        print("❌ Error: No JSON object found in the response.")
        return None
        
    json_string = json_match.group(0)

    # Convert the JSON string into a Python dictionary
    data_dict = json.loads(json_string)

    #debug
    #print ("debug:")
    #print ("json_string and dictionary")
    #print ("json string")
    #print (json_string)
    #print ("Dictionary")
    #print (data_dict)
    return data_dict



################################################
# --- Function to encode the image to base64 ---
def encode_image(image_path):
    """Encodes an image file into a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The image file was not found at {image_path}")
        return None
    
#################################################
def process_an_image(IMAGE_PATH,file):
   
      # 1. Send an image into the model
    base64_image = encode_image(IMAGE_PATH)
    if not base64_image:
        return # Exit if image couldn't be encoded

    try:
        response = client.chat.completions.create(
            model=model , # The model alias in LMStudio
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": FIRST_PROMPT_TEXT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=100, # Limit the length of the response
        )
        
        # 2. Get the answer from the model's response
        answer = response.choices[0].message.content
        #print(f"\n🤖 Model's full answer: {answer}")

        # 3. Parse the answer
        # Convert to lowercase for case-insensitive matching
        answer_lower = answer.lower()

        is_fuel_gauge    = "odometer_reading" in answer_lower
        is_price_display =   "price" in answer_lower 

        # print("\n--- Parsing Result ---")
        if is_fuel_gauge and not is_price_display:
            print("The model indicates it is a fuel gauge with an odometer.")
            
            data_dict = parse_answer(answer)

            odometer_reading   = data_dict['odometer_reading']
            
            print (odometer_reading)


        elif is_price_display:
            print("The model indicates it is a display for fuel prices.")


            data_dict = parse_answer(answer)

            #gas_price   = data_dict['price']
            #gas_gallons = data_dict['gallons']
            #print (gas_price,gas_gallons)

        else:
            print("🤔 The model's answer was inconclusive or did not contain the expected keywords.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure LMStudio is running and the model is loaded correctly.")
    
    #hack for what is coming
    data_dict['file'] = file
    return data_dict

########################################

# --- Main execution ---
def main():


    # Define the directory you want to search.
    # 
    # probably should be configurable
    path_to_check = './images_thumbnails'
    directory_path = Path(path_to_check)

    # Use a list comprehension to get the names of all files.
    file_names = [item.name for item in directory_path.iterdir() if item.is_file()]

    results_llm_dict = {
        'odometer_image': {},
        'gas_pump_image': {},
        'model': "",
        'source_dir': "",
        'input_files': []
}
    
    # Print the results 
    for file in file_names:
        IMAGE_PATH = path_to_check + "/" +  file

        results_llm_dict['source_dir'] = path_to_check
        results_llm_dict['model'] = model

        
        data_dict = process_an_image(IMAGE_PATH,file)
        print (data_dict)
        print ("")

        if 'odometer_reading' in data_dict:
            results_llm_dict['odometer_image']['file'] = file 
            results_llm_dict['odometer_image']['bottom_value_total_mileage'] = data_dict['odometer_reading']
            results_llm_dict['odometer_image']['top_value_trip'] = 0 
            results_llm_dict['input_files'].append(file)
        
        if 'gallons' in data_dict: 
            results_llm_dict['gas_pump_image']['file'] = file 
            results_llm_dict['gas_pump_image']['top_value_dollars'] = data_dict['price']
            results_llm_dict['gas_pump_image']['bottom_value_gallons'] = data_dict['gallons']
            results_llm_dict['input_files'].append(file)

    #print ( results_llm_dict ) 
    json_results_llm= json.dumps(results_llm_dict)
    print ( json_results_llm )

    #write json_results_llm to  results_llm.json (todo jsw)
    file_path = "results_llm.json"
    with open(file_path, "w") as json_file:
        json.dump(results_llm_dict, json_file, indent=4)

if __name__ == "__main__":
    main()

