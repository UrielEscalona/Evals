import json
import logging
import requests
import urllib3
import config

# Desactivar advertencias de SSL no verificado (útil en entornos educativos/locales con problemas de certificados)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración del logging educativo
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GeminiClient")

class GeminiClient:
    """
    Cliente educativo para interactuar con la API de Google Gemini.
    Utiliza peticiones HTTP directas con la librería 'requests' para evitar dependencias pesadas.
    """
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.chat_model = config.GEMINI_MODEL
        self.embed_model = config.EMBEDDING_MODEL
        
        # Validar la API Key
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
            logger.warning(
                "¡Alerta! GEMINI_API_KEY no está configurada correctamente en el archivo .env. "
                "Las llamadas a la API fallarán. Por favor, edita tu archivo .env con una clave válida."
            )

    def _get_url(self, model: str, action: str) -> str:
        """Construye la URL del endpoint de Gemini."""
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{action}?key={self.api_key}"

    def get_embedding(self, text: str) -> list[float]:
        """
        Genera el vector de embeddings para un texto usando el modelo text-embedding-004.
        
        Para fines educativos, imprimimos la estructura del payload que se envía.
        """
        if not text.strip():
            return [0.0] * 768  # Retornar vector vacío para textos vacíos
            
        url = self._get_url(self.embed_model, "embedContent")
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": f"models/{self.embed_model}",
            "content": {
                "parts": [{"text": text}]
            }
        }

        # Logger educativo: Mostrar cómo viaja la petición (anonimizada)
        logger.debug(f"[API RAG] Enviando texto de longitud {len(text)} para embedding.")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15, verify=False)
            if response.status_code != 200:
                logger.error(f"Error en Embeddings API ({response.status_code}): {response.text}")
                response.raise_for_status()
                
            res_data = response.json()
            embedding = res_data["embedding"]["values"]
            return embedding
        except Exception as e:
            logger.error(f"Excepción al llamar a Gemini Embeddings API: {e}")
            raise e

    def generate_content(self, prompt: str, system_instruction: str = None, temperature: float = 0.1) -> str:
        """
        Envía un prompt a Gemini para generar una respuesta usando el modelo configurado.
        
        Soporta instrucciones del sistema (system_instruction) y control de temperatura.
        """
        url = self._get_url(self.chat_model, "generateContent")
        headers = {"Content-Type": "application/json"}
        
        # Estructurar contenido
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        # Agregar instrucciones de sistema si se proveen
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Logger educativo: Explicamos que los datos se envían ya anonimizados
        logger.info(f"[LLM API] Enviando prompt al modelo {self.chat_model} (Temperatura: {temperature}).")
        logger.debug(f"[LLM API] Prompt enviado:\n--- PROMPT START ---\n{prompt}\n--- PROMPT END ---")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
            if response.status_code != 200:
                logger.error(f"Error en Gemini API ({response.status_code}): {response.text}")
                response.raise_for_status()
                
            res_data = response.json()
            
            # Navegar la respuesta estructurada de Gemini
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                candidate = res_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text_response = candidate["content"]["parts"][0]["text"]
                    logger.info("[LLM API] Respuesta recibida exitosamente.")
                    return text_response
            
            logger.warning(f"La API de Gemini retornó una estructura inesperada: {res_data}")
            return "Error: No se pudo extraer la respuesta del modelo."
            
        except Exception as e:
            logger.error(f"Excepción al llamar a Gemini Chat API: {e}")
            raise e
