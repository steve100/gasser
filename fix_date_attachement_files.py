import json
import sys
import os.path
import os 


def main():
    # Default file name
    default_file = "image_meta_full.json"

    # If a command-line argument is provided, use that instead
    filename = sys.argv[1] if len(sys.argv) > 1 else default_file

    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            file_path = entry.get("FilePath", "N/A")
            datetime_original = entry.get("DateTimeOriginal", "N/A")
            FileName = entry.get("FileName", "N/A") 
      
            dir = os.path.dirname(file_path)
        


            if datetime_original:
           
                # Convert to ISO format and replace ':' to make it a valid filename
                iso_date_prefix = datetime_original.replace(':', '-') 
                iso_date_prefix = iso_date_prefix.replace(' ', 'T') + "+00-00_"
                new_file_name = dir + "/" + iso_date_prefix + FileName
            
            old_file_name = dir + "/" +  FileName
            print(f"old_file_name {old_file_name}")
            print(f"new_file_name {new_file_name}")
            os.rename(old_file_name, new_file_name)


    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON - {e}")

if __name__ == "__main__":
    main()
