"""
Configuración de Fixtures y Utilidades para pytest.

Este archivo define las fixtures compartidas por las pruebas unitarias.
Las fixtures permiten reutilizar instancias del chatbot y configurar mocks
de manera limpia y modular.
"""

import pytest
import requests
from config import OLLAMA_API_URL
from chatbot import SelfRefineChatbot


@pytest.fixture
def chatbot_debug():
    """Retorna una instancia limpia del chatbot en modo debug."""
    return SelfRefineChatbot(debug_mode=True)


@pytest.fixture
def chatbot_no_debug():
    """Retorna una instancia limpia del chatbot sin modo debug."""
    return SelfRefineChatbot(debug_mode=False)


def ollama_esta_activo() -> bool:
    """
    Comprueba si el servidor local de Ollama está encendido y accesible.
    Permite decidir dinámicamente si omitir o ejecutar las pruebas de integración.
    """
    try:
        respuesta = requests.get(OLLAMA_API_URL, timeout=2)
        return respuesta.status_code == 200
    except requests.RequestException:
        return False
