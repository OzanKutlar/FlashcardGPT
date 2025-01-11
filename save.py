import sys
import json
import os

def save_to_json():
    # Ensure there are enough arguments
    if len(sys.argv) < 3:
        print("Usage: python save.py <variable_name> <overwrite> <item1> <item2> ... <itemN>")
        sys.exit(1)

    # The first argument is the name of the variable (key)
    variable_name = sys.argv[1]
    
    overwrite = sys.argv[2]

    # The rest of the arguments are the contents of the array
    array_contents = sys.argv[3:]

    # Prepare data to be saved
    try:
        # Load existing data from state.json if it exists
        if os.path.exists('data.json'):
            with open('data.json', 'r') as file:
                data = json.load(file)
        else:
            data = {}

        # Check if the variable name already exists in the data
        if overwrite == 0:
            # If it exists, append to the existing array
            data[variable_name].extend(array_contents)
        else:
            # If it doesn't exist, create a new array for the variable
            data[variable_name] = array_contents

        # Save the updated data back into state.json
        with open('data.json', 'w') as file:
            json.dump(data, file, indent=4)
        
        print(f"Data saved/updated in data.json under the key '{variable_name}'.")

    except Exception as e:
        print(f"Error while processing or saving data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    save_to_json()
