import os
import sys
import time
import requests
from agent import DataClassifierAgent
import generate_mock_data
from logger_config import logger

def is_ollama_active():
    """Valida si la API local de Ollama está activa."""
    try:
        response = requests.get("http://localhost:11434", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def print_separator(char="=", length=65):
    print(char * length)

def main():
    print_separator()
    print("      AGENTE DE CLASIFICACIÓN DE DATOS CON LLM LOCAL (OLLAMA)      ")
    print("               Evaluación y Visión con Qwen3-VL-4B                 ")
    print_separator()
    
    # 1. Asegurar que los datos y las imágenes mock estén generados
    print("\n[Paso 1] Generando dataset local e imágenes de prueba...")
    generate_mock_data.main()
    print("[OK] Dataset e imágenes creados en la carpeta './data/'")
    
    # 2. Inicializar agente
    print("\n[Paso 2] Inicializando el agente clasificador...")
    agent = DataClassifierAgent()
    
    # 3. Comprobar estado de Ollama
    ollama_running = is_ollama_active()
    print("\n[Paso 3] Comprobando conexion con Ollama en localhost:11434...")
    
    if not ollama_running:
        print_separator("!", 65)
        print("[WARNING] ADVERTENCIA: Ollama no se encuentra en ejecucion o esta inaccesible!")
        print("Para ejecutar el analisis en tiempo real:")
        print("  1. Inicie la aplicacion de Ollama en su maquina.")
        print(f"  2. Asegurese de tener el modelo '{agent.model}' descargado (ollama pull {agent.model}).")
        print_separator("!", 65)
        
        # Ejecutar demostración mockeada
        print("\n--> Ejecutando demostracion simulada (MOCK DRY-RUN) <--")
        demo_mock(agent)
    else:
        print(f"[OK] Ollama esta activo. Modelo configurado: '{agent.model}'")
        print("[OK] Iniciando clasificacion de textos e imagenes reales...")
        
        # Ejecutar evaluación real contra Ollama
        run_real_evals(agent)
        
    print_separator()
    print("[OK] Demostracion completada! Revise el archivo 'agent.log' para ver los logs detallados.")
    print_separator()

def demo_mock(agent):
    """Ejecuta una demostración usando mocks en caso de no tener Ollama activo."""
    from unittest.mock import patch, MagicMock
    
    print("\n--- [DEMO TEXTO MOCKEADO] ---")
    mock_content = '{"category": "Error de Base de Datos", "description": "El log describe un timeout de conexion a la base de datos db-instance-01 en el puerto estandar.", "confidence": 0.96}'
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": mock_content}
        }
        mock_post.return_value = mock_response
        
        # Clasificar texto
        sample_log = "Error: Connection timeout at database pool connection. Failure code 504. Host: db-instance-01.internal"
        result = agent.classify_text(sample_log, ["Queja", "Error de Base de Datos", "Alerta"])
        
        print(f"Texto a clasificar: '{sample_log}'")
        print(f"Categoria Detectada: {result['category']}")
        print(f"Confianza:           {result['confidence'] * 100:.1f}%")
        print(f"Descripcion:         {result['description']}")
        print(f"Latencia Simulada:   {result['latency_sec']:.4f} seg")
        
    print("\n--- [DEMO IMAGEN MOCKEADA] ---")
    mock_img_content = '{"category": "Factura", "description": "Se identifica un formato de factura estructurado que detalla licencias de software, consultoria e IVA con un total de $2,378.00 USD.", "confidence": 0.98}'
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": mock_img_content}
        }
        mock_post.return_value = mock_response
        
        # Analizar imagen factura
        image_path = "data/images/factura.png"
        result = agent.analyze_image(image_path)
        
        print(f"Imagen a analizar:  '{image_path}'")
        print(f"Categoria Detectada: {result['category']}")
        print(f"Confianza:           {result['confidence'] * 100:.1f}%")
        print(f"Descripcion:         {result['description']}")

def run_real_evals(agent):
    """Ejecuta la clasificación y el análisis de visión real contra la API local de Ollama."""
    # 1. Textos
    text_samples = [
        ("Me encanta la nueva interfaz web, es extremadamente fluida y rapida. Felicitaciones!", ["Queja", "Felicitacion", "Duda"]),
        ("Alerta critica de almacenamiento: El volumen /dev/sda1 ha alcanzado el 95% de capacidad.", ["Alerta de Infraestructura", "Error de Base de Datos", "Queja"])
    ]
    
    print("\n================== CLASIFICACION DE TEXTOS REALES ==================")
    for text, categories in text_samples:
        print_separator("-", 50)
        print(f"Texto de Entrada: '{text}'")
        print("Clasificando...")
        
        result = agent.classify_text(text, categories)
        
        if result["success"]:
            print(f"[OK] Categoria:   {result['category']}")
            print(f"[OK] Confianza:   {result['confidence'] * 100:.1f}%")
            print(f"[OK] Justificacion: {result['description']}")
            print(f"[OK] Latencia:    {result['latency_sec']:.2f} segundos")
        else:
            print(f"[ERROR] Fallo la clasificacion: {result['description']}")
            
    # 2. Imágenes
    image_samples = [
        ("data/images/factura.png", "Factura"),
        ("data/images/ticket.png", "Ticket"),
        ("data/images/logo.png", "Logo")
    ]
    
    print("\n================== ANALISIS DE IMAGENES REALES (VISION) ==================")
    for img_path, expected in image_samples:
        print_separator("-", 50)
        print(f"Ruta de Imagen: '{img_path}' (Esperado: {expected})")
        print("Analizando imagen con vision multimodal...")
        
        result = agent.analyze_image(img_path)
        
        if result["success"]:
            print(f"[OK] Categoria Detectada: {result['category']}")
            print(f"[OK] Confianza:           {result['confidence'] * 100:.1f}%")
            print(f"[OK] Descripcion LLM:\n{result['description']}")
            print(f"[OK] Latencia:            {result['latency_sec']:.2f} segundos")
        else:
            print(f"[ERROR] Fallo el analisis de imagen: {result['description']}")

if __name__ == "__main__":
    main()
