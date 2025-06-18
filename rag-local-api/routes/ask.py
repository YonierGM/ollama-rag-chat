from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import Optional

# Importaciones internas del proyecto
from config import settings  # Configuraciones generales (como embeddings y vectordb)
from config.prompt_template import build_prompt  # Función para construir el prompt enriquecido
from config.settings import create_chat_model  # Función que crea una instancia del modelo de chat
from config.history import get_last_pairs, add_pair, get_full_history  # Funciones de historial en Redis
from langchain.schema import HumanMessage  # Representa un mensaje del usuario en LangChain
from config.utils import is_valid_model  # Función para validar si el modelo está cargado en Ollama

import time  # Para medir tiempos de ejecución

router = APIRouter()

#datos que se esperan recibir en la solicitud
class AskModelRequest(BaseModel):
    question: str  # Pregunta del usuario
    model: str  # Nombre del modelo a usar

# Ruta para procesar la pregunta del usuario
@router.post("/ask_model")
async def ask_model(req: AskModelRequest):
    # Validación básica de campos requeridos
    if not req.model or not req.question:
        raise HTTPException(status_code=400, detail="Complete todos los campos de la pregunta y el modelo.")

    # Verifica si el modelo existe en Ollama
    if not is_valid_model(req.model):
        raise HTTPException(status_code=400, detail=f"El modelo '{req.model}' no está disponible en Ollama.")

    # Obtiene la instancia actual de la base de vectores
    vectordb = settings.get_vectordb()

    # Verifica si hay documentos previamente indexados
    if vectordb._collection.count() == 0:
        raise HTTPException(status_code=400, detail="No hay documentos indexados. Ingeste archivos primero.")

    # Recupera los últimos 2 pares pregunta-respuesta desde Redis para dar contexto al modelo
    last_pairs = get_last_pairs(k=2)
    history_text = "\n".join(
        f"👤 Usuario: {item['question']}\n🤖 IA: {item['answer']}"
        for item in last_pairs
    )

    # Mide el tiempo que tarda la recuperación de documentos
    start_retrieval = time.time()

    # Usa búsqueda MMR para obtener los documentos más útiles
    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "lambda_mult": 0.8}
    )
    docs = retriever.invoke(req.question)  # Recupera los documentos más relevantes
    context = "".join(doc.page_content for doc in docs)  # Extrae solo el contenido del documento

    end_retrieval = time.time()
    print(f"Tiempo de recuperación de documentos (retrieval): {end_retrieval - start_retrieval:.2f} segundos")

    #prompt final para el modelo, uniendo la pregunta, contexto y el historial
    prompt = build_prompt(req.question, context, history_text)

    # Crea la instancia del modelo
    model = create_chat_model(req.model)

    # Mide el tiempo de respuesta del modelo
    start_inference = time.time()
    resp = model.invoke([HumanMessage(content=prompt)])  # Envía el mensaje al modelo
    end_inference = time.time()
    print(f"Tiempo de inferencia del modelo (Ollama): {end_inference - start_inference:.2f} segundos")

    # Guarda el nuevo par pregunta-respuesta en el historial de Redis
    add_pair(req.question, resp.content)

    return {
        "question": req.question,
        "model": req.model,
        "answer": resp.content,
        "history": get_full_history()
    }
