import os
import pandas as pd
from typing import List
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()

def carregar_dados(caminho_arquivo: str) -> List[Document]:
    """
    Lê o CSV e cria artificialmente a informação de Pet Friendly.
    """
    print(f"Carregando dados de: {caminho_arquivo}...")
    
    try:
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

    documentos = []
    
    for _, row in df.iterrows():
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
        }
        
        documentos.append(Document(page_content=texto_descritivo, metadata=metadados))
    
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