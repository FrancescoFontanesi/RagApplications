

from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain_ollama.llms import OllamaLLM
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import TextRequestsWrapper
import yaml
from typing import  Dict, Any
import logging
import json
import requests
import os 



from langchain.agents import create_openapi_agent
from langchain_community.agent_toolkits import OpenAPIToolkit
from langchain_community.tools.json.tool import JsonSpec

class SwaggerToolkit:
    def __init__(self, json_path: str = "enhanced_swagger copy.json", base_url: str = os.getenv("OLLAMA_URL"), model_name: str ="llama3.1:70b", bearer_token: str =""):
        """
        Initialize the Weather API Toolkit.
        
        Args:
            yaml_path: Path to OpenAPI specification YAML file
            base_url: Base URL for the Ollama LLM service
        """
        self.model_name = model_name
        self.json_path = json_path
        self.base_url = base_url
        self.auth = bearer_token
        self.swagger_json = None

        #self.agent = self._create_api_toolkit()
        
        self.llm = OllamaLLM(
                    temperature=0,
                    base_url=self.base_url,
                    model=self.model_name,
                    verbose=True
                )
    
    
    def fetch_swagger_json(self):
        response = requests.get(os.getenv("SWAGGER_URL"))
        if response.status_code == 200:
            self.swagger_json = response.json()
        else:
            raise ValueError("Failed to retrieve the Swagger JSON file.")
        return self
        

# Now reduced_spec can be used with _create_api_controller_tool
        
    def _create_api_toolkit(self) -> AgentType:
        """
        Create and configure the OpenAPI toolkit with requests wrapper.
        
        Returns:
            AgentType: Configured API agent
        """
        try:
            logging.debug("Loading OpenAPI specification from JSON file.")
            
            # Load and convert JSON to YAML
            with open(self.json_path) as f:
                raw_openapi_api_spec = json.load(f)
                openapi_api_spec = reduce_openapi_spec(raw_openapi_api_spec)
                logging.debug("OpenAPI spec reduced successfully.")  
            
            """with open(self.yaml_path) as f:
                raw_openai_api_spec = yaml.load(f, Loader=yaml.Loader)
            openapi_api_spec = reduce_openapi_spec(raw_openai_api_spec)"""
            
            headers = {
                "Authorization": f"Bearer {self.auth}"
            }
            logging.debug(f"Headers set: {headers}")
            
            requests_wrapper = TextRequestsWrapper(headers=headers)
            logging.debug("Requests wrapper initialized successfully.")
            
            # Initialize LLM
            
            logging.debug("LLM initialized successfully.")
            
            # Create agent
            agent = planner.create_openapi_agent(
                api_spec=openapi_api_spec,
                llm=self.llm,
                requests_wrapper=requests_wrapper,
                allow_dangerous_requests=True,
                verbose=True
            )
            logging.debug("OpenAPI agent created successfully.")
            return agent
            
        except Exception as e:
            logging.error(f"Failed to create API toolkit: {str(e)}")
            raise
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Query the weather API using natural language.
        
        Args:
            question: Natural language weather query
            
        Returns:
            Dict containing the API response
        """
        try:
            response = self.agent.invoke(question)
            return response
        except Exception as e:
            logging.error(f"Error processing question: {str(e)}")
            raise
    
    def run_interactive_cli(self):
        """Launch an interactive CLI for weather queries."""
        while True:
            question = input("\nHow can i help?(type 'quit' to exit): ")
            if question.lower() == 'quit':
                break
                
            try:
                result = self.ask_question(question)
                print(f"Response: {result}")
            except Exception as e:
                print(f"Error: {str(e)}")
                
def main():
    """Entry point for the weather API toolkit."""
    
    logging.basicConfig(level=logging.DEBUG)

    with open("bearer_token.txt", 'r') as f:
        bearer_token = f.read().strip()
    
    swagger_toolkit = SwaggerToolkit(bearer_token=bearer_token)
    swagger_toolkit._create_api_toolkit()


    """try:
        logging.debug("Initializing SwaggerToolkit with provided bearer token.")
        swagger_toolkit = SwaggerToolkit(bearer_token=bearer_token)
        logging.debug("SwaggerToolkit initialized successfully.")
        swagger_toolkit.run_interactive_cli()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")"""
if __name__ == "__main__":
    main()