# Arquivo: versao_2_estruturada/app/routers/chat.py
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import rag_service

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"📩 Mensagem recebida: {request.message}")
        
        resposta_texto = rag_service.get_response(
            session_id=request.session_id, 
            message=request.message
        )
        
        return ChatResponse(response=resposta_texto)
    except Exception as e:
        print(f"❌ Erro no endpoint /chat: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar mensagem.")