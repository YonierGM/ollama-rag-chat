import os
import requests
from fastapi import UploadFile, HTTPException

from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader

# Tamaño máximo permitido para archivos (en MB)
MAX_FILE_SIZE_MB = 8

# Extensiones permitidas para la carga de archivos
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# Diccionario que asocia cada extensión con su cargador correspondiente
LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": lambda path: TextLoader(path, encoding="utf-8"),  # Para archivos de texto plano
}

# validar si un modelo está disponible en el servidor de Ollama
def is_valid_model(model_name: str) -> bool:
    try:
        # Consulta a la API de Ollama para obtener los modelos disponibles
        response = requests.get("http://ollama:11434/api/tags")
        response.raise_for_status()  # Lanza una excepción si hubo error HTTP
        models = response.json().get("models", [])  # Extrae la lista de modelos
        available = [m["name"] for m in models]  # Extrae solo los nombres
        return model_name in available  # Verifica si el modelo está entre los disponibles
    except Exception as e:
        print(f"Error al validar modelo: {e}")
        return False

#validar archivo cargado por el usuario
def validate_file(file: UploadFile):
    # Extrae la extensión del archivo
    ext = os.path.splitext(file.filename)[-1].lower()
    
    # Verifica si la extensión está permitida
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {ext}")

    # Calcula el tamaño del archivo en MB
    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)  # Conversión a megabytes
    file.file.seek(0) 

    # Verifica si excede el tamaño máximo permitido
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande: {size_mb:.2f} MB (máx {MAX_FILE_SIZE_MB} MB)"
        )