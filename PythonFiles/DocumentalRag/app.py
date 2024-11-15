from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, request, jsonify
import logging
from flask_swagger import swagger
from enum import Enum
import psycopg2
from typing import List
import VectorToolKit as vs  # Import the VectorToolKit class
from LLMToolKit import RagPipeline as rag  # Import the RagPipeline class
import DataProcessing as dp  # Import the Dataprocessing class
from dotenv import load_dotenv
import os
load_dotenv()



# Create Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s - %(name)s : %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app.py")

# Configure Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    "/swagger",
    "/swagger-file",
    config={
        'app_name': "Documental Rag",
        'version': "0.0.1"
    }
)

app.register_blueprint(swaggerui_blueprint)
VectorTool = vs.VectorToolKit()
RagTool = rag()
DataProcessor = dp.DocumentProcessor()


class SchemasNames(Enum):
    """
    SchemasNames is an enumeration that represents different schema names used in the application.

    Attributes:
        DB30 (str): Represents the schema name "Overlap30"
        DB_HYBRID_128 (str): Represents the schema name "Hybrid128".
        
    """
    DB30 = "Overlap30"
    DB_HYBRID_128 = "Hybrid128"

class SchemaType(Enum):
    """
    SchemaType is an enumeration that defines different types of schemas.

    Attributes:
        OVERLAP (int): Represents the overlap schema type with a value of 2.
        HYBRID (int): Represents the hybrid schema type with a value of 1.
    """
    OVERLAP = 2
    HYBRID = 1

schemas_enum_overlap = {
    # Overlap schemas with different overlap percentages 
    
    SchemasNames.DB30: SchemaType.OVERLAP,    # 30% overlap between chunks
    
    
}
schemas_enum_hybrid = {
    # Hybrid schemas with different small chunk sizes (64-256 tokens)
    SchemasNames.DB_HYBRID_128: SchemaType.HYBRID,    # Large chunks split into 128-token pieces
}

schemas_enum = {
    **schemas_enum_overlap,
    **schemas_enum_hybrid
}


    
"""
Maps schema names to their types (OVERLAP or HYBRID).

OVERLAP schemas use different percentages of overlap between adjacent text chunks.
HYBRID schemas use a two-level chunking strategy where large chunks are split into
smaller pieces of specified token sizes.

The schema name indicates either:
- The overlap percentage (e.g. DB5 = 5% overlap)
- The schemas_enum: Dict[SchemasNames, SchemaType] = {
    # Overlap schemas with different overlap percentage

    SchemasNames.DB30: SchemaType.OVERLAP,    # 30% overlap between chunks
    
    # Hybrid schemas with different small chunk size
    
    SchemasNames.DB_HYBRID_128: SchemaType.HYBRID,   # Large chunks split into 128-token pieces

}
"""

VERSION = "1.0.0"
APP_NAME = "Documental Rag"

@app.route("/swagger-file")
def spec():
    swag = swagger(app)
    swag['info']['version'] = VERSION
    swag['info']['title'] = APP_NAME
    return jsonify(swag)


def get_available_schemas() -> List[str]:
    """
    Returns a list of available schema names from the SchemasNames enum.
    
    Returns:
        List[str]: List of schema names (e.g., ["Overlap0", "Overlap0.5", ...])
    """
    return [schema_name for schema_name in SchemasNames]

def get_connection_to_sql_database(
    host: str = os.getenv("HOST"),
    port: str = os.getenv("PORT"),
    username: str = os.getenv("USERNAME"),
    password: str = os.getenv("PASSWORD"),
    data_base_name: str = "postgres",
    schema_name: str = SchemasNames.DB_HYBRID_128.value[0]
) -> psycopg2.extensions.connection:
    """
    Creates a connection to the PostgreSQL database with the specified schema.
    
    Args:
        host (str): Database host address
        username (str): Database username
        password (str): Database password
        data_base_name (str): Database name (default: "postgres")
        schema_name (str): Schema name (default: Hybrid128)
        
    Returns:
        psycopg2.extensions.connection: Database connection object
    """
    return psycopg2.connect(
        host=host,
        port = port,
        dbname=data_base_name,
        user=username,
        password=password,
        options=f"-c search_path={schema_name}"
    )

@app.route('/swagger-file')
def swagger_file():
    """
    Endpoint to serve the Swagger file.
    
    Returns:
        Swagger file content
    """
    return app.send_from_directory('swagger.json')





"""
    Initializes the database with schemas for different types of chunking.

    This route triggers the `init_for_sea` method of the `DataProcessor` class, which performs the following steps:
    1. Extracts subtitles and text from the document.
    2. Generates chunked dictionaries with different overlap percentages.
    3. Generates hybrid chunked dictionaries with different chunk sizes.
    4. Creates schemas in the SQL database for both overlap and hybrid chunked data.
    5. Inserts the generated data into the respective schemas in the SQL database.

    The schemas for overlap and hybrid chunked data are provided as `schemas_enum_overlap` and `schemas_enum_hybrid` respectively.

    Returns:
        None
"""

@app.route('/init', methods=['GET'])
    
def init():
    """
    @swagger
    paths:
        /init:
            post:
                summary: Initialize the data processor for sea schemas
                description: This endpoint initializes the data processor with the provided sea schemas.
                tags:
                    - DataProcessor
                responses:
                    200:
                        description: Data processor initialized successfully
                    400:
                        description: Bad request, invalid input parameters
    """
    DataProcessor.init_for_sea(schemas_enum_overlap, schemas_enum_hybrid)
    # funziona sulla base degli enum definiti qua dentro, l'utente non ha controllo sul'inizializzazione dei db


@app.route('/methods', methods=['GET'])
def get_methods():
    """
    Endpoint to retrieve all available database schemas.
    
    Returns:
        JSON response containing array of schema names
        
    Example Response:
        [
            "Overlap30",
            "Hybrid64"
        ]
    
    OpenAPI Spec:
    ---
    get:
      summary: Retrieve available schemas
      description: Returns a list of all available database schemas that can be used in the system
      responses:
        '200':
          description: List of available schemas
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string
                example: [ "Overlap30", "Hybrid128"]
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
    """
    schemas = get_available_schemas()
    try:
        return jsonify([schema.value for schema in schemas]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
def vectorial_query(question, schema):
    
    conn = get_connection_to_sql_database(schema_name=schema)
    
    results = VectorTool.query_selector(schemas_enum[schema], conn, question, 5)
    return results



@app.route('/save', methods=['POST'])
def save():
    """
    Endpoint to save user valuation of the answer.
    ---
    tags:
    - Save
    summary: Save user valuation
    description: Save user valuation of the answer  
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - question
                        - answer
                        - valuation type 1
                        - valuation type 2
                        - valuation type 3
                        - valuation type 4
                        - valuation type 5
                    properties:
                        question:
                            type: string
                            description: Question text
                        answer:
                            type: string
                            description: Answer to the question
                        valuation type 1:
                            type: string
                            description: Valuation of to question 1
                        valuation type 2:
                            type: string
                            description: Valuation of to question 2
                        valuation type 3:
                            type: string
                            description: Valuation of to question 3
                        valuation type 4:
                            type: string
                            description: Valuation of to question 4
                        valuation type 5:
                            type: string
                            description: Valuation of to question 5                     
    """
    data = request.get_json()
    
    if not data or 'question' not in data or 'answer' not in data:
        return jsonify({
            'error': 'Missing required parameters',
            'required': ['question', 'answer', 'valuation type 1', 'valuation type 2', 'valuation type 3', 'valuation type 4', 'valuation type 5']
        }), 400
        
    question = data['question']
    answer = data['answer']
    valuation_type_1 = data['valuation type 1']
    valuation_type_2 = data['valuation type 2']
    valuation_type_3 = data['valuation type 3']
    valuation_type_4 = data['valuation type 4']
    valuation_type_5 = data['valuation type 5']
    
    try:
        conn = get_connection_to_sql_database(schema_name='valutation')
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO valutation (question, answer, valuation_type_1, valuation_type_2, valuation_type_3, valuation_type_4, valuation_type_5)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (question, answer, valuation_type_1, valuation_type_2, valuation_type_3, valuation_type_4, valuation_type_5))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Valuation saved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    pass
            
        
@app.route('/question', methods=['POST'])
def question():
    """
    Endpoint to answer a question using the specified schema.
    ---
    tags:
    - Question
    summary: Answer a question
    description: Answers a question using specified schema and question text
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - schema
                        - question
                    properties:
                        schema:
                            type: string
                            description: Schema name to use for answering the question
                            enum: [DB30, DB_HYBRID_128]
                        question:
                            type: string
                            description: Question text to answer
    responses:
        200:
            description: Answer to the question, the indices of the results and the question itself
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            answer:
                                type: string
                            indecies:
                                type: array
                                items:
                                    type: string
                            question:
                                type: string
        400:
            description: Invalid request parameters
        500:
            description: Internal server error
    """
    try:
        data = request.get_json()
        
        if not data or 'schema' not in data or 'question' not in data:
            return jsonify({
                'error': 'Missing required parameters',
                'required': ['schema', 'question']
            }), 400
            
        schema = data['schema']
        question = data['question']
        
        if schema not in schemas_enum:
            return jsonify({
                'error': 'Invalid schema',
                'valid_schemas': list(schemas_enum.keys())
            }), 400
            
        # Create a connection to the database
        conn = get_connection_to_sql_database(schema_name=schema)
        
        # Get the results for the question
        results = VectorTool.query_selector(schemas_enum[schema], conn, question, 5)
        
        # Answer the question using the results
        answer, indecies = RagTool.answer_question(results, question)
        
        return jsonify({
            'answer': answer,
            'indecies': indecies,
            'question': question
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)