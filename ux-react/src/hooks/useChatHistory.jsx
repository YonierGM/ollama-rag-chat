import { useState, useEffect } from "react";
import axios from "axios";

import { Report } from "notiflix/build/notiflix-report-aio";
import { Confirm } from 'notiflix/build/notiflix-confirm-aio';

export function useChatHistory(historyUrl) {
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState(null);

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    setHistoryError(null);
    try {
      const response = await axios.get(historyUrl);
      setChatHistory(response.data);
    } catch (e) {
      console.error("Error al obtener el historial:", e);
      setHistoryError("Error al cargar el historial. Intente recargar la página.");
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [historyUrl]);

  const handleDeleteHistory = async () => {
      Confirm.show(
      'Confirmación',
      '¿Seguro que deseas eliminar todo el historial? Esta acción no se puede deshacer.',
      'Sí, eliminar',
      'No, cancelar',
      async () => {
        try {
          await axios.post("http://localhost:8000/clearHistory");
          await fetchHistory(); // Reconsulta para asegurar consistencia
          Report.success("Hecho", "Historial eliminado correctamente.", "Entendido");
        } catch (err) {
          console.error("Error al limpiar el historial:", e);
          Report.failure("Error", "No se pudo limpiar el historial.", "Cerrar");
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

  return { chatHistory, setChatHistory, isLoadingHistory, historyError, handleDeleteHistory };
}