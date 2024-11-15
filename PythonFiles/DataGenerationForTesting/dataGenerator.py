import pandas as pd
import json
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
        Adds links from a CSV file to an existing JSON structure.
        
        Parameters:
        csv_file_path (str): Path to the CSV file containing the link data.
        initial_data (dict): Initial JSON structure to append the links to.
        
        Returns:
        dict: Updated JSON structure containing both initial data and new links.
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
            
            
            item = {
                "itemType": row['itemType'],
                "key": f"{key1}-{key2}",
                "label": row['label'],
                "type": row['type'],
                "key1": key1,
                "key2": key2,
                "type1": row['type1'],
                "type2": row['type2'],
                "properties": {}
            }
            if 'properties' in row and pd.notna(row['properties']):
                try:
                    # Try to parse the JSON string, removing any extra quotes if present
                    properties_str = row['properties'].strip('"').replace('""', '"')
                    item["properties"] = json.loads(properties_str)
                except json.JSONDecodeError:
                    # If parsing fails, keep empty properties
                    item["properties"] = {}
                
            data["items"].append(item)
        
        return data

    def generate_random_color(self):
        """Generate a random hex color."""
        return f"#{random.randint(0, 0xFFFFFF):06x}"
    
    def generate_metatype(self):
        return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)}"

    def generate_links_for_dm_from_csv(self, csv_file_path, json_file_path):
        """
        Generate possible links from CSV data and save them in the specified JSON format.
        Collects all unique property names for each link type combination.
        """
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Initialize the links list
        links = []
        
        # Get unique combinations of type1, type2, and type
        unique_type_combinations = df[['type1', 'type2', 'type']].drop_duplicates()
        
        # For each unique combination
        for _, combo in unique_type_combinations.iterrows():
            # Get all rows matching this type combination
            matching_rows = df[
                (df['type1'] == combo['type1']) & 
                (df['type2'] == combo['type2']) & 
                (df['type'] == combo['type'])
            ]
            
            # Collect all unique property names for this link type
            all_properties = set()
            for _, row in matching_rows.iterrows():
                if 'properties' in row and pd.notna(row['properties']):
                    try:
                        properties_str = row['properties'].strip('"').replace('""', '"')
                        properties = json.loads(properties_str)
                        all_properties.update(properties.keys())
                    except json.JSONDecodeError:
                        continue
            
            # Create property structure for all unique properties
            property_structure = [
                {
                    "IsMandatory": False,
                    "InputType": 11,
                    "SearchInputType": 11,
                    "Mask": None,
                    "Values": None,
                    "IsLabel": False,
                    "IsIndex": False,
                    "Grouping": None,
                    "Name": prop_name,
                    "DisplayName": prop_name,
                    "MetaType": self.generate_metatype(),
                    "DataType": 4
                }
                for prop_name in sorted(all_properties)
            ]
            
            # Create the link structure
            link = {
                "Label": None,
                "EndsTypes": [
                    {
                    "type1": combo['type1'],
                    "type2": combo['type2']
                    }
                ],
                "Color": self.generate_random_color(),
                "IsSymmetricLink": False,
                "ShowArrows": True,
                "DisplayName": combo['type'],
                "Name": combo['type'],
                "MetaType": self.generate_metatype(),
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
            
    def merge_duplicate_links(self,json_data):
        if "Links" not in json_data:
            return json_data
        
        # Group links by Name
        links_by_name = {}
        for link in json_data["Links"]:
            name = link["Name"]
            if name not in links_by_name:
                links_by_name[name] = []
            links_by_name[name].append(link)
        
        # Merge duplicates
        merged_links = []
        for name, links in links_by_name.items():
            if len(links) == 1:
                merged_links.append(links[0])
            else:
                # Create merged link from first occurrence
                merged_link = links[0].copy()
                # Combine all EndsTypes
                all_ends_types = []
                for link in links:
                    all_ends_types.extend(link["EndsTypes"])
                # Remove duplicates from EndsTypes based on type1+type2 combination
                unique_ends_types = []
                seen = set()
                for end_type in all_ends_types:
                    key = f"{end_type['type1']}-{end_type['type2']}"
                    if key not in seen:
                        seen.add(key)
                        unique_ends_types.append(end_type)
                merged_link["EndsTypes"] = unique_ends_types
                merged_links.append(merged_link)
        
        json_data["Links"] = merged_links
        
        with open("datamodel.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            
    def generate_dcj_and_dm(self, entities_csv, links_csv):
        
        data = self.generate_entities_from_csv(entities_csv)
        self.add_links_from_csv(links_csv, data)
        self.save_dcj(data, os.path.join(os.getcwd()+'\dcj.json'))
        
        self.generate_links_for_dm_from_csv(links_csv, os.path.join(os.getcwd()+'\links_dm.json'))
        
        self.add_links_to_dm(os.path.join(os.getcwd()+'\links_dm.json'), os.path.join(os.getcwd()+'\datamodelBase.json'))
        with open(os.path.join(os.getcwd()+'\datamodel.json'), 'r', encoding='utf-8') as f:
            datamodel = json.load(f)
        self.merge_duplicate_links(datamodel)
    
    


def main():
    converter = dataConverterForSE()
    converter.generate_dcj_and_dm('entities.csv', 'links.csv')

if __name__ == "__main__":
    main()