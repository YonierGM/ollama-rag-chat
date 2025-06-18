import os
import tempfile
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

#configuración, validaciones, utilidades
from config import settings
from config.utils import validate_file, LOADERS
from langchain_core.documents import Document

router = APIRouter()

# Ruta para ingestar documentos
@router.post("/ingest")
async def ingest(
    files: List[UploadFile] = File(...),  # Permite subir uno o varios archivos
    chunk_size: Optional[int] = Form(1000),  # Tamaño de cada fragmento de texto
    chunk_overlap: Optional[int] = Form(50),  # Porcentaje de solapamiento entre fragmentos
):
    vectordb = settings.get_vectordb()  # Obtiene la instancia actual de la base vectorial

    if not files:
        raise HTTPException(status_code=400, detail="Debes enviar al menos un archivo.")
    
    # Validaciones para los parámetros de chunking
    if chunk_size <= 0:
        raise HTTPException(status_code=400, detail="chunk_size debe ser un número entero positivo.")
    if chunk_overlap < 0:
        raise HTTPException(status_code=400, detail="chunk_overlap no puede ser negativo.")
    if chunk_overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="chunk_overlap debe ser menor que chunk_size.")

    # Variables auxiliares para la respuesta final
    total_chunks = 0
    indexed_files = []
    errors = []

    # Procesamiento de cada archivo recibido
    for file in files:
        validate_file(file)  # Validar tamaño y tipo permitido
        suffix = os.path.splitext(file.filename)[-1].lower()  # Obtener extensión
        tmp_path = None

        # Verificar si hay un loader para la extensión dada
        if suffix not in LOADERS:
            errors.append({"file": file.filename, "error": f"Tipo de archivo no soportado: {suffix}"})
            continue

        try:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            # Cargar el archivo con el loader adecuado
            loader = LOADERS[suffix](tmp_path)
            raw_documents = loader.load()

            # Función auxiliar para extraer texto de un documento
            def extract_text(doc):
                if isinstance(doc, tuple):
                    return doc[0]
                elif isinstance(doc, Document):
                    return doc.page_content
                return str(doc)

            # Verificar si el documento tiene texto legible
            if not raw_documents or all(len(extract_text(doc).strip()) < 20 for doc in raw_documents):
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} parece estar escaneado o no contiene texto extraíble."
                )

            # Convertir los documentos a objetos Document de LangChain
            processed_documents = []
            for doc in raw_documents:
                if isinstance(doc, tuple):
                    content, metadata = doc
                    if not isinstance(metadata, dict):
                        metadata = {"source": file.filename}
                    processed_documents.append(Document(page_content=content, metadata=metadata))
                elif isinstance(doc, Document):
                    processed_documents.append(doc)
                else:
                    processed_documents.append(Document(page_content=str(doc), metadata={"source": file.filename}))

            # Dividir documentos en fragmentos (chunks)
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            docs = splitter.split_documents(processed_documents)

            # Agregar documentos a la base vectorial
            vectordb.add_documents(docs)

            total_chunks += len(docs)
            indexed_files.append(file.filename)

        except HTTPException as ve:
            errors.append({"file": file.filename, "error": ve.detail})
        except Exception as e:
            error_msg = str(e)
            if "Invalid Elementary Object" in error_msg or "Could not read malformed PDF file" in error_msg:
                friendly_error = (
                    f"El archivo '{file.filename}' parece estar dañado o contener contenido no estándar. "
                    "Asegúrate de subir un PDF válido con texto extraíble."
                )
            else:
                friendly_error = f"Hubo un error al procesar '{file.filename}': {error_msg}"
            errors.append({"file": file.filename, "error": friendly_error})
        finally:
            # Elimina el archivo temporal
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            await file.close()

    # Construir la respuesta final
    response = {
        "status": "partial_success" if errors else "indexed",
        "files_indexed": indexed_files,
        "total_chunks": total_chunks,
    }
    if errors:
        response["errors"] = errors
    return response

# Ruta para eliminar todos los embeddings de ChromaDB
@router.delete("/reset_embeddings")
async def reset_embeddings():
    try:
        # Reinicia la base de datos vectorial
        settings.reset_vectordb()
        return {
            "status": "ok",
            "message": "Base de datos reseteada completamente."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al resetear base de datos: {e}")
