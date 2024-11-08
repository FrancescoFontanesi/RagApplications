from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, request, jsonify
from flask_swagger import swagger
import logging

# Creazione dell'applicazione Flask
app = Flask(__name__)



# Configurazione del logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s - %(name)s : %(message)s',
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("app.py")

# Configurazione del logger per il modulo requests
swaggerui_blueprint = get_swaggerui_blueprint(
    "/swagger",
    "/swagger-file",
    config={
        'app_name': "test-rag",
        'version': "0.0.1"
    }
)

app.register_blueprint(swaggerui_blueprint)


@app.route("/swagger-file")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "0.0.1"
    swag['info']['title'] = "test-rag"
    return jsonify(swag)


@app.route('/', methods=['GET'])
def home():
    """
    Return the status of the service
    ---
    produces:
        text/plain
    responses:
        200:
            description: return the status of the service
    """
    return "funziona!"



# Avviare il server Flask
if __name__ == "__main__":
    app.run(debug=True)
