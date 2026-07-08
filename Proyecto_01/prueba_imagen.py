import os
from agent import DataClassifierAgent

# 1. Inicializar el agente
agent = DataClassifierAgent()

# 2. Definir la ruta de su imagen (puede ser PNG, JPG, JPEG, etc.)
# Reemplace esto con la ruta real a su archivo
ruta_imagen = "data/images/ticket_01.jpg" 

# 3. Ejecutar el análisis
if os.path.exists(ruta_imagen):
    print(f"Analizando la imagen: '{ruta_imagen}'...")
    
    # El agente procesará la imagen en base64 y la enviará a Ollama
    resultado = agent.analyze_image(ruta_imagen)
    
    print("\n=== RESULTADO DEL ANÁLISIS ===")
    if resultado["success"]:
        print(f"Categoría Detectada: {resultado['category']}")
        print(f"Confianza:           {resultado['confidence'] * 100:.1f}%")
        print(f"Descripción:\n{resultado['description']}")
    else:
        print(f"Error: {resultado['description']}")
else:
    print(f"Error: El archivo de imagen no existe en: {ruta_imagen}")