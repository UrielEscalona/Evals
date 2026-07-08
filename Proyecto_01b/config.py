"""
Módulo de Configuración para el Chatbot de Servicio al Cliente con Self-Refine.

Este archivo centraliza todos los parámetros del sistema para facilitar su
ajuste y experimentación. Al ser un proyecto educativo, cada parámetro
está documentado con su propósito.
"""

# Dirección de la API local de Ollama.
# Por defecto, Ollama se ejecuta en el puerto 11434.
OLLAMA_API_URL = "http://localhost:11434"

# Modelo de lenguaje que utilizaremos.
# En este entorno, usaremos 'gemma4:latest' según la configuración local de Ollama.
MODEL_NAME = "gemma4:latest"

# Parámetros del Ciclo Self-Refine
# ---------------------------------
# Número máximo de veces que el chatbot intentará evaluar y corregir su respuesta.
# Un límite de 3 es un buen balance para evitar bucles infinitos y consumo excesivo de tiempo.
MAX_REFINEMENT_ITERATIONS = 3

# Temperaturas de inferencia (Controlan la creatividad del modelo, de 0.0 a 1.0)
# -----------------------------------------------------------------------------

# Temperatura para la generación inicial:
# Un valor intermedio (0.5) permite que la respuesta sea natural y amable,
# pero se mantiene relativamente apegada al contexto proporcionado.
TEMPERATURE_GENERATION = 0.5

# Temperatura para la crítica (evaluación propia):
# Un valor bajo (0.0 o 0.1) fuerza al modelo a ser lo más analítico, frío y
# determinista posible al juzgar si hay errores o violaciones de seguridad.
TEMPERATURE_CRITIC = 0.0

# Temperatura para el refinamiento:
# Un valor bajo-medio (0.3) ayuda a que el modelo corrija con precisión
# siguiendo las indicaciones de la crítica, sin desviarse demasiado.
TEMPERATURE_REFINEMENT = 0.3
