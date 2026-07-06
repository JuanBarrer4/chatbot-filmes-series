from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import json
import requests

# IMPORTANDO o RECOMENDADOR SEPARADO:
from recomendador_kmeans import RecomendadorCineBot

load_dotenv()

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.secret_key = 'chave_secreta_para_o_cinebot'

def load_filmes_series():
    """Carrega filmes e séries em JSON"""
    try:
        with open('filmes.json', 'r', encoding='utf-8') as f:
            filmes = json.load(f)
        with open('series.json', 'r', encoding='utf-8') as f:
            series = json.load(f)
        return filmes, series
    except FileNotFoundError:
        return [], []

def montar_contexto(filmes, series):
    contexto = """Você é um assistente virtual especialista e educado chamado CineBot.
Você fala exclusivamente em português.

[REGRA CRÍTICA ABSOLUTA]
1. Você APENAS pode citar, sugerir, recomendar ou mencionar filmes e séries que estejam explicitamente listados na base de dados abaixo.
2. É TOTALMENTE PROIBIDO usar o seu conhecimento externo para sugerir obras de fora, mesmo que você avise que elas não estão no catálogo. Se não estiver na lista abaixo, para você a obra NÃO EXISTE.
3. Se o usuário pedir sugestões de um gênero (Ex: aventura, ação), olhe o catálogo local, veja quais se encaixam e recomende APENAS os do catálogo local usando a formatação obrigatória.

Se o usuário mencionar ou perguntar por uma obra inexistente no catálogo local:
- Responda educadamente que não possui essa obra no catálogo atual.
- NÃO invente dados e NÃO comente sobre a obra de fora.
- Sugira imediatamente opções parecidas contidas APENAS na base local.

[COMO FORMATAR SUAS RESPOSTAS]
Sempre que você citar, listar ou recomendar qualquer filme ou série do catálogo local, use obrigatoriamente esta estrutura exata para cada um:

- **Título**: [Nome] ([Ano])
- 🎬 **Gênero**: [Gênero] | 🔞 **Classificação**: [Classificação]
- ⭐ **Nota**: [Nota]/10
- 📝 **Resumo**: [Breve resumo]

=== BASE DE FILMES ===\n"""

    for f in filmes:
        ano_f = f.get('ano', 'N/A')
        diretor_f = f.get('diretor', 'Desconhecido')
        elenco_f = ', '.join(f.get('elenco', []))
        genero_f = f.get('genero', 'N/A')
        nota_f = f.get('nota', 'N/A')
        classificacao_f = f.get('classificacao', 'N/A')
        duracao_f = f.get('duracao', 'N/A')
        resumo_f = f.get('resumo', 'Sem resumo disponível.')
        semelhantes_f = ', '.join(f.get('semelhantes', []))

        contexto += f"- {f.get('titulo', 'Sem título')} ({ano_f}) | Diretor: {diretor_f} | Elenco: {elenco_f} | Gênero: {genero_f} | Nota: {nota_f} | Classificação: {classificacao_f} | Duração: {duracao_f} | Resumo: {resumo_f} | Semelhantes: {semelhantes_f}\n"
        
    contexto += "\n=== BASE DE SÉRIES ===\n"
    for s in series:
        ano = s.get('ano_de_lancamento', 'N/A')
        criador = s.get('criador', 'Desconhecido')
        temporadas = s.get('numero_de_temporadas', 'N/A')
        genero = s.get('genero', 'N/A')
        classificacao = s.get('classificacao_indicativa', 'N/A')
        nota = s.get('nota', 'N/A')
        resumo = s.get('resumo', 'Sem resumo disponível.')
        semelhantes = ', '.join(s.get('series_semelhantes', []))
        
        contexto += f"- {s.get('titulo', 'Sem título')} ({ano}) | Criador: {criador} | Temporadas: {temporadas} | Gênero: {genero} | Classificação: {classificacao} | Nota: {nota} | Resumo: {resumo} | Semelhantes: {semelhantes}\n"
        
    return contexto

def get_chatbot_response(user_message):
    filmes, series = load_filmes_series()
    contexto = montar_contexto(filmes, series)
    
    # CHAMANDO O MÉTODO DO RECOMENDADOR
    recomendador = RecomendadorCineBot()
    recomendador.carregar_dados(filmes, series)
    resultado_kmeans = recomendador.obter_recomendacoes_mensagem(user_message)
    
    # Se o recomendador encontrou algo, injeta no prompt do Gemini formatar
    if resultado_kmeans:
        contexto += f"\n\n[DADOS COMPLEMENTARES DO SISTEMA K-MEANS]:\nO algoritmo matemático analisou os arquivos JSON e obteve este resultado:\n{resultado_kmeans}\nPor favor, exiba e formate essas recomendações de acordo com o padrão exigido do CineBot."

    if 'historico' not in session or not isinstance(session['historico'], list):
        session['historico'] = []

    historico_atual = list(session['historico'])
    
    system_message = {"role": "system", "content": contexto}
    if len(historico_atual) == 0:
        historico_atual.append(system_message)
    else:
        historico_atual[0] = system_message
        
    historico_atual.append({"role": "user", "content": user_message})  

    if len(historico_atual) > 5:
        historico_atual = [historico_atual[0]] + historico_atual[-4:]

    try:
        # Puxa a chave do arquivo .env de forma limpa
        api_key = os.getenv("GEMINI_API_KEY")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": historico_atual,
                "temperature": 0.0,
                "max_tokens": 2000
            }
        )
        data = response.json()
        if "choices" in data:
            resposta_ia = data["choices"][0]["message"]["content"]
            historico_atual.append({"role": "assistant", "content": resposta_ia})
            session['historico'] = historico_atual
            session.modified = True
            return resposta_ia
        else:
            return f"Error: {data.get('error', {}).get('message', 'Erro desconhecido')}"
    except Exception as e:
        return f"Erro ao se conectar à API: {str(e)}"

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    response = get_chatbot_response(user_message)
    return jsonify({'response': response})

@app.route('/api/filmes', methods=['GET'])
def get_filmes():
    filmes, _ = load_filmes_series()
    return jsonify(filmes)

@app.route('/api/series', methods=['GET'])
def get_series():
    _, series = load_filmes_series()
    return jsonify(series)

if __name__ == '__main__':
    app.run(debug=True, port=5000)