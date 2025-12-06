# Arquivo: versao_2_estruturada/app/schemas/chat.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str = "usuario_padrao"  # Valor padrão se o front não enviar
    message: str

class ChatResponse(BaseModel):
    response: str