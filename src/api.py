import os
import sys

# Adiciona o diretório atual ao path para conseguir importar o app_ia
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Importações do LangChain e Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

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
    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | chat_model
        | StrOutputParser()
    )
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