import os
import json
from redis import Redis
from typing import List, Dict
from datetime import datetime, timezone

# Configuración de conexión a Redis, variables definidas en "api" de docker-compose
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Inicializa el cliente Redis
try:
    redis_client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True  # Hace que las respuestas sean strings en lugar de bytes
    )
    redis_client.ping()  # Verifica si Redis está disponible
    print("Conexión a Redis exitosa.")
except Exception as e:
    print(f"Error al conectar a Redis: {e}")

# Clave por defecto donde se almacenará el historial de conversación
DEFAULT_HISTORY_REDIS_KEY = "conversation_history:default_single_user"

# cargar el historial desde Redis
def _load_history_from_redis() -> List[Dict[str, str]]:
    try:
        history_json = redis_client.get(DEFAULT_HISTORY_REDIS_KEY)
        if history_json:
            return json.loads(history_json)  # Convierte el JSON a lista de diccionarios
    except Exception as e:
        print(f"Error al cargar historial desde Redis: {e}")
    return []

#guardar el historial en Redis
def _save_history_to_redis(history: List[Dict[str, str]]) -> None:
    try:
        redis_client.set(DEFAULT_HISTORY_REDIS_KEY, json.dumps(history))
    except Exception as e:
        print(f"Error al guardar historial en Redis: {e}")

# Retorna todo el historial guardado en Redis
def get_full_history() -> List[Dict[str, str]]:
    return _load_history_from_redis()

# Elimina completamente el historial de Redis
def clear_history() -> None:
    try:
        redis_client.delete(DEFAULT_HISTORY_REDIS_KEY)
    except Exception as e:
        print(f"Error al eliminar historial de Redis: {e}")

# Obtiene los últimos 'k' pares pregunta-respuesta
def get_last_pairs(k: int = 2) -> List[Dict[str, str]]:
    current_history = _load_history_from_redis()
    # Retorna los últimos k elementos si hay suficientes
    return current_history[-k:] if len(current_history) > k else current_history

# Agrega un nuevo par pregunta-respuesta al historial
def add_pair(question: str, answer: str) -> None:
    current_history = _load_history_from_redis()

    # Obtiene la fecha y hora actual
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    current_history.append({
        "question": question,
        "answer": answer,
        "timestamp": timestamp_utc
    })

    # Guarda el historial actualizado
    _save_history_to_redis(current_history)