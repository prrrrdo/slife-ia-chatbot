import os
import sys

# Garante que o Python encontre o arquivo app_ia na mesma pasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
sys.path.append(diretorio_atual)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Importação segura
try:
    from app_ia import carregar_dados, criar_indice_vetorial
except ImportError as e:
    print(f"ERRO CRÍTICO: Não consegui importar o app_ia.py. Detalhe: {e}")
    exit()

# Carrega a senha do .env (procura na mesma pasta do script)
caminho_env = os.path.join(diretorio_atual, ".env")
load_dotenv(caminho_env)

if not os.getenv("GOOGLE_API_KEY"):
    print("ERRO: A chave GOOGLE_API_KEY não foi configurada no arquivo .env")

app = FastAPI(title="API SLife", description="Chatbot Universitário Inteligente")

# --- CONFIGURAÇÃO DE SEGURANÇA (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_chain = None

@app.on_event("startup")
async def startup_event():
    global rag_chain
    print("--- INICIANDO SISTEMA SLIFE ---")
    
    # --- A MÁGICA DO CAMINHO (CORREÇÃO DO ERRO) ---
    # Isso força o Python a pegar o CSV que está do lado deste arquivo api.py
    caminho_csv = os.path.join(diretorio_atual, "slife_imoveis.csv")
    
    print(f"Procurando arquivo em: {caminho_csv}")

    if not os.path.exists(caminho_csv):
        print(f"❌ ERRO FATAL: O arquivo não está aqui! Verifique se o nome é 'slife_imoveis.csv'.")
        return

    # Processar Dados
    docs = carregar_dados(caminho_csv)
    if not docs:
        print("ALERTA: O arquivo existe mas nenhum imóvel foi carregado (está vazio ou com erro).")
        return

    # Criar o Cérebro
    vector_store = criar_indice_vetorial(docs)
    
    # Configurar Gemini
    chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})

    # Prompt
    template = """
    Você é o consultor virtual da SLife.
    
    INSTRUÇÕES:
    1. Use APENAS os imóveis do contexto abaixo.
    2. Se pedirem "Santa Catarina" ou "Florianópolis", busque por "SC".
    3. Responda de forma curta e vendedora.
    4. Cite valor e bairro.
    
    Contexto:
    {context}
    
    Pergunta:
    {question}
    
    Resposta:
    """
    
    prompt = PromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | chat_model
        | StrOutputParser()
    )
    print("--- ✅ SISTEMA ONLINE E CARREGADO ---")

class UserRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    global rag_chain
    if not rag_chain:
        raise HTTPException(status_code=500, detail="Erro: O sistema iniciou mas não carregou os dados.")
    try:
        resposta = rag_chain.invoke(request.message)
        return {"response": resposta}
    except Exception as e:
        return {"response": f"Erro interno: {str(e)}"}
