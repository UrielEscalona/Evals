"""
Cliente de Conexión HTTP para la API de Ollama.

Este módulo gestiona la comunicación directa con el servidor local de Ollama.
Utiliza la biblioteca 'requests' para realizar solicitudes POST al endpoint
de chat (/api/chat), lo cual es ideal para entender cómo viajan los datos
en formato JSON (payloads) entre nuestra aplicación y el servidor LLM.
"""

import requests
import json
from typing import List, Dict, Any
from config import OLLAMA_API_URL, MODEL_NAME


class OllamaClient:
    def __init__(self, api_url: str = OLLAMA_API_URL, model_name: str = MODEL_NAME):
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name
        self.chat_endpoint = f"{self.api_url}/api/chat"

    def enviar_chat(
        self, 
        mensajes: List[Dict[str, str]], 
        temperature: float = 0.5
    ) -> str:
        """
        Envía un historial de chat al modelo de Ollama y devuelve la respuesta de texto.
        
        Args:
            mensajes: Lista de diccionarios en formato [{"role": "user/assistant/system", "content": "..."}]
            temperature: Creatividad del modelo (0.0 a 1.0)
            
        Returns:
            La respuesta en texto plano generada por el LLM.
        """
        # Estructuramos el cuerpo de la solicitud JSON de acuerdo a la API oficial de Ollama.
        # Desactivamos el "streaming" (stream=False) para obtener la respuesta completa
        # de una sola vez y facilitar el procesamiento educativo de este ejercicio.
        payload = {
            "model": self.model_name,
            "messages": mensajes,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            # Hacemos la solicitud POST al servidor local
            respuesta = requests.post(
                self.chat_endpoint, 
                json=payload, 
                timeout=30  # Timeout razonable por si el modelo tarda en cargar
            )
            
            # Verificamos si la petición fue exitosa (código HTTP 200)
            respuesta.raise_for_status()
            
            # Decodificamos la respuesta JSON del servidor
            datos_respuesta = respuesta.json()
            
            # Extraemos el contenido del mensaje generado por el asistente
            contenido_respuesta = datos_respuesta.get("message", {}).get("content", "")
            return contenido_respuesta.strip()
            
        except requests.exceptions.Timeout:
            return "Error de comunicación: La solicitud a Ollama superó el tiempo límite de espera (timeout)."
        except requests.exceptions.ConnectionError:
            return (
                f"Error de comunicación: No se pudo establecer conexión con Ollama en '{self.api_url}'. "
                "Asegúrate de que Ollama está activo corriendo en segundo plano (`ollama serve`)."
            )
        except Exception as e:
            return f"Error inesperado al conectar con Ollama: {str(e)}"
