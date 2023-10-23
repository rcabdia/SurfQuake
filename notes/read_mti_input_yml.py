import yaml

# Replace 'input_file.yaml' with the correct file path
input_file_path = 'mti_input.yml'

try:
    with open(input_file_path, 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    # Access and work with the data as needed
    earthquakes = data['earthquakes']
    for earthquake in earthquakes:
        # Process earthquake data
        print("Date:", earthquake['date'])
        print("Magnitude:", earthquake['magnitude'])
        # Access other earthquake data, stations, MTI parameters, and signal processing settings
except yaml.YAMLError as e:
    print(f"YAML parsing error: {e}")
except FileNotFoundError:
    print(f"File not found: {input_file_path}")