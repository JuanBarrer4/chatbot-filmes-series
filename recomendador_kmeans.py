import math
import random
from typing import List, Dict, Any

class AgrupamentoKMeans:
    def __init__(self, k: int = 5, max_iter: int = 100):
        self.k = k
        self.max_iter = max_iter
        self.centroides = []
        self.grupos = {}
        # Categorias definidas para o sistema, conforme a documentação do Integrante 5
        self.categorias_totais = [
            "Ação", "Comédia", "Drama", "Terror", "Ficção Científica", 
            "Romance", "Suspense", "Animação", "Aventura", "Documentário",
            "Fantasia", "Mistério", "Crime", "Guerra", "Biografia", "História",
            "Policial", "Família", "Música", "Musical", "Faroeste", "Crime"
        ]

    def extrair_caracteristicas(self, item: Dict[str, Any]) -> List[float]:
        """
        Converte um filme/série num vetor numérico para calcular a dissimilaridade.
        """
        # Funciona para filmes e séries
        ano = item.get('ano', item.get('ano_de_lancamento', 2000))
        ano_norm = (ano - 1900) / 125.0
        
        nota = item.get('nota', 5.0)
        nota_norm = nota / 10.0
        
        generos = item.get("genero", "")

        # O JSON guarda o gênero como string
        if isinstance(generos, str):
              generos = [g.strip() for g in generos.split(",")]
 
        vetor_generos = [
              1.0 if cat in generos else 0.0
              for cat in self.categorias_totais
]
        
        return [ano_norm, nota_norm] + vetor_generos

    def distancia_euclidiana(self, p1: List[float], p2: List[float]) -> float:
        """Calcula a distância euclidiana entre dois pontos no espaço."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def treinar(self, dados: List[Dict[str, Any]]):
        """
        Aplica o algoritmo K-Means para agrupar os itens.
        """
        if not dados or len(dados) < self.k:
            return

        # 1. Escolhe arbitrariamente K objetos do banco de dados
        amostras_iniciais = random.sample(dados, self.k)
        self.centroides = [self.extrair_caracteristicas(item) for item in amostras_iniciais]
        
        for _ in range(self.max_iter):
            novos_grupos = {i: [] for i in range(self.k)}
            
            # 2. Atribui cada objeto ao centroide mais próximo
            for item in dados:
                vetor = self.extrair_caracteristicas(item)
                distancias = [self.distancia_euclidiana(vetor, c) for c in self.centroides]
                indice_vencedor = distancias.index(min(distancias))
                novos_grupos[indice_vencedor].append(item)
                
            centroides_antigos = self.centroides.copy()
            
            # 3. Calcula os novos centros de gravidade (média do grupo)
            for i in range(self.k):
                itens_grupo = novos_grupos[i]
                if not itens_grupo:
                    continue
                    
                vetores = [self.extrair_caracteristicas(item) for item in itens_grupo]
                novo_centroide = [sum(dim) / len(vetores) for dim in zip(*vetores)]
                self.centroides[i] = novo_centroide
                
            self.grupos = novos_grupos
            
            # 4. Condição de paragem
            mudanca = sum(self.distancia_euclidiana(c1, c2) for c1, c2 in zip(centroides_antigos, self.centroides))
            if mudanca < 0.0001:
                break

    def recomendar_semelhantes(self, titulo_alvo: str, todos_dados: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """Retorna obras do mesmo grupo, ordenadas pela proximidade exata."""
        item_alvo = next((item for item in todos_dados if item.get('titulo', '').lower() == titulo_alvo.lower()), None)
        
        if not item_alvo:
            return []
            
        vetor_alvo = self.extrair_caracteristicas(item_alvo)
        
        # Encontra a qual grupo a obra pertence
        distancias_centroides = [self.distancia_euclidiana(vetor_alvo, c) for c in self.centroides]
        indice_grupo = distancias_centroides.index(min(distancias_centroides))
        
        candidatos = []
        for item in self.grupos.get(indice_grupo, []):
            if item.get('titulo') != item_alvo.get('titulo'):
                dist = self.distancia_euclidiana(vetor_alvo, self.extrair_caracteristicas(item))
                candidatos.append((dist, item))
                
        # Ordena a lista pelas obras mais curtas em termos de distância Euclidiana
        candidatos.sort(key=lambda x: x[0])
        return [item for dist, item in candidatos[:top_n]]


class RecomendadorCineBot:
    def __init__(self, k_filmes=8, k_series=5):
        # Inicializa o K-Means para filmes e para séries
        self.modelo_filmes = AgrupamentoKMeans(k=k_filmes)
        self.modelo_series = AgrupamentoKMeans(k=k_series)
        self.filmes = []
        self.series = []
        
    def carregar_dados(self, filmes: List[Dict[str, Any]], series: List[Dict[str, Any]]):
        """Carrega as bases de dados e treina o agrupamento automaticamente."""
        self.filmes = filmes
        self.series = series
        self.modelo_filmes.treinar(self.filmes)
        self.modelo_series.treinar(self.series)
        
    def obter_recomendacoes_mensagem(self, prompt_utilizador: str) -> str:
        """
        Recebe o prompt do utilizador, identifica o título mencionado e 
        devolve as recomendações com base no grupo associado.
        """
        mensagem_lower = prompt_utilizador.lower()
        
        item_encontrado = None
        is_filme = True
        
        # Procura correspondência na base de filmes
        for filme in self.filmes:
            if filme.get("titulo", "").lower() in mensagem_lower:
                item_encontrado = filme
                break
                
        # Se não encontrar, procura na base de séries
        if not item_encontrado:
            for serie in self.series:
                if serie.get("titulo", "").lower() in mensagem_lower:
                    item_encontrado = serie
                    is_filme = False
                    break
                    
        # Constrói a recomendação caso um título compatível tenha sido encontrado no prompt
        if item_encontrado:
            if is_filme:
                recomendacoes = self.modelo_filmes.recomendar_semelhantes(item_encontrado['titulo'], self.filmes)
            else:
                recomendacoes = self.modelo_series.recomendar_semelhantes(item_encontrado['titulo'], self.series)
                
            if recomendacoes:
                resposta = f"Como gostou de '{item_encontrado['titulo']}', eis algumas obras do mesmo grupo que recomendo:\n"
            
                for rec in recomendacoes:

                    ano = rec.get("ano", rec.get("ano_de_lancamento", "N/A"))

                    genero = rec.get("genero", "N/A")

                    resposta += (
                        f"- {rec['titulo']} ({ano}) | "
                        f"Nota: {rec.get('nota', 'N/A')} | "
                        f"Gênero: {genero}\n"
    )
                return resposta
            else:
                return f"Ainda não tenho obras suficientemente semelhantes a '{item_encontrado['titulo']}' na minha base de dados atual."
                
        return "Para criar uma associação, por favor mencione no seu texto o título exato de um filme ou série de que tenha gostado."
