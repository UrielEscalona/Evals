import os
import dotenv
import google.generativeai as genai

# Cargar variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 1. BASE DE CONOCIMIENTO INTERNA (Ficticia - Empresa "ActumLogos")
KNOWLEDGE_BASE = [
    {
        "id": "sec_01",
        "title": "Política de Seguridad de Contraseñas",
        "content": "En ActumLogos, todas las contraseñas corporativas deben tener un mínimo de 14 caracteres. Deben incluir al menos una letra mayúscula, una minúscula, un número y un carácter especial (ej. !, @, #). Las contraseñas deben ser actualizadas obligatoriamente cada 90 días. Está estrictamente prohibido compartir contraseñas por canales de mensajería como Slack o Teams, o anotarlas en medios físicos.",
        "category": "Seguridad"
    },
    {
        "id": "sec_02",
        "title": "Acceso Remoto y VPN",
        "content": "Para acceder a los servidores internos y herramientas de desarrollo desde fuera de la oficina, los empleados deben utilizar la VPN corporativa 'FortiActum'. El acceso requiere autenticación de dos factores (2FA) configurada en la aplicación 'Google Authenticator'. Queda prohibido conectarse a la VPN desde redes Wi-Fi públicas abiertas sin activar el cifrado adicional.",
        "category": "Seguridad"
    },
    {
        "id": "hr_01",
        "title": "Política de Trabajo Remoto (Home Office)",
        "content": "ActumLogos ofrece un modelo de trabajo híbrido. Los empleados pueden realizar trabajo remoto hasta 2 días por semana, recomendándose los días martes y jueves. Para programar los días de Home Office, se debe solicitar la aprobación del supervisor directo a través de la plataforma 'ActumPeople' con al menos 24 horas de anticipación. Es obligatorio estar disponible en Teams en el horario central de 9:00 AM a 6:00 PM.",
        "category": "Recursos Humanos"
    },
    {
        "id": "hr_02",
        "title": "Reembolso de Gastos de Viaje",
        "content": "Los gastos relacionados con viajes de negocios deben registrarse en la plataforma 'ActumExp' dentro de los 15 días posteriores al término del viaje. Los vuelos de menos de 5 horas de duración deben reservarse en clase económica. Los viáticos diarios para comidas están limitados a un máximo de $50 USD por día, y se requiere cargar facturas digitales válidas para cualquier gasto superior a $10 USD.",
        "category": "Recursos Humanos"
    },
    {
        "id": "hr_03",
        "title": "Código de Conducta y Propiedad Intelectual",
        "content": "Todo código, diseño, algoritmo o documentación desarrollado por los empleados durante su jornada laboral en ActumLogos es propiedad intelectual exclusiva de la empresa. Los empleados no pueden subir código del trabajo a repositorios públicos personales (como GitHub personal) ni utilizar herramientas de IA no autorizadas para procesar datos confidenciales de clientes. La infracción de esta norma conlleva acción disciplinaria.",
        "category": "Recursos Humanos"
    }
]

# 2. RETRIEVER SIMPLE BASADO EN COINCIDENCIA DE PALABRAS CLAVE
def retrieve_context(query: str, top_k: int = 2) -> list:
    """
    Busca en la base de conocimiento los fragmentos más relevantes a la consulta.
    Usa un algoritmo simple de coincidencia de palabras clave (Jaccard / Intersección de tokens)
    para mantener el código ligero y fácil de entender.
    """
    query_words = set(query.lower().replace("?", "").replace("¿", "").split())
    scored_docs = []
    
    for doc in KNOWLEDGE_BASE:
        # Combinar título y contenido para la búsqueda
        text = f"{doc['title']} {doc['content']}".lower()
        # Eliminar signos comunes de puntuación
        for char in [".", ",", "(", ")", "'", '"', "-", "¡", "!"]:
            text = text.replace(char, "")
        
        doc_words = set(text.split())
        
        # Calcular intersección de palabras (similitud de Jaccard simplificada)
        intersection = query_words.intersection(doc_words)
        score = len(intersection) / len(query_words) if query_words else 0
        
        # Dar un pequeño boost si las palabras coinciden en el título
        title_words = set(doc['title'].lower().split())
        title_intersection = query_words.intersection(title_words)
        score += len(title_intersection) * 0.2
        
        scored_docs.append((score, doc))
    
    # Ordenar por puntaje descendente
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # Retornar los top_k más relevantes (siempre que tengan algún puntaje > 0)
    results = [doc for score, doc in scored_docs if score > 0]
    
    # Si no hay coincidencias de palabras clave, devolver los dos primeros documentos por defecto
    if not results:
        results = [doc for _, doc in scored_docs[:top_k]]
        
    return results[:top_k]

# 3. GENERADORES DE RESPUESTAS (Fines Educativos)

def call_gemini(prompt: str, model_name: str = "gemini-3.1-flash-lite") -> str:
    """Realiza una llamada directa a Gemini API."""
    if not api_key:
        return "Error: No se encontró la API Key de Gemini en el archivo .env."
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2}
        )
        return response.text
    except Exception as e:
        return f"Error en la llamada de Gemini API: {str(e)}"

def generate_answer_perfect(query: str, contexts: list) -> str:
    """Genera una respuesta RAG ideal: basada estrictamente en el contexto."""
    context_text = "\n\n".join([f"Documento '{doc['title']}':\n{doc['content']}" for doc in contexts])
    
    prompt = f"""
Eres un asistente de IA corporativo para ActumLogos.
Tu tarea es responder la pregunta del usuario basándote ÚNICAMENTE en la información provista en el Contexto de Referencia.
Si la respuesta no se encuentra en el contexto, di amablemente que no tienes esa información en las políticas corporativas.

Contexto de Referencia:
{context_text}

Pregunta del Usuario:
{query}

Respuesta (sé conciso, directo y 100% verídico respecto al contexto anterior):
"""
    return call_gemini(prompt)

def generate_answer_hallucinated(query: str, contexts: list) -> str:
    """Genera una respuesta con alucinaciones intencionales."""
    context_text = "\n\n".join([f"Documento '{doc['title']}':\n{doc['content']}" for doc in contexts])
    
    prompt = f"""
Eres un asistente de IA corporativo para ActumLogos.
El usuario hará una pregunta. Debes responder la pregunta fingiendo que usas el contexto, pero debes INVENTAR datos, nombres, sistemas o reglas que NO están en el contexto. Por ejemplo, inventa contraseñas de 8 caracteres, nombres de VPN falsos como 'SuperConnect', o viáticos de comida de $500 dólares, etc. 
Asegúrate de que la respuesta suene extremadamente profesional y convincente, pero que contradiga o agregue detalles falsos no presentes en el Contexto.

Contexto de Referencia (Ignóralo parcialmente o contradícelo inventando datos):
{context_text}

Pregunta del Usuario:
{query}

Respuesta Alucinada (sé convincente pero añade mentiras y datos no presentes en el contexto):
"""
    return call_gemini(prompt)

def generate_answer_irrelevant(query: str, contexts: list) -> str:
    """Genera una respuesta que no responde directamente a la pregunta."""
    prompt = f"""
El usuario hará una pregunta. Debes responder algo completamente genérico sobre la tecnología de IA, la transformación digital o la historia de la informática. 
No respondas en absoluto a la pregunta específica del usuario ni utilices el contexto de ActumLogos. Sin embargo, sé formal y amable.

Pregunta del Usuario:
{query}

Respuesta Irrelevante:
"""
    return call_gemini(prompt)
