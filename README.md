# Chatbot de Filmes e Séries

Chatbot inteligente para consultar informações sobre filmes e séries usando IA.

## Como executar

### 1. Clonar o repositório
```bash
git clone https://github.com/JuanBarrer4/chatbot-filmes-series.git
cd chatbot-filmes-series
```

### 2. Criar o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar as bibliotecas
```bash
pip install flask python-dotenv requests
```

### 4. Criar o arquivo .env
Crie um arquivo chamado `.env` na pasta com o seguinte conteúdo:
OPENROUTER_API_KEY=sua_chave_aqui
Crie sua chave grátis em: https://openrouter.ai

### 5. Executar
```bash
python app.py
```

### 6. Abrir no navegador
http://localhost:5000

## Tecnologias utilizadas
- Python
- Flask
- OpenRouter API
- HTML/CSS/JavaScript
Depois executa:
bashgit add README.md
git commit -m "adiciona README"
git push
