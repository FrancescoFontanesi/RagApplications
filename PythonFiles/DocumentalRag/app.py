from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, request, jsonify
import logging
from flask_swagger import swagger
from enum import Enum
import psycopg2
from typing import List
import VectorToolKit as vs  # Import the VectorToolKit class
from LLMToolKit import RagPipeline as rag  # Import the RagPipeline class
from dotenv import load_dotenv

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


class SchemasNames(Enum):
    """
    SchemasNames is an enumeration that represents different schema names used in the application.

    Attributes:
        DB0 (str): Represents the schema name "Overlap0".
        DB5 (str): Represents the schema name "Overlap0.5".
        DB10 (str): Represents the schema name "Overlap1".
        DB15 (str): Represents the schema name "Overlap1.5".
        DB20 (str): Represents the schema name "Overlap2".
        DB25 (str): Represents the schema name "Overlap2.5".
        DB30 (str): Represents the schema name "Overlap3".
        DB_HYBRID_54 (str): Represents the schema name "Hybrid64".
        DB_HYBRID_128 (str): Represents the schema name "Hybrid128".
        DB_HYBRID_64 (str): Represents the schema name "Hybrid64".
        DB_HYBRID_256 (str): Represents the schema name "Hybrid256".
    """
    DB30 = "Overlap3"
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


schemas_enum = {
    # Overlap schemas with different overlap percentages

    SchemasNames.DB30: SchemaType.OVERLAP,    # 30% overlap between chunks

    # Hybrid schemas with different small chunk sizes (64-256 tokens)
    # Large chunks split into 128-token pieces
    SchemasNames.DB_HYBRID_128: SchemaType.HYBRID,

}
"""
Maps schema names to their types (OVERLAP or HYBRID).

OVERLAP schemas use different percentages of overlap between adjacent text chunks.
HYBRID schemas use a two-level chunking strategy where large chunks are split into
smaller pieces of specified token sizes.

The schema name indicates either:
- The overlap percentage (e.g. DB5 = 5% overlap)
- The schemas_enum: Dict[SchemasNames, SchemaType] = {
    # Overlap schemas with different overlap percentages (0-30%)
    SchemasNames.DB0: SchemaType.OVERLAP,     # No overlap between chunks
    SchemasNames.DB5: SchemaType.OVERLAP,     # 5% overlap between chunks
    SchemasNames.DB10: SchemaType.OVERLAP,    # 10% overlap between chunks
    SchemasNames.DB15: SchemaType.OVERLAP,    # 15% overlap between chunks
    SchemasNames.DB20: SchemaType.OVERLAP,    # 20% overlap between chunks
    SchemasNames.DB25: SchemaType.OVERLAP,    # 25% overlap between chunks
    SchemasNames.DB30: SchemaType.OVERLAP,    # 30% overlap between chunks
    
    # Hybrid schemas with different small chunk sizes (64-256 tokens)
    SchemasNames.DB_HYBRID_54: SchemaType.HYBRID,    # Large chunks split into 64-token pieces
    SchemasNames.DB_HYBRID_128: SchemaType.HYBRID,   # Large chunks split into 128-token pieces
    SchemasNames.DB_HYBRID_192: SchemaType.HYBRID,   # Large chunks split into 192-token pieces
    SchemasNames.DB_HYBRID_256: SchemaType.HYBRID    # Large chunks split into 256-token pieces
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


@app.route('/init', methods=['GET'])
def init():
    pass


def get_available_schemas() -> List[str]:
    """
    Returns a list of available schema names from the SchemasNames enum.

    Returns:
        List[str]: List of schema names (e.g., ["Overlap0", "Overlap0.5", ...])
    """
    return [schema_name for schema_name in SchemasNames]


def get_connection_to_sql_database(
    host: str,
    username: str,
    password: str,
    data_base_name: str = "Manuale Tetras",
    schema_name: str = SchemasNames.DB_HYBRID_128.value[0]
) -> psycopg2.extensions.connection:
    """
    Creates a connection to the PostgreSQL database with the specified schema.

    Args:
        host (str): Database host address
        username (str): Database username
        password (str): Database password
        data_base_name (str): Database name (default: "Manuale Tetras")
        schema_name (str): Schema name (default: Hybrid128)

    Returns:
        psycopg2.extensions.connection: Database connection object
    """
    return psycopg2.connect(
        host=host,
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


@app.route('/')
def index():
    return 'Hello, World!'


@app.route('/methods', methods=['GET'])
def get_methods():
    """
    Endpoint to retrieve all available database schemas.

    Returns:
        JSON response containing array of schema names

    Example Response:
        [
            "Overlap0",
            "Overlap0.5",
            "Overlap1",
            "Overlap1.5",
            "Overlap2",
            "Overlap2.5",
            "Overlap3",
            "Hybrid64",
            "Hybrid128",
            "Hybrid192",
            "Hybrid256"
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
                example: ["Overlap0", "Overlap0.5", "Hybrid128"]
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
    print(schemas)
    try:
        return jsonify([schema.value for schema in schemas]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def vectorial_query(question, schema):

    conn = get_connection_to_sql_database(schema_name=schema)

    results = VectorTool.query_selector(
        schemas_enum[schema], conn, question, 5)
    return results


@app.route('/save', methods=['POST'])
def save():
    """
    Endpoint to perform vector similarity search using specified schema.
    ---
    tags:
    - Save
    summary: Perform vector similarity search using specified schema 
    description: Performs semantic search using specified schema and question returning the top 5 matching results as a 
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
                            description: Schema name to use for search
                            enum: [DB0, DB5, DB10, DB15, DB20, DB25, DB30, DB_HYBRID_54, DB_HYBRID_128, DB_HYBRID_192, DB_HYBRID_256]
                        question:
                            type: string
                            description: Query text to search for
    responses:
        200:
            description: Search results
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            results:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        content: 
                                            type: string
                                        index: 
                                            type: string
                                        similarity:
                                            type: number
                                            format: float
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

        results = vectorial_query(question, schema)

        formatted_results = [
            {
                'content': result[0],
                'index': result[1],
                'similarity': float(result[2])
            }
            for result in results
        ]

        return jsonify({
            'results': formatted_results,
            'count': len(formatted_results)
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


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
                            enum: [DB0, DB5, DB10, DB15, DB20, DB25, DB30, DB_HYBRID_54, DB_HYBRID_128, DB_HYBRID_192, DB_HYBRID_256]
                        question:
                            type: string
                            description: Question text to answer
    responses:
        200:
            description: Answer to the question
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
        results = VectorTool.query_selector(
            schemas_enum[schema], conn, question, 5)

        # Answer the question using the results
        answer, indecies = RagTool.answer_qestion(results, question)

        return jsonify({
            'answer': answer,
            'indecies': indecies
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
