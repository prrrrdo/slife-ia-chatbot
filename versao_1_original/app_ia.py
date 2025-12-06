import os
import pandas as pd
from dotenv import load_dotenv
# Importações específicas do Google Gemini
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Carrega as variáveis de ambiente
load_dotenv()

# Verifica se a chave da API existe
if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: A chave GOOGLE_API_KEY não foi encontrada no arquivo .env")
    exit()

def carregar_dados(caminho_arquivo):
    """
    Lê o CSV da SLife e prepara o texto para a IA.
    """
    print(f"Carregando dados de: {caminho_arquivo}...")
    
    try:
        # O CSV da SLife usa ponto e vírgula (;) como separador
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return []

    documentos = []
    
    for _, row in df.iterrows():
        # Criamos uma frase descritiva para cada imóvel
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
        
        # Metadados para ajudar na recuperação
        metadados = {
            "id": row['imovel_id'],
            "tipo": row['tipo'],
            "cidade": row['cidade'],
            "valor": float(row['valor_aluguel']),
            "texto_original": texto_descritivo
        }
        
        documentos.append(Document(page_content=texto_descritivo, metadata=metadados))
    
    print(f"{len(documentos)} imóveis processados e prontos para indexação.")
    return documentos

def criar_indice_vetorial(docs):
    """
    Cria o 'cérebro' da busca usando Google Gemini Embeddings.
    """
    print("Criando índice vetorial com Google Gemini...")
    
    # Modelo de Embeddings do Google (gratuito no tier free)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Cria o banco FAISS
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