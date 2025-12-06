# Arquivo: versao_2_estruturada/app/config.py
import os
from dotenv import load_dotenv

class Settings:
    print("--- 🕵️ INICIANDO DIAGNÓSTICO DE CONFIGURAÇÃO ---")
    
    # 1. Onde estou agora?
    CURRENT_FILE = os.path.abspath(__file__)
    print(f"📍 Arquivo config.py: {CURRENT_FILE}")
    
    # 2. Calculando a raiz (subindo 3 níveis: app -> versao_2 -> raiz)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_FILE)))
    print(f"📂 Raiz do Projeto calculada: {BASE_DIR}")
    
    # 3. Caminho esperado do .env
    ENV_PATH = os.path.join(BASE_DIR, ".env")
    print(f"🔎 Procurando .env em: {ENV_PATH}")
    
    # 4. Verificação física
    if os.path.exists(ENV_PATH):
        print("✅ Arquivo .env ENCONTRADO no disco!")
        load_dotenv(dotenv_path=ENV_PATH)
    else:
        print("❌ Arquivo .env NÃO ENCONTRADO neste local.")
        # Tenta procurar na pasta atual por desencargo
        print("   Tentando procurar na pasta atual...")
        load_dotenv() 

    # 5. Tentativa de pegar a chave
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if GOOGLE_API_KEY:
        # Mostra apenas os primeiros caracteres por segurança
        print(f"🔑 Chave carregada: {GOOGLE_API_KEY[:5]}...OK")
    else:
        print("❌ A variável GOOGLE_API_KEY está vazia ou nula.")
    
    # Caminho do CSV
    CSV_PATH = os.path.join(BASE_DIR, "data", "slife_imoveis.csv")
    print(f"📊 Caminho do CSV: {CSV_PATH}")
    
    MODEL_NAME = "gemini-2.5-flash"
    print("--- FIM DO DIAGNÓSTICO ---\n")

settings = Settings()