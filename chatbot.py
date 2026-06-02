import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ─── Cargar las bases de datos ───
def carregar_base():
    with open("filmes.json", "r", encoding="utf-8") as f:
        filmes = json.load(f)
    with open("series.json", "r", encoding="utf-8") as f:
        series = json.load(f)
    return filmes, series

# ─── Montar el contexto con los datos ───
def montar_contexto(filmes, series):
    contexto = """Você é um chatbot especialista em filmes e séries chamado CineBot.
Responda sempre em português, de forma organizada e educada.
Use as informações da base de dados abaixo para responder.
Quando recomendar filmes ou séries, mostre: título, ano, gênero, nota e classificação.
Quando fizer resumos, seja detalhado mas claro.

=== BASE DE FILMES ===\n"""
    
    for f in filmes:
        contexto += f"- {f['titulo']} ({f['ano']}) | Diretor: {f['diretor']} | Elenco: {', '.join(f['elenco'])} | Gênero: {f['genero']} | Nota: {f['nota']} | Classificação: {f['classificacao']} | Duração: {f['duracao']} | Resumo: {f['resumo']} | Semelhantes: {', '.join(f['semelhantes'])}\n"
    
    contexto += "\n=== BASE DE SÉRIES ===\n"
    for s in series:
        contexto += f"- {s['titulo']} ({s['ano']}) | Criador: {s['criador']} | Temporadas: {s['temporadas']} | Gênero: {s['genero']} | Nota: {s['nota']} | Classificação: {s['classificacao']} | Resumo: {s['resumo']} | Semelhantes: {', '.join(s['semelhantes'])}\n"
    
    return contexto

# ─── Enviar mensaje a la API ───
def enviar_mensagem(historico):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openrouter/auto",
            "messages": historico
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]

# ─── Loop principal del chatbot ───
def iniciar_chat():
    filmes, series = carregar_base()
    contexto = montar_contexto(filmes, series)
    
    # Historial de conversación (memoria)
    historico = [
        {"role": "system", "content": contexto}
    ]
    
    print("=" * 50)
    print("🎬 Bem-vindo ao CineBot!")
    print("Pergunte sobre filmes e séries.")
    print("Digite 'sair' para encerrar.")
    print("=" * 50)
    print()
    
    while True:
        pergunta = input("Você: ").strip()
        
        if pergunta.lower() == "sair":
            print("Até mais! 🎬")
            break
        if not pergunta:
            continue
        
        # Agregar pregunta al historial
        historico.append({"role": "user", "content": pergunta})
        
        print("CineBot: pensando...")
        
        # Obtener respuesta
        resposta = enviar_mensagem(historico)
        
        # Agregar respuesta al historial (memoria)
        historico.append({"role": "assistant", "content": resposta})
        
        print(f"\nCineBot: {resposta}\n")

if __name__ == "__main__":
    iniciar_chat()