

from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain_ollama.llms import OllamaLLM
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import TextRequestsWrapper
import yaml
from typing import Optional, Dict, Any
import logging


class SwaggerToolkit:
    def __init__(self, yaml_path: str = "testroute2.yaml", base_url: str = "192.168.100.149:8537", model_name: str ="llama3.1:70b"):
        """
        Initialize the Weather API Toolkit.
        
        Args:
            yaml_path: Path to OpenAPI specification YAML file
            base_url: Base URL for the Ollama LLM service
        """
        self.model_name = model_name
        self.yaml_path = yaml_path
        self.base_url = base_url
        self.agent = self._create_api_toolkit()
        
    def _create_api_toolkit(self) -> AgentType:
        """
        Create and configure the OpenAPI toolkit with requests wrapper.
        
        Returns:
            AgentType: Configured API agent
        """
        try:
            # Load and reduce OpenAPI spec
            with open(self.yaml_path) as f:
                raw_openai_api_spec = yaml.load(f, Loader=yaml.Loader)
            openai_api_spec = reduce_openapi_spec(raw_openai_api_spec)
            
            # Configure headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            requests_wrapper = TextRequestsWrapper(headers=headers)
            
            # Initialize LLM
            llm = OllamaLLM(
                temperature=0,
                base_url=self.base_url,
                model=self.model_name,
                verbose=True
            )
            
            # Create agent
            return planner.create_openapi_agent(
                api_spec=openai_api_spec,
                llm=llm,
                requests_wrapper=requests_wrapper,
                allow_dangerous_requests=True,
                verbose=True
            )
            
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
        print("\nWeather Information Assistant")
        print("Ask me anything about the weather!")
        print("\nExample questions:")
        print("- What's the weather like in Roma today?")
        print("- Is it sunny in Milano right now?")
        print("- Tell me the temperature in Napoli")
        print("- How's the weather in Florence?")
        
        while True:
            question = input("\nWhat would you like to know about the weather? (type 'quit' to exit): ")
            if question.lower() == 'quit':
                break
                
            try:
                result = self.ask_question(question)
                print(f"Response: {result}")
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Entry point for the weather API toolkit."""
    try:
        weather_toolkit = SwaggerToolkit()
        weather_toolkit.run_interactive_cli()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        
if __name__ == "__main__":
    main()