# Evals - Proyectos de Inteligencia Artificial

Este repositorio contiene una colección de proyectos prácticos de Inteligencia Artificial y Agentes Inteligentes, enfocados en clasificación multimodal, auto-evaluación (Self-Refine) y pruebas automatizadas (Evals) utilizando LLMs locales.

## 📂 Proyectos Incluidos

### 1. [Proyecto 01: Agente de Clasificación Multimodal](file:///Proyecto_01/README.md)
* **Descripción**: Agente en Python para la clasificación de datos no estructurados y análisis visual de imágenes (facturas, tickets de compra, logotipos) a través de la API local de **Ollama** utilizando **Qwen3-VL-4B**.
* **Características**: Parser robusto, generación programática de datos sintéticos con Pillow, logs estructurados y suite de pruebas unitarias/integración con Pytest.
* **Carpeta**: [Proyecto_01/](file:///Proyecto_01)

### 2. [Proyecto 01b: Chatbot con Auto-Evaluación (Self-Refine)](file:///Proyecto_01b/README.md)
* **Descripción**: Agente conversacional interactivo (EcoShop Chatbot) implementado con el paradigma **Self-Refine** para auditoría y corrección en tiempo real de sus propias respuestas antes de entregarlas al usuario.
* **Características**: Arquitectura generador/auditor con temperaturas optimizadas, parser flexible con fallback de expresiones regulares y mocks de LLM en Pytest para pruebas instantáneas.
* **Carpeta**: [Proyecto_01b/](file:///Proyecto_01b)

---

## 🛠️ Requisitos Generales

- **Python 3.8+** (recomendado 3.10+)
- **Ollama** ejecutándose localmente ([ollama.com](https://ollama.com))
- Modelos locales requeridos (según el proyecto):
  - `qwen3-vl:4b` (o equivalente multimodal como `qwen2.5-vl:3b`)
  - `gemma4:latest` (o modelo similar)

Para instrucciones específicas de instalación, configuración y ejecución, por favor dirígete al `README.md` dentro de la carpeta de cada proyecto.
