import os
import shutil
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from chromadb import PersistentClient
from chromadb.config import Settings as ChromaSettings

#modelo de embeddings a utilizar
EMBED_MODEL = "mxbai-embed-large"

# Directorio donde se almacenará la base de datos de vectores
CHROMA_DIR = "chroma_db_e5"

# Nombre de la colección que se usará para el RAG
COLLECTION_NAME = "rag_collection"

# Crea una instancia global de embeddings usando el modelo definido
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

def create_chat_model(model_name: str) -> ChatOllama:
    return ChatOllama(
        model=model_name,
        temperature=0.3,
    )

# Crea una instancia de la base de datos vectorial Chroma
def create_vectordb():
    client = PersistentClient(
        path=CHROMA_DIR,
        settings=ChromaSettings(allow_reset=True)  # Permite reiniciar desde código
    )
    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,  #convertir documentos en vectores
        persist_directory=CHROMA_DIR
    )

# Variable global para guardar una única instancia del vectorstore durante la ejecución
_vectordb = None

# Devuelve la instancia global de vectorstore; si no existe, la crea
def get_vectordb():
    global _vectordb
    if _vectordb is None:
        _vectordb = create_vectordb()
    return _vectordb

# Reinicia la base de datos vectorial:
# - borra la instancia actual
# - elimina los datos del disco
# - crea una nueva base limpia
def reset_vectordb():
    global _vectordb
    # Resetea cliente actual si existe
    if _vectordb:
        _vectordb._client.reset()  # Limpieza lógica (no elimina archivos)
        _vectordb._client = None
        _vectordb = None

    # Elimina subdirectorios en el directorio de Chroma
    if os.path.exists(CHROMA_DIR):
        for item in os.listdir(CHROMA_DIR):
            item_path = os.path.join(CHROMA_DIR, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Elimina subcarpetas

    # Crea nueva instancia desde cero
    _vectordb = create_vectordb()
    return _vectordb
