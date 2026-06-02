from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import json
import requests

load_dotenv()

app = Flask(__name__)

def load_filmes_series():
    """Carga películas y series desde JSON"""
    try:
        with open('filmes.json', 'r', encoding='utf-8') as f:
            filmes = json.load(f)
        with open('series.json', 'r', encoding='utf-8') as f:
            series = json.load(f)
        return filmes, series
    except FileNotFoundError:
        return [], []

def get_chatbot_response(user_message):
    """Obtiene respuesta del chatbot via OpenRouter"""
    filmes, series = load_filmes_series()
    
    context = f"""Eres un asistente que ayuda a usuarios a buscar películas y series.
    
Tienes acceso a esta base de datos:

PELÍCULAS:
{json.dumps(filmes, ensure_ascii=False, indent=2)}

SERIES:
{json.dumps(series, ensure_ascii=False, indent=2)}

El usuario pregunta: {user_message}

Responde en un tono amigable y ayuda al usuario a encontrar películas o series basándote en la base de datos."""
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ]
            }
        )
        
        data = response.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: {data.get('error', {}).get('message', 'Error desconocido')}"
    except Exception as e:
        return f"Error al conectar con la API: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para enviar mensajes al chatbot"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Mensaje vacío'}), 400
    
    response = get_chatbot_response(user_message)
    return jsonify({'response': response})

@app.route('/api/filmes', methods=['GET'])
def get_filmes():
    """Endpoint para obtener todas las películas"""
    filmes, _ = load_filmes_series()
    return jsonify(filmes)

@app.route('/api/series', methods=['GET'])
def get_series():
    """Endpoint para obtener todas las series"""
    _, series = load_filmes_series()
    return jsonify(series)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
