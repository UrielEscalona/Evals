import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Configuración del LLM
# Usamos gemini-3.1-flash-lite por especificación del usuario
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-2"

# Rutas de almacenamiento de datos
DATA_DIR = BASE_DIR / "data"
RAW_LAWS_DIR = DATA_DIR / "raw_laws"
TEST_DOCS_DIR = DATA_DIR / "test_documents"
KB_PATH = DATA_DIR / "vector_store.enc"

# Clave de cifrado para la base de datos vectorial.
# En un entorno de producción real, esta clave debe almacenarse en un Gestor de Secretos (Secret Manager).
# Para este proyecto educativo, cargamos una clave estática o la derivamos de una variable de entorno.
ENCRYPTION_KEY_RAW = os.getenv("DB_ENCRYPTION_KEY", "compliance_agent_educational_key_32bytes_!!")
# Asegurar que la clave tenga exactamente 32 bytes para AES-256
import hashlib
ENCRYPTION_KEY = hashlib.sha256(ENCRYPTION_KEY_RAW.encode()).digest()

# Crear los directorios necesarios si no existen
os.makedirs(RAW_LAWS_DIR, exist_ok=True)
os.makedirs(TEST_DOCS_DIR, exist_ok=True)
