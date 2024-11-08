from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify, request
from flask_swagger import swagger
from numba import jit
import numpy as np
import random
app = Flask(__name__)

# Configurazione del blueprint di Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    "/swagger",  # URL per Swagger UI
    "/swagger-file",  # Endpoint che restituisce il file Swagger
    config={
        'app_name': 'Swagger RAG',
        'version': '1.0.0',
    }
)

# Registrare il blueprint di Swagger UI
app.register_blueprint(swaggerui_blueprint)

@jit(nopython=True)
def cosine_similarity(A, B):
    dot_product = 0.0
    norm_A = 0.0
    norm_B = 0.0
    
    for i in range(len(A)):
        dot_product += A[i] * B[i]
        norm_A += A[i] * A[i]
        norm_B += B[i] * B[i]
    
    return dot_product / (np.sqrt(norm_A) * np.sqrt(norm_B))

# Rotta che restituisce il file Swagger
@app.route("/swagger-file")
def spec():
    swag = swagger(app)
    swag['info']['title'] = "RAG API"
    swag['info']['description'] = "API per il calcolo della similarità del coseno e altre funzioni di supporto per il modello RAG"
    swag['info']['version'] = "1.0.0"
    
    
     # Definizione modelli
    swag['definitions'] = {
        'SimilaritaRequest': {
            'type': 'object',
            'required': ['vector1', 'vector2'],
            'properties': {
                'vector1': {
                    'type': 'array',
                    'items': {'type': 'number','format':'float'},
                    'example': [1.0, 2.0, 3.0],
                    'description': 'Primo vettore numerico'
                },
                'vector2': {
                    'type': 'array',
                    'items': {'type': 'number','format':'float'},
                    'example': [4.0, 5.0, 6.0],
                    'description': 'Secondo vettore numerico'
                }
            }
        },
        'SimilaritaResponse': {
            'type': 'object',
            'properties': {
                'similarity': {
                    'type': 'number',
                    'format': 'float',
                    'example': 0.974631,
                    'description': 'Valore della similarità del coseno (tra -1 e 1)'
                }
            }
        },
        'ErroreResponse': {
            'type': 'object',
            'properties': {
                'errore': {
                    'type': 'string',
                    'example': 'I vettori devono avere la stessa dimensione',
                    'description': 'Messaggio di errore'
                }
            }
        }
    }
    
    # Aggiunta tags per organizzare le API
    swag['tags'] = [
        {
            'name': 'Calcoli e valutazioni',
            'description': '''Operazioni relative ai calcoli e alle valutazioni per decidere 
                              parametri fondamnetali''',
        }
    ]

    return jsonify(swag)

    

# Rotta di test semplice
@app.route('/', methods=['GET'])
def test():
    """
    Test di base dell'API
    ---
    responses:
      200:
        description: Conferma che l'API è funzionante
    """
    return "Swagger has been loaded"

@app.route('/cosine-similarity', methods=['POST'])
def calculate_similarity():
    """
    Calcola la similarità del coseno tra due vettori
    ---
    tags:
      - Calcoli e valutazioni 
    parameters:
      - in: body
        name: vectors
        required: true
        schema:
          $ref: '#/definitions/SimilaritaRequest'
        description: Coppia di vettori da confrontare
    responses:
      200:
        description: Calcolo eseguito con successo
        schema:
          $ref: '#/definitions/SimilaritaResponse'
      400:
        description: Errore nei parametri di input
        schema:
          $ref: '#/definitions/ErroreResponse'
    """
    try:
        data = request.get_json()
        if not data or 'vector1' not in data or 'vector2' not in data:
            return jsonify({'errore': 'Richiesti entrambi i vettori (vector1 e vector2)'}), 400

        # Conversione in numpy arrays
        v1 = np.array(data['vector1'], dtype=np.float64)
        v2 = np.array(data['vector2'], dtype=np.float64)

        # Validazione dimensioni
        if len(v1) != len(v2):
            return jsonify({'errore': 'I vettori devono avere la stessa dimensione'}), 400

        # Calcolo similarità
        similarity = cosine_similarity(v1, v2)
        return jsonify({'similarity': float(similarity)})

    except ValueError as e:
        return jsonify({'errore': 'I vettori devono contenere solo valori numerici'}), 400
    except Exception as e:
        return jsonify({'errore': str(e)}), 400
    


# Avvio del server Flask
if __name__ == "__main__":
    app.run(debug=True)