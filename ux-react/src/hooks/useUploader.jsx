import { useState, useEffect } from "react";
import { Report } from "notiflix/build/notiflix-report-aio";
import { Confirm } from 'notiflix/build/notiflix-confirm-aio';
import axios from "axios";

export function useUploader() {
  const [selectedFiles, setSelectedFiles] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFiles(event.target.files);
    setResult(null); // Limpiar resultados anteriores al seleccionar nuevos archivos
  };

  const handleUpload = async (chunkSize, chunkOverlap) => {
    if (!selectedFiles || selectedFiles.length === 0) {
      Report.warning("Selección de archivos", "Por favor, selecciona al menos un archivo para subir.", "Ok");
      return;
    }

    const formData = new FormData();
    Array.from(selectedFiles).forEach((file) => {
      formData.append("files", file);
    });

    if (chunkSize !== undefined && chunkSize !== null) {
      formData.append("chunk_size", chunkSize);
    }
    if (chunkOverlap !== undefined && chunkOverlap !== null) {
      formData.append("chunk_overlap", chunkOverlap);
    }

    try {
      setLoading(true);
      const response = await axios.post("http://localhost:8000/ingest", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setResult(response.data);
    } catch (err) {
      const errorMsg =
        err?.response?.data?.detail || "Ocurrió un error al subir los archivos.";
      setResult({
        files_indexed: [],
        total_chunks: 0,
        errors: [{ file: "Error general", error: errorMsg }],
      });
      
      Report.failure("Error en la Ingesta", errorMsg, "Ok");
    } finally {
      setLoading(false);
    }
  };
  
  const handleResetEmbeddings = () => {
    Confirm.show(
      'Confirmación',
      '¿Seguro que deseas eliminar toda la base de datos? Esta acción no se puede deshacer.',
      'Sí, eliminar',
      'No, cancelar',
      async () => {
        try {
          const response = await axios.delete("http://localhost:8000/reset_embeddings");
          const data = response.data;

          Report.success("Base de Datos Reseteada", data.message, "Ok");
          setSelectedFiles(null);
          setResult(null);
        } catch (err) {
          const detail =
            err?.response?.data?.detail || "Error inesperado al conectar con el servidor.";
          Report.failure("Error al procesar", detail, "Ok");
        }
      },
      () => {
        Report.info("Acción Cancelada", "La operación ha sido cancelada.", "Ok");
      },
      {
        width: '320px',
        borderRadius: '8px',
        okButtonBackground: '#dc2626',
        titleColor: '#ef4444',
        messageColor: '#374151',
      }
    );
  };

  return {
    selectedFiles,
    result,
    loading,
    handleFileChange,
    handleUpload,
    handleResetEmbeddings,
    hasIndexed: result?.files_indexed?.length > 0,
    hasErrors: result?.errors?.length > 0,
  };
}