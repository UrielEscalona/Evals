import os
import time
import base64
import json
import requests
from dotenv import load_dotenv
from logger_config import logger

# Cargar variables de entorno
load_dotenv()

class DataClassifierAgent:
    """
    Agente de clasificación de datos no estructurados y análisis de imágenes
    que consume la API local de Ollama utilizando el modelo Qwen3-VL-4B.
    """
    def __init__(self):
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3-vl:4b")
        logger.info(f"Agente inicializado con modelo: '{self.model}' y URL de API: '{self.api_url}'")

    def _call_ollama(self, messages: list) -> dict:
        """
        Envía una solicitud POST a la API local de Ollama con un esquema JSON forzado.
        Registra el tiempo de respuesta, modelo usado y posibles errores.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json"  # Forzar respuesta estructurada en formato JSON
        }
        
        start_time = time.time()
        logger.info(f"Enviando solicitud a Ollama [{self.model}]...")
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            elapsed_time = time.time() - start_time
            
            # Verificar si la petición fue exitosa (código 200)
            if response.status_code != 200:
                error_msg = f"Error de Ollama API. Código de estado: {response.status_code}. Detalle: {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "latency_sec": elapsed_time
                }
            
            # Parsear la respuesta
            response_json = response.json()
            message_content = response_json.get("message", {}).get("content", "").strip()
            
            logger.info(f"Respuesta recibida exitosamente en {elapsed_time:.2f} segundos.")
            
            # Intentar parsear el contenido de la respuesta a un diccionario JSON
            try:
                parsed_content = json.loads(message_content)
                return {
                    "success": True,
                    "data": parsed_content,
                    "latency_sec": elapsed_time
                }
            except json.JSONDecodeError as jde:
                error_msg = f"No se pudo decodificar el contenido de la respuesta como JSON: '{message_content}'. Error: {str(jde)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "raw_content": message_content,
                    "latency_sec": elapsed_time
                }
                
        except requests.exceptions.RequestException as re:
            elapsed_time = time.time() - start_time
            error_msg = f"Error de conexión con Ollama en {self.api_url}. ¿Está Ollama ejecutándose? Error: {str(re)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "latency_sec": elapsed_time
            }

    def _parse_robust(self, data: dict) -> dict:
        """
        Parsea de forma extremadamente robusta las respuestas del LLM,
        soportando múltiples idiomas (español/inglés) y capitalizaciones de claves,
        así como valores descriptivos de confianza (por ejemplo, 'high' o 'alta').
        """
        logger.info(f"Parseando robustamente: {data}")
        # 1. Mapear categoría
        category = "Desconocido"
        for k in ["category", "Category", "categoria", "Categoria", "categoría", "Categoría"]:
            if k in data:
                category = data[k]
                break
                
        # 2. Mapear descripción
        description = "Sin descripción provista por el modelo."
        for k in ["description", "Description", "descripcion", "Descripcion", "descripción", "Descripción", "justification", "justificación"]:
            if k in data:
                description = data[k]
                break
                
        # 3. Mapear confianza
        confidence = 0.0
        for k in ["confidence", "Confidence", "confianza", "Confianza"]:
            if k in data:
                val = data[k]
                if isinstance(val, (int, float)):
                    confidence = float(val)
                elif isinstance(val, str):
                    val_clean = val.strip().lower()
                    if "high" in val_clean or "alta" in val_clean or "alto" in val_clean:
                        confidence = 0.95
                    elif "medium" in val_clean or "media" in val_clean or "medio" in val_clean:
                        confidence = 0.75
                    elif "low" in val_clean or "baja" in val_clean or "bajo" in val_clean:
                        confidence = 0.50
                    else:
                        try:
                            confidence = float(val_clean)
                        except ValueError:
                            confidence = 0.85
                break
                
        return {
            "category": category,
            "description": description,
            "confidence": confidence
        }

    def classify_text(self, text: str, categories: list) -> dict:
        """
        Clasifica un texto o log no estructurado dentro de las categorías indicadas.
        Retorna un diccionario con la categoría seleccionada, justificación y confianza.
        """
        logger.info(f"Iniciando clasificación de texto. Longitud del texto: {len(text)} caracteres.")
        
        system_prompt = (
            "Eres un asistente experto en clasificación y análisis de datos. "
            "Tu tarea es clasificar el texto proporcionado por el usuario en EXACTAMENTE UNA de las siguientes categorías:\n"
            f"{categories}\n\n"
            "Debes responder EXCLUSIVAMENTE con un objeto JSON estructurado que contenga las siguientes claves:\n"
            "- 'category': La categoría seleccionada de la lista provista.\n"
            "- 'description': Una breve descripción en español de por qué se seleccionó esa categoría (justificación lógica).\n"
            "- 'confidence': Un número flotante entre 0.0 y 1.0 que indica tu nivel de confianza en la clasificación.\n"
            "No incluyas explicaciones previas, ni markdown de código, ni texto adicional fuera del JSON."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Clasifica este texto:\n'{text}'"}
        ]
        
        result = self._call_ollama(messages)
        
        if not result["success"]:
            # Retornar estructura fallback en caso de error
            return {
                "success": False,
                "category": "Error",
                "description": f"Fallo al procesar la clasificación de texto: {result.get('error')}",
                "confidence": 0.0,
                "latency_sec": result.get("latency_sec", 0.0)
            }
            
        # Extraer campos de la respuesta decodificada con valores por defecto seguros usando parseo robusto
        parsed = self._parse_robust(result["data"])
        return {
            "success": True,
            "category": parsed["category"],
            "description": parsed["description"],
            "confidence": parsed["confidence"],
            "latency_sec": result["latency_sec"]
        }

    def analyze_image(self, image_path: str, prompt: str = None, categories: list = None) -> dict:
        """
        Analiza una imagen (factura, ticket, logo, etc.) utilizando Qwen3-VL-4B.
        Codifica la imagen a base64 y la envía a la API de Ollama.
        """
        if not os.path.exists(image_path):
            error_msg = f"El archivo de imagen no existe en la ruta especificada: {image_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "category": "Error",
                "description": error_msg,
                "confidence": 0.0,
                "latency_sec": 0.0
            }
            
        logger.info(f"Iniciando análisis de imagen en la ruta: '{image_path}'")
        
        # Codificar la imagen a base64
        try:
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            error_msg = f"Error al abrir o codificar la imagen: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "category": "Error",
                "description": error_msg,
                "confidence": 0.0,
                "latency_sec": 0.0
            }
            
        # Prompt por defecto si no se provee uno personalizado
        if not prompt:
            prompt = (
                "Describe detalladamente la imagen proporcionada. Clasifícala como una de las siguientes categorías:\n"
                f"{categories if categories else ['Factura', 'Ticket', 'Logo', 'Otro']}\n"
                "e indica claramente qué elementos visuales o textuales te permitieron llegar a esa conclusión."
            )
            
        system_prompt = (
            "Eres un agente experto en visión artificial y análisis de documentos e imágenes. "
            "Tu tarea es analizar la imagen provista (que puede ser una factura, un ticket de compra, un logo, etc.) "
            "y retornar un análisis estructurado en formato JSON.\n"
            "El objeto JSON retornado debe tener EXACTAMENTE las siguientes claves:\n"
            "- 'category': La categoría del documento ('Factura', 'Ticket', 'Logo' u 'Otro').\n"
            "- 'description': Una descripción detallada en español de lo que se observa en la imagen y qué elementos justifican tu respuesta.\n"
            "- 'confidence': Un número flotante entre 0.0 y 1.0 que indique tu nivel de certeza.\n"
            "Responde EXCLUSIVAMENTE con el objeto JSON estructurado."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": prompt,
                "images": [base64_image]
            }
        ]
        
        result = self._call_ollama(messages)
        
        if not result["success"]:
            return {
                "success": False,
                "category": "Error",
                "description": f"Fallo al procesar el análisis de imagen: {result.get('error')}",
                "confidence": 0.0,
                "latency_sec": result.get("latency_sec", 0.0)
            }
            
        parsed = self._parse_robust(result["data"])
        return {
            "success": True,
            "category": parsed["category"],
            "description": parsed["description"],
            "confidence": parsed["confidence"],
            "latency_sec": result["latency_sec"]
        }
