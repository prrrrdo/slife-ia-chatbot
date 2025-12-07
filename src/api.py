# api.py

import os # importa ferramentas do SO para ler pastas, caminhos, variaveis de ambiente , etc.
import sys # Importa ferramentas do interpretador python

# Garante que o Python encontre os módulos no diretório atual (evita erros de importação)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException # #classe principal, httoexception para retornar esseos de chamada da api
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from dotenv import load_dotenv

# --- LANGCHAIN ---
from langchain_google_genai import ChatGoogleGenerativeAI # O modelo de chat (Gemini Flash)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # Para criar templates de conversa
from langchain_core.runnables import RunnablePassthrough # Conecta etapas do pipeline
from langchain_core.output_parsers import StrOutputParser # Limpa a saída para ser só texto (string)
from langchain_core.chat_history import InMemoryChatMessageHistory # Memória RAM
from langchain_core.runnables.history import RunnableWithMessageHistory # Gerenciador de histórico

# Importa as funções que explicamos no arquivo anterior
try:
    from app_ia import carregar_dados, criar_indice_vetorial
except ImportError:
    from src.app_ia import carregar_dados, criar_indice_vetorial

load_dotenv()

# Inicializa o servidor web
app = FastAPI(title="API SLife - Chatbot com Memória", version="1.2.0")

# --- CORS (Cross-Origin Resource Sharing) ---
# Isso é vital. Permite que um site (ex: localhost:3000 ou seu frontend) 
# faça requisições para este backend sem ser bloqueado pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, colocar apenas o domínio do site aqui.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GESTÃO DE MEMÓRIA ---
# Um dicionário simples para guardar as conversas.
# Chave: session_id (ex: "usuario_123"), Valor: Lista de mensagens.
# OBS: Se reiniciar o servidor, perde-se tudo (pois é memória RAM).
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Recupera ou cria o histórico de um usuário específico."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Variável global para guardar a "cadeia" de IA pronta para uso
rag_chain_with_history = None

# Modelo de dados que define o que o usuário DEVE enviar no JSON (validação automática)
class UserRequest(BaseModel):
    message: str
    session_id: str = "usuario_padrao"

# --- INICIALIZAÇÃO (STARTUP) ---
# Executa apenas UMA VEZ quando o servidor liga.
@app.on_event("startup")
async def startup_event():
    global rag_chain_with_history
    print("🚀 Inicializando API com Memória...")

    # Tenta localizar o CSV (lógica para funcionar localmente ou em pastas diferentes)
    caminho_csv = "data/slife_imoveis.csv"
    if not os.path.exists(caminho_csv):
        caminho_csv = "../data/slife_imoveis.csv"
    
    # 1. Pipeline de Dados (ETL + Vetorização)
    # Chama as funções do app_ia.py para carregar e indexar os imóveis na memória.
    docs = carregar_dados(caminho_csv)
    vector_store = criar_indice_vetorial(docs)
    
    # 2. Configura o Retriever (O "Buscador")
    # search_type="mmr" (Maximal Marginal Relevance): 
    # Em vez de pegar os 20 imóveis mais parecidos (que podem ser quase idênticos),
    # ele pega alguns parecidos e tenta variar um pouco entre eles para dar diversidade.
    retriever = vector_store.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": 20, "fetch_k": 100, "lambda_mult": 0.6}
    )

    # Configura o Gemini (modelo Flash é mais rápido e barato para chat)
    chat_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    # --- RAG CHAIN: O CÉREBRO COMPLEXO ---
    
    # PASSO A: Contextualização (Reformulador de Perguntas)
    # Problema: Se o usuário diz "E qual o preço?", a busca vetorial falharia (pois não sabe o sujeito).
    # Solução: A IA reescreve a pergunta baseada no histórico: "Qual o preço [do imóvel X que falamos antes]?"
    contextualize_q_system_prompt = """
    Dado um histórico de chat e a última pergunta do usuário, 
    formule uma pergunta autônoma que possa ser entendida sem o histórico.
    """
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        ("placeholder", "{chat_history}"), # Aqui entra o histórico
        ("human", "{input}"), # Aqui entra a pergunta atual ("E o preço?")
    ])
    
    # Cria um mini-pipeline só para reformular a pergunta
    history_aware_retriever = (
        contextualize_q_prompt
        | chat_model
        | StrOutputParser()
        | retriever # Usa a pergunta reformulada para buscar no banco vetorial
    )

    # PASSO B: Resposta Final (QA - Question Answering)
    # Agora que temos os documentos (contexto), pedimos para a IA responder.
    qa_system_prompt = """
    Você é o assistente da SLife (Moradia Universitária). Jovem, útil e direto.
    Use os contextos abaixo para responder. Cite ID, Cidade e Valor.
    CONTEXTO: {context}
    """
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    # Monta a cadeia principal:
    # 1. Pega a pergunta -> Reformula -> Busca documentos (history_aware_retriever)
    # 2. Joga os documentos + pergunta no Prompt (qa_prompt)
    # 3. Manda para o Gemini (chat_model)
    question_answer_chain = (
        RunnablePassthrough.assign(context=history_aware_retriever)
        | qa_prompt
        | chat_model
        | StrOutputParser()
    )

    # PASSO C: O Gerente de Sessão
    # Adiciona a capacidade automática de ler/gravar o histórico na variável 'store'
    rag_chain_with_history = RunnableWithMessageHistory(
        question_answer_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    print("✅ API com Memória Pronta!")

# --- ENDPOINT (A ROTA) ---
@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    # Rota que o Frontend vai chamar.
    
    try:
        # Invoca a cadeia inteira.
        # O 'configurable' é onde passamos o ID da sessão para o LangChain saber quem é quem.
        resposta = rag_chain_with_history.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}}
        )
        return {"response": resposta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))