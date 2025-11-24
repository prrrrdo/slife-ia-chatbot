# SLife - Chatbot de Recomendação Imobiliária com IA 🏠🤖

Este projeto implementa uma solução de Inteligência Artificial Generativa para a **SLife**, uma proptech focada em moradia universitária. O sistema utiliza técnicas de **RAG (Retrieval-Augmented Generation)** para permitir que estudantes encontrem imóveis através de conversas em linguagem natural, superando os filtros de busca tradicionais.

## 🎯 Objetivo do Projeto
Desenvolver uma interface conversacional inteligente que:
1. Entenda o perfil e necessidades do estudante.
2. Busque semanticamente no catálogo de imóveis da SLife.
3. Recomende opções personalizadas com justificativas amigáveis.

## 🛠️ Arquitetura da Solução
A solução foi construída utilizando:
* **Linguagem:** Python 3.9+
* **Orquestração de IA:** LangChain
* **Banco Vetorial:** FAISS (para busca semântica eficiente)
* **LLM:** OpenAI GPT-3.5/4o (para geração de respostas)
* **API:** FastAPI (backend para conexão com o frontend)
* **Dados:** Processamento de CSV via Pandas

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python instalado.
* Chave de API da OpenAI configurada.

### Instalação
1. Clone o repositório:
   ```bash
   git clone [https://github.com/SEU-USUARIO/atividade-ia-slife.git](https://github.com/SEU-USUARIO/atividade-ia-slife.git)
   cd atividade-ia-slife