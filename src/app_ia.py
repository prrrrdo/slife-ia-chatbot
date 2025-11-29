import os
import pandas as pd
<<<<<<< HEAD
from typing import List
from dotenv import load_dotenv
=======
from dotenv import load_dotenv
# Importações específicas do Google Gemini
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

<<<<<<< HEAD
load_dotenv()

def carregar_dados(caminho_arquivo: str) -> List[Document]:
    """
    Lê o CSV e cria artificialmente a informação de Pet Friendly.
=======
# Carrega as variáveis de ambiente
load_dotenv()

# Verifica se a chave da API existe
if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: A chave GOOGLE_API_KEY não foi encontrada no arquivo .env")
    exit()

def carregar_dados(caminho_arquivo):
    """
    Lê o CSV da SLife e prepara o texto para a IA.
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
    """
    print(f"Carregando dados de: {caminho_arquivo}...")
    
    try:
<<<<<<< HEAD
        try:
            df = pd.read_csv(caminho_arquivo, sep=';', decimal=',', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(caminho_arquivo, sep=';', decimal=',', encoding='latin-1')
            
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return []
    except Exception as e:
        print(f"Erro genérico ao ler arquivo: {e}")
        return []

    mapa_estados = {
        "SC": "Santa Catarina", "SP": "São Paulo", "RJ": "Rio de Janeiro",
        "MG": "Minas Gerais", "RS": "Rio Grande do Sul", "PR": "Paraná",
        "DF": "Distrito Federal", "BA": "Bahia"
    }
=======
        # O CSV da SLife usa ponto e vírgula (;) como separador
        df = pd.read_csv(caminho_arquivo, sep=';', decimal=',')
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return []
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59

    documentos = []
    
    for _, row in df.iterrows():
<<<<<<< HEAD
        # --- TRATAMENTO DE LOCALIZAÇÃO ---
        cidade_original = str(row['cidade'])
        estado_nome = ""
        cidade_nome = cidade_original
        sigla = ""
        
        if "-" in cidade_original:
            partes = cidade_original.split("-")
            cidade_nome = partes[0].strip()
            if len(partes) > 1:
                sigla = partes[1].strip()
                estado_nome = mapa_estados.get(sigla, sigla)
                localizacao_completa = f"{cidade_nome}, {estado_nome} ({sigla})"
            else:
                localizacao_completa = cidade_original
        else:
            localizacao_completa = cidade_original

        # --- A MÁGICA DO PET 🐶 (REGRA DE NEGÓCIO) ---
        # Regra: Se for Kitnet ou Apartamento -> Aceita Pet.
        # Se for República ou Casa Compartilhada -> Depende do ID (par aceita, ímpar não).
        tipo = row['tipo']
        
        if "Kitnet" in tipo or "Apartamento" in tipo:
            info_pet = "ACEITA ANIMAIS DE ESTIMAÇÃO (Pet Friendly 🐾)"
        else:
            # Para repúblicas, sorteamos 50% de chance baseado no ID ser par
            if row['imovel_id'] % 2 == 0:
                info_pet = "Aceita animais de pequeno porte 🐶"
            else:
                info_pet = "Não aceita animais (Regra do condomínio) 🚫"

        # Outras infos
        mobilia = 'Totalmente mobiliado' if row.get('tem_mobilia') else 'Sem mobília'
        internet = 'com internet inclusa' if row.get('tem_internet') else 'sem internet'
        
        # O texto que a IA vai ler agora inclui o PET
        texto_descritivo = (
            f"Imóvel tipo {tipo} localizado em: {localizacao_completa}. "
            f"Valor: R$ {row['valor_aluguel']}. "
            f"Política Pet: {info_pet}. " 
            f"Detalhes: {row['quartos']} quartos. "
            f"Estrutura: {mobilia}, {internet}."
        )

        metadados = {
            "id": row['imovel_id'],
            "cidade": cidade_nome,
            "estado": estado_nome,
            "valor": float(row['valor_aluguel']),
            "pet": info_pet # Guardamos no metadado também
=======
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
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
        }
        
        documentos.append(Document(page_content=texto_descritivo, metadata=metadados))
    
<<<<<<< HEAD
    print(f"{len(documentos)} imóveis processados com regras de Pet.")
    return documentos

def criar_indice_vetorial(docs: List[Document]):
    print("Gerando Embeddings com Gemini...")
    if not docs:
        return None
    
    # Usando modelo compatível
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store
=======
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
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
