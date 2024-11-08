import pandas as pd
import json
from pandas import notna
import os 
import random




class dataConverterForSE:
    
    
    def __init__(self):
        self.entities = None
        self.links = None
        
        

    def generate_entities_from_csv(self, csv_file_path):
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Initialize the JSON structure
        entities = {"items": []}
        
        for _, row in df.iterrows():
            entity_type = row['type']
            entity = {
                "itemType": "entity",
                "key": str(row['key']),
                "label": row['label'],
                "type": entity_type,
                "properties": {}
            }
            
            # Assign properties directly from the row
            if 'properties' in row and pd.notna(row['properties']):
                # Assuming properties is a JSON string, we need to parse it
                entity["properties"] = json.loads(row['properties'])
            
            entities["items"].append(entity)
        
        return entities

    def add_links_from_csv(self, csv_file_path, initial_data):
        """
        Converts tabular data in a CSV file to a JSON structure.
        
        Parameters:
        csv_file_path (str): Path to the CSV file containing the tabular data.
        json_file_path (str): Path to the output JSON file.
        """
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Initialize the JSON structure
        data = initial_data
        
        # Iterate over the rows of the DataFrame
        for _, row in df.iterrows():
            # Convert float keys to integer strings
            key1 = str(int(row['key1']))
            key2 = str(int(row['key2']))
            
            # Parse the properties string if it's a string
            if isinstance(row['properties'], str):
                try:
                    properties = json.loads(row['properties'])
                except json.JSONDecodeError:
                    properties = {"Description": {"value": row['properties']}}
            else:
                properties = row['properties']
            
            item = {
                "itemType": row['itemType'],
                "key": f"{key1}-{key2}",
                "label": row['label'],
                "type": row['type'],
                "key1": key1,
                "key2": key2,
                "type1": row['type1'],
                "type2": row['type2'],
                "properties": properties
            }
            data["items"].append(item)
        
        return data

    def generate_random_color(self):
        """Generate a random hex color."""
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    def generate_links_for_dm_from_csv(self, csv_file_path, json_file_path):
        """
        Generate possible links from CSV data and save them in the specified JSON format.
        
        Parameters:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to save the generated JSON
        """
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Initialize the links list
        links = []
        
        # Get unique combinations of type1, type2, and type (Name)
        unique_type_combinations = df[['type1', 'type2', 'type']].drop_duplicates()
        
        # Generate links for each unique combination
        for _, row in unique_type_combinations.iterrows():
            # Get all display names for this combination
            matching_rows = df[
                (df['type1'] == row['type1']) & 
                (df['type2'] == row['type2']) & 
                (df['type'] == row['type'])
            ]
            # Use the first display name found
            display_name = matching_rows['type'].iloc[0]
            
            # Create the standard property structure for Description
            property_structure = [{
                "IsMandatory": False,
                "InputType": 11,
                "SearchInputType": 11,
                "Mask": None,
                "Values": None,
                "IsLabel": False,
                "IsIndex": False,
                "Grouping": None,
                "Name": "Description",
                "DisplayName": "Descrizione",
                "DataType": 4
            }]
            
            link = {
                "Label": None,
                "EndsTypes": [
                    {
                        "type1": row['type1'],
                        "type2": row['type2']
                    }
                ],
                "Color": self.generate_random_color(),
                "IsSymmetricLink": False,
                "ShowArrows": True,
                "DisplayName": display_name,
                "Name": row['type'],
                "Property": property_structure
            }
            
            links.append(link)
        
        # Create the final structure
        output = {
            "Links": links
        }
        
        # Write to JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
            
    def save_dcj(self, data, json_file_path):
    # Write the JSON structure to a file
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def add_links_to_dm(self, links_dm, datamodel):
        
        with open(datamodel, 'r', encoding='utf-8') as f:
            datamodel = json.load(f)
        
        with open(links_dm, 'r', encoding='utf-8') as f:
            links_dm = json.load(f)
        
        datamodel['Links'] = links_dm['Links']
        
        with open('datamodel.json', 'w', encoding='utf-8') as f:
            json.dump(datamodel, f, ensure_ascii=False, indent=4)
            
    def generate_dcj_and_dm(self, entities_csv, links_csv):
        
        data = self.generate_entities_from_csv(entities_csv)
        self.add_links_from_csv(links_csv, data)
        self.save_dcj(data, os.path.join(os.getcwd()+'\dcj.json'))
        
        self.generate_links_for_dm_from_csv(links_csv, os.path.join(os.getcwd()+'\links_dm.json'))
        
        self.add_links_to_dm(os.path.join(os.getcwd()+'\links_dm.json'), os.path.join(os.getcwd()+'\datamodelBase.json'))
        


def main():
    converter = dataConverterForSE()
    converter.generate_dcj_and_dm('entities.csv', 'links.csv')

if __name__ == "__main__":
    main()