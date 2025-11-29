import os
import sys

<<<<<<< HEAD
# Garante que o Python encontre o arquivo app_ia na mesma pasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
sys.path.append(diretorio_atual)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
=======
# Adiciona o diretório atual ao path para conseguir importar o app_ia
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from dotenv import load_dotenv

# Importações do LangChain e Google Gemini
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

<<<<<<< HEAD
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

=======
# Importamos as funções do seu motor de busca
# Se der erro de importação, verifique se o arquivo app_ia.py está na mesma pasta
try:
    from app_ia import carregar_dados, criar_indice_vetorial
except ImportError:
    from src.app_ia import carregar_dados, criar_indice_vetorial

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a API
app = FastAPI(
    title="API SLife - Chatbot Universitário",
    description="API para recomendação de imóveis universitários usando RAG + Google Gemini",
    version="1.0.0"
)

# BLOCO DE SEGURANÇA (CORS)#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite qualquer origem (navegador, arquivo, etc)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (incluindo OPTIONS)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# --- Variáveis Globais (O "Cérebro" carregado na memória) ---
vector_store = None
retriever = None
chat_model = None
rag_chain = None

# --- Modelo de Dados (O que o Frontend envia) ---
class UserRequest(BaseModel):
    message: str

# --- Evento de Inicialização (Roda apenas 1 vez ao ligar o servidor) ---
@app.on_event("startup")
async def startup_event():
    global vector_store, retriever, chat_model, rag_chain
    print("Inicializando a API do Chatbot SLife...")

    # 1. Definir caminho do CSV
    # Tenta achar o arquivo tanto rodando da raiz quanto da pasta src
    caminho_csv = "data/slife_imoveis.csv"
    if not os.path.exists(caminho_csv):
        caminho_csv = "../data/slife_imoveis.csv"
    
    if not os.path.exists(caminho_csv):
        print(f"ERRO CRÍTICO: Arquivo {caminho_csv} não encontrado!")
        return

    # 2. Carregar dados e criar índice (Motor de Busca)
    print("Carregando catálogo de imóveis...")
    docs = carregar_dados(caminho_csv)
    if not docs:
        print("Falha ao carregar documentos.")
        return
    
    vector_store = criar_indice_vetorial(docs)
    
    # Configura o "Retriever" para buscar os 4 imóveis mais relevantes
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # 3. Configurar o Modelo de Chat (Gemini 1.5 Flash)
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERRO: GOOGLE_API_KEY não configurada no .env")
        return
        
    chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    # 4. Criar o Prompt (A Personalidade da SLife)
    # Baseado no perfil da empresa: jovem, universitária, focada em praticidade [cite: 78, 79]
    template = """
    Você é o assistente virtual oficial da SLife, especializado em moradia universitária.
    Seu tom deve ser jovem, prestativo e direto.
    
    Sua missão é ajudar estudantes a encontrar o imóvel ideal no nosso catálogo.
    
    INSTRUÇÕES:
    1. Use APENAS as informações dos "Imóveis Encontrados" abaixo para responder.
    2. Se os imóveis listados não forem exatamente o que o usuário pediu, explique isso educadamente e mostre a opção mais próxima.
    3. Sempre mencione o ID do imóvel, o valor e a cidade.
    4. Se a informação não estiver no contexto, diga que não encontrou nada com essas características específicas no momento.
    
    Imóveis Encontrados (Contexto):
    {context}
    
    Pergunta do Estudante:
    {question}
    
    Sua Resposta (em português do Brasil):
    """
    prompt = PromptTemplate.from_template(template)

    # 5. Montar a Chain (Fluxo de IA)
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | chat_model
        | StrOutputParser()
    )
<<<<<<< HEAD
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
=======
    print("API SLife carregada e pronta para receber conexões!")

# --- Rotas da API ---

@app.get("/")
def read_root():
    """Rota de teste para ver se a API está online"""
    return {"status": "online", "service": "SLife AI Chatbot"}

@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    """Rota principal que recebe a pergunta e devolve a resposta da IA"""
    global rag_chain
    
    if not rag_chain:
        raise HTTPException(status_code=500, detail="Sistema de IA não foi inicializado corretamente.")
    
    try:
        print(f"Pergunta recebida: {request.message}")
        # Chama a IA para processar
        resposta = rag_chain.invoke(request.message)
        return {"response": resposta}
    except Exception as e:
        print(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
>>>>>>> 9dc71862df5efd464000d7e1d7da3da72b039a59
