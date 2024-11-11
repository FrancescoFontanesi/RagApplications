import json
import yaml

# Load JSON file
with open('swaggerS&A.json', 'r') as json_file:
    data = json.load(json_file)

# Save as YAML file
with open('swaggerSEA.yaml', 'w') as yaml_file:
    yaml.dump(data, yaml_file, default_flow_style=False)