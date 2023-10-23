import json

# Load the JSON file
with open('mti_input.json', 'r') as file:
    data = json.load(file)

# Access earthquake data
try:
    with open(input_file_path, 'r') as file:
        data = json.load(file)
    # Access and work with the data as needed
    earthquakes = data['earthquakes']
    for earthquake in earthquakes:
        # Process earthquake data
        print("Date:", earthquake['date'])
        print("Magnitude:", earthquake['magnitude'])
        # Access other earthquake data, stations, MTI parameters, and signal processing settings
except json.JSONDecodeError as e:
    print(f"JSON decoding error: {e}")
except FileNotFoundError:
    print(f"File not found: {input_file_path}")