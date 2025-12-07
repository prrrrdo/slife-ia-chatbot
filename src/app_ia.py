# app_ia.py

import os
import pandas as pd
from dotenv import load_dotenv

# --- IMPORTAÇÕES DO LANGCHAIN ---
# GoogleGenerativeAIEmbeddings: É a ferramenta que traduz texto (palavras) para vetores (listas de números).
# Isso é essencial para a máquina entender "significado".
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# FAISS (Facebook AI Similarity Search): É o banco de dados vetorial.
# Ele armazena os números gerados acima e permite buscas ultra-rápidas por similaridade.
from langchain_community.vectorstores import FAISS

# Document: Objeto padrão do LangChain para guardar texto + metadados.
from langchain_core.documents import Document

# Carrega variáveis do arquivo .env (onde sua senha/API Key deve estar segura)
load_dotenv()

# Verificação de segurança básica para garantir que a chave existe antes de prosseguir
if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: A chave GOOGLE_API_KEY não foi encontrada no arquivo .env")
    exit()

def carregar_dados(caminho_arquivo):
    """
    Função ETL (Extract, Transform, Load):
    Lê o CSV, transforma linhas em texto descritivo e carrega em objetos Document.
    """
    print(f"Carregando dados de: {caminho_arquivo}...")
    
    try:
        # Lê o CSV. Importante: no Brasil usamos ';' como separador e ',' para decimais.
        # Sem isso, o Python acharia que "1.500,00" são duas colunas diferentes.
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return []

    documentos = []
    
    # Itera sobre cada linha do DataFrame
    for _, row in df.iterrows():
        # --- A MÁGICA ACONTECE AQUI ---
        # Transformamos dados tabulares em uma "história" (string).
        # A LLM (Gemini) precisa ler um texto coerente para entender o imóvel.
        # Se você só passasse os números soltos, ela poderia se confundir.
        texto_descritivo = (
            f"Imóvel tipo {row['tipo']} em {row['cidade']}. "
            f"Valor do aluguel: R$ {row['valor_aluguel']}. "
            f"Possui {row['quartos']} quartos e {row['vagas_totais']} vagas. "
            f"Diferenciais: {'Mobiliado' if row['tem_mobilia'] else 'Sem mobília'}, "
            f"{'Internet inclusa' if row['tem_internet'] else 'Sem internet'}, "
            f"{'Lavanderia' if row['tem_lavanderia'] else 'Sem lavanderia'}. "
            f"Distância da universidade: {row['distancia_universidade_km']}km. "
            f"Avaliação dos estudantes: {row['nota_avaliacao']} estrelas."
        )
        
        # Metadados são dados "invisíveis" para a IA na hora de gerar texto, 
        # mas úteis para filtros (ex: filtrar só imóveis em "Campinas" antes da busca).
        metadados = {
            "id": row['imovel_id'],
            "tipo": row['tipo'],
            "cidade": row['cidade'],
            "valor": float(row['valor_aluguel']),
            "texto_original": texto_descritivo # Guardamos o texto original por segurança
        }
        
        # Cria o objeto Document final
        documentos.append(Document(page_content=texto_descritivo, metadata=metadados))
    
    print(f"{len(documentos)} imóveis processados e prontos para indexação.")
    return documentos

def criar_indice_vetorial(docs):
    """
    Esta função cria o 'cérebro' de busca.
    Ela pega os textos -> converte em vetores -> guarda no FAISS.
    """
    print("Criando índice vetorial com Google Gemini...")
    
    # Inicializa o modelo de Embeddings.
    # O 'models/text-embedding-004' é específico para criar vetores, não para gerar texto de chat.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Cria o índice FAISS na memória RAM.
    # Ele calcula a "impressão digital" matemática de cada imóvel.
    vector_store = FAISS.from_documents(docs, embeddings)
    
    print("Banco vetorial criado com sucesso!")
    return vector_store

# --- Bloco de Teste ---
if __name__ == "__main__":
    # Ajuste o caminho se necessário
    caminho_csv = "data/slife_imoveis.csv"
    
    docs = carregar_dados(caminho_csv)
    
    if docs:
        try:
            banco = criar_indice_vetorial(docs)
            
            # Simulação de busca
            pergunta = "quero uma republica barata em campinas perto da faculdade"
            print(f"\nTestando busca Gemini por: '{pergunta}'")
            
            resultados = banco.similarity_search(pergunta, k=2)
            
            for doc in resultados:
                print(f"\n--- Imóvel ID {doc.metadata['id']} ---")
                print(doc.page_content)
        except Exception as e:
            print(f"\nErro ao conectar com o Google: {e}")
            print("Verifique se sua chave no .env está correta e se a API 'Generative Language API' está ativada no Google Cloud.")