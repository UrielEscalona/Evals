import os
import pytest
import requests
from unittest.mock import patch, MagicMock
from agent import DataClassifierAgent

# Función auxiliar para comprobar si Ollama está disponible localmente
def is_ollama_available():
    try:
        response = requests.get("http://localhost:11434", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# ==========================================
# 1. PRUEBAS UNITARIAS CON MOCKS (Simuladas)
# ==========================================

@patch('requests.post')
def test_classify_text_mocked(mock_post, agent):
    """
    Verifica que classify_text procese la respuesta simulada de Ollama,
    retornando la estructura JSON esperada con las claves correctas.
    """
    # Configurar respuesta simulada exitosa
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "role": "assistant",
            "content": '{"category": "Queja", "description": "El cliente expresa enojo porque tardaron 3 horas en responder.", "confidence": 0.95}'
        }
    }
    mock_post.return_value = mock_response

    text = "El servicio al cliente fue terrible, tardaron 3 horas en responder."
    categories = ["Queja", "Duda", "Felicitación"]
    
    result = agent.classify_text(text, categories)
    
    # Aserciones
    assert result["success"] is True
    assert result["category"] == "Queja"
    assert "tardaron 3 horas" in result["description"]
    assert result["confidence"] == 0.95
    assert result["latency_sec"] >= 0
    
    # Verificar que requests.post fue llamado con los argumentos correctos
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["format"] == "json"
    assert kwargs["json"]["model"] == agent.model

@patch('requests.post')
def test_analyze_image_mocked(mock_post, agent, dataset_content):
    """
    Verifica que analyze_image abra el archivo de imagen de prueba,
    lo codifique en base64 y retorne los campos mapeados desde el mock.
    """
    # Configurar respuesta simulada para análisis de imagen
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "role": "assistant",
            "content": '{"category": "Factura", "description": "Se observa una factura detallada con un total neto.", "confidence": 0.98}'
        }
    }
    mock_post.return_value = mock_response

    # Usar la ruta de factura generada
    factura_info = dataset_content["image_tests"][0]
    image_path = factura_info["path"]
    
    result = agent.analyze_image(image_path)
    
    # Aserciones
    assert result["success"] is True
    assert result["category"] == "Factura"
    assert "factura detallada" in result["description"]
    assert result["confidence"] == 0.98
    
    # Verificar que el payload contiene la imagen base64
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert len(payload["messages"][1]["images"]) == 1
    # Asegurar que se haya codificado como base64 válido (sin saltos de línea al inicio)
    assert payload["messages"][1]["images"][0] != ""

@patch('requests.post')
def test_agent_error_handling_http_error(mock_post, agent):
    """
    Verifica que el agente maneje errores HTTP (por ejemplo, código 500)
    de forma segura, retornando una estructura fallback con éxito falso.
    """
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    result = agent.classify_text("Prueba de error", ["Categoría"])
    
    assert result["success"] is False
    assert result["category"] == "Error"
    assert "Código de estado: 500" in result["description"]
    assert result["confidence"] == 0.0

@patch('requests.post')
def test_agent_error_handling_connection_failure(mock_post, agent):
    """
    Verifica que el agente capture excepciones de conexión (Ollama apagado)
    y retorne la estructura segura correspondiente.
    """
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
    
    result = agent.classify_text("Prueba de fallo de conexión", ["Categoría"])
    
    assert result["success"] is False
    assert result["category"] == "Error"
    assert "Error de conexión" in result["description"]
    assert result["confidence"] == 0.0

def test_analyze_image_file_not_found(agent):
    """
    Verifica el comportamiento seguro del agente cuando se le solicita
    analizar un archivo de imagen inexistente.
    """
    result = agent.analyze_image("data/images/no_existe.png")
    
    assert result["success"] is False
    assert result["category"] == "Error"
    assert "no existe en la ruta" in result["description"]
    assert result["confidence"] == 0.0


# ==========================================
# 2. PRUEBAS DE INTEGRACIÓN REALES (Evals)
# ==========================================

@pytest.mark.skipif(not is_ollama_available(), reason="Ollama no está en ejecución localmente")
def test_classify_text_real_eval(agent):
    """
    Evaluación real: verifica que el modelo local de Ollama clasifique texto
    y retorne un JSON con el esquema y campos requeridos.
    """
    text = "Error crítico: Memory leak detected in database module. Out of memory exception."
    categories = ["Queja", "Duda", "Error de Base de Datos", "Alerta de Infraestructura"]
    
    result = agent.classify_text(text, categories)
    
    assert result["success"] is True
    assert result["category"] in categories
    assert isinstance(result["description"], str)
    assert len(result["description"]) > 0
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["latency_sec"] > 0
    print(f"\n[INTEGRACIÓN] Texto clasificado como: '{result['category']}' con confianza {result['confidence']:.2f}")

@pytest.mark.skipif(not is_ollama_available(), reason="Ollama no está en ejecución localmente")
def test_analyze_image_real_eval(agent, dataset_content):
    """
    Evaluación real de visión: envía la factura autogenerada al modelo
    qwen3-vl:4b y verifica que se devuelva una descripción y estructura correctas.
    """
    factura_info = dataset_content["image_tests"][0] # factura.png
    image_path = factura_info["path"]
    
    result = agent.analyze_image(image_path)
    
    assert result["success"] is True
    # Debería reconocer la factura como 'Factura' o al menos responder un esquema válido
    assert result["category"] in ["Factura", "Ticket", "Logo", "Otro"]
    assert isinstance(result["description"], str)
    assert len(result["description"]) > 0
    assert 0.0 <= result["confidence"] <= 1.0
    print(f"\n[INTEGRACIÓN] Imagen '{image_path}' analizada como: '{result['category']}'")
    print(f"Descripción del LLM: {result['description']}")
