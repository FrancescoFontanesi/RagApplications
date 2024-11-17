

from langchain.agents import AgentType, initialize_agent
from langchain.chains import LLMChain
from langchain_ollama.llms import OllamaLLM
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import TextRequestsWrapper
from typing import  Dict, Any
import logging
from operator import itemgetter
from langchain_core.prompts import PromptTemplate
import json
import requests
import os 
from dotenv import load_dotenv
load_dotenv()


class SwaggerToolkit:
    def __init__(self, json_path: str = "enhanced_swagger copy.json", base_url: str = os.getenv("OLLAMA_URL"), model_name: str ="llama3.1:latest", bearer_token: str =""):
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
        self.llm = OllamaLLM(
                    temperature=0,
                    base_url=self.base_url,
                    model=self.model_name,
                    verbose=True
                )

        self.agent = self._create_api_toolkit()
        print(os.getenv("OLLAMA_URL"))
        
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
            
            print(openapi_api_spec)
            
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
                
class ReducedSwagger:
    def __init__(self, specs, swagger_description, server_url):
        self.specs = specs
        self.swagger_description = swagger_description
        self.server_url = server_url

    def __str__(self):
        return json.dumps({
            "specs": self.specs,
            "swagger_description": self.swagger_description,
            "server_url": self.server_url
        }, indent=4)
        

def extract_specs(swagger_json):
    specs = {}
    for path, methods in swagger_json.get('paths', {}).items():
        for method, details in methods.items():
            specs[path] = {
                'method': method.upper(),
                'description': details.get('description', '')
            }
    return specs

def format_specs(specs):
    formatted_specs = ""
    for path, details in specs.items():
        formatted_specs += f"Path: {path}\n"
        formatted_specs += f"Method: {details['method']}\n"
        formatted_specs += f"Description: {details['description']}\n\n"
    return formatted_specs

def extract_request_bodies(swagger_json):
    request_bodies = {}
    for path, methods in swagger_json.get('paths', {}).items():
        for method, details in methods.items():
            request_body = details.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
            request_bodies[path] = request_body
    return request_bodies

def extract_swagger_description(swagger_json):
    return swagger_json.get('info', {}).get('description', '')

def extract_server_url(swagger_json):
    servers = swagger_json.get('servers', [])
    if servers:
        return servers[0].get('url', '')
    return ''

def create_reduced_swagger(swagger_json):
    specs = extract_specs(swagger_json)
    swagger_description = extract_swagger_description(swagger_json)
    server_url = extract_server_url(swagger_json)
    
    reduced_spec = ReducedSwagger(specs, swagger_description, server_url)
    return reduced_spec



def main():
    """Entry point for the weather API toolkit."""
    
    logging.basicConfig(level=logging.DEBUG)
    
    with open("bearer_token.txt", 'r') as f:
        bearer_token = f.read().strip()
    
    swagger_toolkit = SwaggerToolkit(bearer_token=bearer_token)

    """
    swagger_toolkit._create_api_toolkit()


    try:
        logging.debug("Initializing SwaggerToolkit with provided bearer token.")
        swagger_toolkit = SwaggerToolkit(bearer_token=bearer_token)
        logging.debug("SwaggerToolkit initialized successfully.")
        swagger_toolkit.run_interactive_cli()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")"""
    
    with open("enhanced_swagger copy.json") as f:
        swagger_json = json.load(f)
    reduced_spec = create_reduced_swagger(swagger_json)
    prompt1 = PromptTemplate(
        input_variables=["specs", "user_query"],
        template=
        """
You are a **Planner Agent** tasked with achieving user goals by intelligently utilizing available API calls. Your primary responsibility is to analyze the user's query and, based on the provided API specifications, determine the optimal usage of API calls necessary to accomplish the goal. You must strictly adhere to the given API specifications and cannot assume the existence of unlisted endpoints or external actions.

---

### **Available APIs**
You have access to the following API endpoints. Each endpoint includes its path, method (e.g., GET, POST), input parameters, output structure, and description.
This is a static process, the user query will not include additional information outside the one he provides.
{specs}

---

### **User Query**

This is the goal to achieve:
{user_query}


---

### **Objective**

Your goal is to create a clear, step-by-step plan to achieve the user's objective. Follow these guidelines to ensure your plan is logical, efficient, and aligned with the user's requirements:

---

### **Requirements for the Plan**

- **Necessary Steps Only**: Include only the steps essential for achieving the goal. Avoid redundant or superfluous actions.
- **Clear and Followable**: Ensure the plan is easy to understand, as it will be executed by another LLM chain.
- **Logical Completion**: If the user’s goal can be met through reasoning with the API outputs, conclude without extra steps.

---

### **Output Format**

**Step (n):**
- **Action:** What this step achieves.
- **API Endpoint:** The exact endpoint to be used (path and method).
- **Inputs:** Parameters to send with the API call.
- **Expected Outcome:** The result of the API call and its role in subsequent steps.
- **Logical Interpretation:** The output answer to this question "{user_query}" ? .

If the user goal can be achieved through logical interpretation of the output, conclude the plan with the reasoning and omit unnecessary steps.
""")
    
    prompt2 = PromptTemplate(
        input_variables=["api_output", "step_details", "user_query"],
        template=
        """
You are an **Analysis Agent** responsible for interpreting the results of API calls made as part of a plan to achieve a user's goal. Your task is to carefully evaluate the output of an API call against the step description and assess whether this step resolves the user's query or if further steps are needed.

---

### **Input Information**
**Step Details**:
- {step_details}

**API Call Output**:
- {api_output}

**User Query**:
- {user_query}

---

### **Objective**

Your goal is to interpret the API output in the context of the plan and the user's query to determine if the output successfully resolves the user's objective. If it does not, analyze why and suggest what additional steps or reasoning may be needed to achieve the goal.

---

### **Requirements for the Analysis**

- **Relevance Check**: Determine if the API output is relevant to the user's query and aligns with the expected outcome of the step.
- **Resolution Assessment**: Assess whether the output and reasoning from this step are sufficient to resolve the user's query. 
- **Next Steps (If Needed)**: If the query is not resolved, outline what additional steps, reasoning, or actions should follow.

---

### **Output Format**

**Final answer to the question**
"""
)

    chain = (
        {"specs": itemgetter("specs"),
         "user_query": itemgetter("user_query")}
        | prompt1
        | swagger_toolkit.llm
    )
    
    result = chain.invoke({
        "specs": format_specs(reduced_spec.specs),
        "user_query": "Esiste Michele Senese?"
    })
    
    print(result)
    
    chain = (
        {"step_details": itemgetter("step_details"),
         "user_query": itemgetter("user_query"),
         "api_output": itemgetter("api_output")}
        | prompt2
        | swagger_toolkit.llm
    )
    
    out = chain.invoke({
        "step_details": result,
        "user_query": "Esiste Michele Senese?",
        "api_output": "[1]"
    })
    
    print(out)
    
    prompt3 = PromptTemplate(
        input_variables=["answer"],
        template=
        """
You are a **Final Agent** tasked with evaluating the final answer to a user query. Your role is to assess the validity and correctness of the answer provided by the previous agents and determine if it is a satisfactory response to the user's query.
Interpret this : {answer} and give a final answer to the question {question}.
""")
    
    chain = (
        {"answer": itemgetter("answer"),
        "question": itemgetter("question")}
        | prompt3
        | swagger_toolkit.llm
    )
    
    final = chain.invoke({
        "answer": out,
        "question": "Esiste Michele Senese?"
    })
    
    print(final)
    
    """
    reduced_spec = create_reduced_swagger(swagger_json)
    print(reduced_spec)
    print(format_specs(reduced_spec.specs))
"""
    
    
if __name__ == "__main__":
    main()