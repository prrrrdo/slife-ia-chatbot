import os
import sys

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from dotenv import load_dotenv

# --- NOVAS IMPORTAÇÕES PARA MEMÓRIA ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Importa funções do motor de busca
try:
    from app_ia import carregar_dados, criar_indice_vetorial
except ImportError:
    from src.app_ia import carregar_dados, criar_indice_vetorial

load_dotenv()

app = FastAPI(title="API SLife - Chatbot com Memória", version="1.2.0")

# --- BLOCO DE SEGURANÇA (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Gestão de Sessão (Memória RAM) ---
# Aqui guardamos o histórico de cada usuário enquanto o servidor roda
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# --- Variáveis Globais ---
rag_chain_with_history = None

class UserRequest(BaseModel):
    message: str
    session_id: str = "usuario_padrao" # Identificador da conversa

@app.on_event("startup")
async def startup_event():
    global rag_chain_with_history
    print("🚀 Inicializando API com Memória...")

    caminho_csv = "data/slife_imoveis.csv"
    if not os.path.exists(caminho_csv):
        caminho_csv = "../data/slife_imoveis.csv"
    
    if not os.path.exists(caminho_csv):
        print("❌ ERRO: CSV não encontrado.")
        return

    # 1. Carregar Dados
    print("📂 Carregando dados...")
    docs = carregar_dados(caminho_csv)
    if not docs:
        print("❌ Falha ao carregar documentos.")
        return
        
    vector_store = criar_indice_vetorial(docs)
    
    # 2. Retriever com MMR (Diversidade)
    # k=20 com MMR é suficiente se a busca for bem feita
    retriever = vector_store.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": 20, "fetch_k": 100, "lambda_mult": 0.6}
    )

    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERRO: Sem API KEY.")
        return
        
    # Modelo Gemini (Usando a versão flash estável)
    chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    # --- CÉREBRO DA MEMÓRIA ---
    
    # PASSO A: Reformulador de Perguntas
    # Se o usuário diz "E com lavanderia?", a IA transforma em "Imóveis em [cidade anterior] com lavanderia"
    contextualize_q_system_prompt = """
    Dado um histórico de chat e a última pergunta do usuário 
    (que pode fazer referência ao contexto passado), formule uma pergunta autônoma 
    que possa ser entendida sem o histórico. NÃO responda à pergunta, 
    apenas a reformule se necessário ou retorne-a como está.
    """
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = (
        contextualize_q_prompt
        | chat_model
        | StrOutputParser()
        | retriever
    )

    # PASSO B: Resposta Final (QA)
    qa_system_prompt = """
    Você é o assistente da SLife (Moradia Universitária). Jovem, útil e direto.
    
    DIRETRIZES:
    1. Use os contextos abaixo para responder.
    2. Se o usuário pediu perfil (silêncio vs festa), filtre mentalmente.
    3. Cite ID, Cidade e Valor das opções.
    
    CONTEXTO:
    {context}
    
    Responda em português do Brasil.
    """
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        ("placeholder", "{chat_history}"), # Histórico entra aqui
        ("human", "{input}"),
    ])

    question_answer_chain = (
        RunnablePassthrough.assign(context=history_aware_retriever)
        | qa_prompt
        | chat_model
        | StrOutputParser()
    )

    # PASSO C: Chain Final com Gestão de Histórico
    rag_chain_with_history = RunnableWithMessageHistory(
        question_answer_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    print("✅ API com Memória Pronta!")

@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    if not rag_chain_with_history:
        raise HTTPException(status_code=500, detail="IA off.")
    
    try:
        print(f"📩 Msg: {request.message} | Session: {request.session_id}")
        
        # Invocamos passando o session_id para recuperar o histórico correto
        resposta = rag_chain_with_history.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}}
        )
        return {"response": resposta}
    except Exception as e:
        print(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))