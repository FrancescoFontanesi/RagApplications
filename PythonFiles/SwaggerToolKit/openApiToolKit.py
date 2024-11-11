

from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain_ollama.llms import OllamaLLM
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import TextRequestsWrapper
import yaml
from typing import Optional, Dict, Any
import logging
import json


class SwaggerToolkit:
    def __init__(self, json_path: str = "swaggerS&A.json", base_url: str = "192.168.100.149:8537", model_name: str ="llama3.1:latest", bearer_token: str =""):
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
        self.yaml_path = "swaggerSEA.yaml"

        self.agent = self._create_api_toolkit()
        
    def _create_api_toolkit(self) -> AgentType:
        """
        Create and configure the OpenAPI toolkit with requests wrapper.
        
        Returns:
            AgentType: Configured API agent
        """
        try:
            logging.debug("Loading OpenAPI specification from JSON file.")
            
            # Load and convert JSON to YAML
            """with open(self.json_path) as f:
                raw_openapi_api_spec = json.load(f)
                logging.debug("Raw OpenAPI spec loaded successfully.")
                yaml_openapi_api_spec = yaml.dump(raw_openapi_api_spec)
                logging.debug("OpenAPI spec converted to YAML successfully.")
                openapi_api_spec = reduce_openapi_spec(yaml.safe_load(yaml_openapi_api_spec))
                logging.debug("OpenAPI spec reduced successfully.")  """
            
            with open(self.yaml_path) as f:
                raw_openai_api_spec = yaml.load(f, Loader=yaml.Loader)
            openapi_api_spec = reduce_openapi_spec(raw_openai_api_spec)
            
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.auth}"
            }
            logging.debug(f"Headers set: {headers}")
            
            requests_wrapper = TextRequestsWrapper(headers=headers)
            logging.debug("Requests wrapper initialized successfully.")
            
            # Initialize LLM
            llm = OllamaLLM(
                temperature=0,
                base_url=self.base_url,
                model=self.model_name,
                verbose=True
            )
            logging.debug("LLM initialized successfully.")
            
            # Create agent
            agent = planner.create_openapi_agent(
                api_spec=openapi_api_spec,
                llm=llm,
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

    try:
        logging.debug("Initializing SwaggerToolkit with provided bearer token.")
        weather_toolkit = SwaggerToolkit(bearer_token=bearer_token)
        logging.debug("SwaggerToolkit initialized successfully.")
        weather_toolkit.run_interactive_cli()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
if __name__ == "__main__":
    main()