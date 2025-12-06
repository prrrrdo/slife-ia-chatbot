# Arquivo: versao_2_estruturada/app/services/rag_service.py
import os
import pandas as pd
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.config import settings

# Armazenamento de histórico em memória RAM
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

class RAGService:
    def __init__(self):
        print("🚀 Inicializando Serviço RAG...")
        
        # VERIFICAÇÃO DE SEGURANÇA
        if not settings.GOOGLE_API_KEY:
            print("❌ ERRO CRÍTICO: A chave GOOGLE_API_KEY não foi encontrada.")
            print("   Verifique se o arquivo .env está na raiz do projeto 'atividade-ia-slife'")
            raise ValueError("Chave de API ausente")

        # 1. Carregar e Processar Dados do CSV
        docs = self._carregar_dados_csv()
        
        if not docs:
            raise RuntimeError("❌ Falha crítica: Nenhum dado foi carregado do CSV.")

        # 2. Criar Banco Vetorial em Memória (FAISS)
        print("🧠 Criando índice vetorial na memória...")
        try:
            # AQUI ESTÁ A CORREÇÃO PRINCIPAL: google_api_key=...
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.GOOGLE_API_KEY 
            )
            
            vector_store = FAISS.from_documents(docs, embeddings)
            
            retriever = vector_store.as_retriever(
                search_type="mmr", 
                search_kwargs={"k": 20, "fetch_k": 100, "lambda_mult": 0.6}
            )
            print("✅ Banco vetorial criado com sucesso!")
        except Exception as e:
            raise RuntimeError(f"Erro ao criar vetores (Embeddings): {e}")

        # 3. Configurar o Modelo Gemini
        # AQUI TAMBÉM: google_api_key=...
        llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME, 
            temperature=0.7,
            google_api_key=settings.GOOGLE_API_KEY
        )

        # 4. Configurar as Chains
        
        # A) Reformulação
        contextualize_q_system_prompt = """
        Dado um histórico de chat e a última pergunta do usuário, 
        formule uma pergunta autônoma que possa ser entendida sem o histórico. 
        NÃO responda, apenas reformule se necessário.
        """
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = (
            contextualize_q_prompt
            | llm
            | StrOutputParser()
            | retriever
        )

        # B) Resposta Final
        qa_system_prompt = """
        Você é o assistente virtual da SLife (Moradia Universitária).
        
        DIRETRIZES:
        1. Use os contextos fornecidos para responder.
        2. Se encontrar imóveis, cite o ID, Cidade e Valor.
        3. Seja cordial e objetivo.
        
        CONTEXTO:
        {context}
        """
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

        question_answer_chain = (
            RunnablePassthrough.assign(context=history_aware_retriever)
            | qa_prompt
            | llm
            | StrOutputParser()
        )

        self.chain = RunnableWithMessageHistory(
            question_answer_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def _carregar_dados_csv(self):
        print(f"📂 Lendo CSV: {settings.CSV_PATH}")
        if not os.path.exists(settings.CSV_PATH):
            print(f"❌ Arquivo não encontrado: {settings.CSV_PATH}")
            return []

        try:
            df = pd.read_csv(settings.CSV_PATH, sep=';', decimal=',')
            documentos = []
            for _, row in df.iterrows():
                texto = (
                    f"Imóvel ID {row['imovel_id']} tipo {row['tipo']} em {row['cidade']}. "
                    f"Valor: R$ {row['valor_aluguel']}. "
                    f"{row['quartos']} quartos. Mobília: {'Sim' if row['tem_mobilia'] else 'Não'}. "
                )
                documentos.append(Document(page_content=texto, metadata={"id": row['imovel_id']}))
            
            print(f"📊 {len(documentos)} imóveis carregados.")
            return documentos
        except Exception as e:
            print(f"❌ Erro CSV: {e}")
            return []

    def get_response(self, session_id: str, message: str) -> str:
        return self.chain.invoke(
            {"input": message},
            config={"configurable": {"session_id": session_id}}
        )

rag_service = RAGService()