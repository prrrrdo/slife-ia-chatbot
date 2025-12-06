# Arquivo: versao_2_estruturada/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat

# Inicialização da Aplicação
app = FastAPI(
    title="SLife API V2 (Estruturada)",
    description="API de Chatbot imobiliário com arquitetura em camadas",
    version="2.0.0"
)

# Configuração de CORS (Permite conexão do index.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das Rotas
app.include_router(chat.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "version": "2.0.0",
        "message": "API SLife rodando na nova arquitetura!"
    }