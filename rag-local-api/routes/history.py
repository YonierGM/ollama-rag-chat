from fastapi import APIRouter, HTTPException

# Importa las funciones del historial
from config.history import get_full_history, clear_history

router = APIRouter()

# Ruta para obtener el historial completo de conversación
@router.get("/history")
async def get_chat_history():
    return get_full_history()

# Ruta para limpiar/eliminar todo el historial de conversación
@router.post("/clearHistory")
async def clear_chat_history():
    try:
        # Llama a la función que elimina el historial en Redis
        clear_history()
        return {"message": "Historial de conversación eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))