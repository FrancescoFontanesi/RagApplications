import requests
import json
import yaml
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Define the Swagger file URL
SWAGGER_URL = "http://localhost:5000/swagger-file"

class SwaggerEnhancer:
    def __init__(self, swagger_url, model_name="llama3.1:70b", temperature=0.2, base_url="http://192.168.100.149:8537"):
        self.swagger_url = swagger_url
        self.swagger_json = None
        self.swagger_yaml = None
        self.enhanced_yaml = None
        self.ollama_llm = OllamaLLM(model=model_name, temperature=temperature, base_url=base_url)

    def fetch_swagger_json(self):
        response = requests.get(self.swagger_url)
        if response.status_code == 200:
            self.swagger_json = response.json()
        else:
            raise ValueError("Failed to retrieve the Swagger JSON file.")
        return self

    def convert_to_yaml(self):
        if not self.swagger_json:
            raise ValueError("No Swagger JSON to convert. Call fetch_swagger_json first.")
        self.swagger_yaml = yaml.dump(self.swagger_json, default_flow_style=False)
        return self

    def enhance_yaml(self):
        if not self.swagger_yaml:
            raise ValueError("No YAML to enhance. Call convert_to_yaml first.")
        
        prompt = PromptTemplate(
            input_variables=["yaml_content"],
            template=(
                "You are an helpfull assistant designed to enhance API documentation YAML files. "
                "Make the following YAML more informative, add explanations where needed, "
                "ensure it follows best practices for API documentation including the server and info field:\n\n"
                "{yaml_content}"
            )
        )
        
        sequence = prompt | self.ollama_llm
        self.enhanced_yaml = sequence.invoke(input=self.swagger_yaml)
        return self

    def save_to_file(self, filename="enhanced_swagger.yaml"):
        if not self.enhanced_yaml:
            raise ValueError("No enhanced YAML to save. Call enhance_yaml first.")
        with open(filename, "w") as file:
            file.write(self.enhanced_yaml)
        return self

def main():
    # Create an instance of SwaggerEnhancer and process the swagger file
    enhancer = SwaggerEnhancer(SWAGGER_URL)
    """enhancer.fetch_swagger_json()\
            .convert_to_yaml()\
            .enhance_yaml()\
            .save_to_file()"""
            
    

if __name__ == "__main__":
    main()
