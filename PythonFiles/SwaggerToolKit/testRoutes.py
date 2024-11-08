from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, request, jsonify
from flask_swagger import swagger
import logging
import random

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
        'app_name': "test",
        'version': "0.0.1"
    }
)

app.register_blueprint(swaggerui_blueprint)

# Mock weather conditions
CONDIZIONI_METEO = [
    "Soleggiato",
    "Parzialmente nuvoloso",
    "Nuvoloso",
    "Piovoso",
    "Temporale"
]

def get_weather_conditions(temperature):
    if temperature >= 25:
        return "Soleggiato"
    elif temperature >= 20:
        return "Parzialmente nuvoloso"
    elif temperature >= 15:
        return "Nuvoloso"
    elif temperature >= 10:
        return "Piovoso"
    else:
        return "Temporale"

@app.route("/swagger-file")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "0.0.1"
    swag['info']['title'] = "test"
    return jsonify(swag)
'''
@app.route('/meteo', methods=['POST'])
def ottieni_meteo():
    """
    Ottieni le condizioni meteo per una città specificata.
    ---
    tags:
      - Weather
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - citta
          properties:
            citta:
              type: string
              description: Nome della città
    responses:
      200:
        description: Dati meteo generati con successo
        schema:
          type: object
          properties:
            citta:
              type: string
              description: Nome della città richiesta
            temperatura:
              type: number
              format: float
              description: Temperatura in gradi Celsius
            condizioni:
              type: string
              description: Condizioni meteo attuali
      400:
        description: Errore nella richiesta
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
      500:
        description: Errore interno del server
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
    """
    try:
        dati = request.get_json()
        
        # Input validation
        if not dati or 'citta' not in dati:
            return jsonify({
                "errore": "È necessario specificare una città nella richiesta"
            }), 400
        
        citta = dati['citta']
        
        # Generate mock weather data
        dati_meteo = {
            "citta": citta,
            "temperatura": round(random.uniform(15.0, 30.0), 1),
            "condizioni": random.choice(CONDIZIONI_METEO)
        }
        
        return jsonify(dati_meteo), 200
        
    except Exception as e:
        return jsonify({
            "errore": f"Errore interno del server: {str(e)}"
        }), 500
'''


@app.route('/meteo', methods=['POST'])
def ottieni_meteo():
    """
    Ottieni le condizioni meteo in base alla temperatura fornita.
    ---
    tags:
      - Weather
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - temperatura
          properties:
            temperatura:
              type: number
              format: float
              description: Temperatura in gradi Celsius
    responses:
      200:
        description: Condizioni meteo basate sulla temperatura
        schema:
          type: object
          properties:
            temperatura:
              type: number
              format: float
              description: Temperatura fornita
            condizioni:
              type: string
              description: Condizioni meteo stimate
      400:
        description: Errore nella richiesta
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
      500:
        description: Errore interno del server
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
    """
    try:
        dati = request.get_json()
        
        # Input validation
        if not dati or 'temperatura' not in dati:
            return jsonify({
                "errore": "È necessario specificare una temperatura nella richiesta"
            }), 400
        
        temperatura = dati['temperatura']
        
        # Get weather condition based on temperature
        condizioni = get_weather_conditions(temperatura)
        
        return jsonify({
            "temperatura": temperatura,
            "condizioni": condizioni
        }), 200
        
    except Exception as e:
        return jsonify({
            "errore": f"Errore interno del server: {str(e)}"
        }), 500
        
        

@app.route('/temperatura', methods=['POST'])
def ottieni_temperatura():
    """
    Ottieni la temperatura per una città specificata.
    ---
    tags:
      - Weather
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - citta
          properties:
            citta:
              type: string
              description: Nome della città
    responses:
      200:
        description: Temperatura ottenuta con successo
        schema:
          type: object
          properties:
            citta:
              type: string
              description: Nome della città richiesta
            temperatura:
              type: number
              format: float
              description: Temperatura in gradi Celsius
      400:
        description: Errore nella richiesta
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
      500:
        description: Errore interno del server
        schema:
          type: object
          properties:
            errore:
              type: string
              description: Messaggio di errore
    """
    try:
        dati = request.get_json()
        
        # Input validation
        if not dati or 'citta' not in dati:
            return jsonify({
                "errore": "È necessario specificare una città nella richiesta"
            }), 400
        
        citta = dati['citta']
        
        # Generate mock temperature data
        temperatura = round(random.uniform(15.0, 30.0), 1)
        
        return jsonify({
            "citta": citta,
            "temperatura": temperatura
        }), 200
        
    except Exception as e:
        return jsonify({
            "errore": f"Errore interno del server: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)