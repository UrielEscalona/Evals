import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

def setup_logger(name: str = "agent_logger") -> logging.Logger:
    """
    Configura y retorna un logger que escribe logs tanto en la consola
    como en el archivo 'agent.log'.
    """
    # Obtener el nivel de log desde .env (default: INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    logger = logging.getLogger(name)
    
    # Evitar duplicar manejadores si el logger ya fue configurado
    if logger.handlers:
        return logger
        
    logger.setLevel(log_level)
    
    # Formato común para los mensajes de log
    log_format = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Manejador para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Manejador para archivo 'agent.log' en el espacio de trabajo
    file_handler = logging.FileHandler("agent.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger

# Instancia global del logger lista para usar
logger = setup_logger()
