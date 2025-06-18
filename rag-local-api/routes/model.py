from fastapi import APIRouter
import requests

router = APIRouter()

#obtiene todos los modelos disponibles en el servidor de Ollama
def get_available_models() -> list[str]:
    try:
        # Realiza una solicitud GET a la API local de Ollama para obtener los modelos disponibles
        response = requests.get("http://ollama:11434/api/tags")
        response.raise_for_status()  # Lanza una excepción si la respuesta es un error HTTP

        # Extrae la lista de modelos
        models = response.json().get("models", [])

        #palabras clave que identifican modelos de embeddings (no de chat)
        excluded_keywords = ["embed", "embedding", "bge", "e5", "mxbai"]

        # Función para determinar si un modelo es de tipo chat (no embedding)
        def is_chat_model(model_name: str) -> bool:
            # Devuelve True solo si no contiene ninguna palabra clave de embeddings
            return not any(keyword in model_name.lower() for keyword in excluded_keywords)

        # Filtra y devuelve solo los modelos válidos para chat
        return [m["name"] for m in models if is_chat_model(m["name"])]

    except Exception as e:
        print(f"Error al obtener modelos: {e}")
        return []

# Ruta GET para listar modelos disponibles (solo los de tipo chat)
@router.get("/models", tags=["Modelos"])
def list_models():
    return {"models": get_available_models()}
