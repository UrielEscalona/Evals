# 🤖 Chatbot de Servicio al Cliente con Auto-Evaluación (Self-Refine)

¡Bienvenido al proyecto educativo **EcoShop Chatbot**! Este sistema demuestra la implementación práctica de un agente conversacional inteligente equipado con el paradigma **Self-Refine** (Auto-Evaluación y Refinamiento), ejecutado localmente utilizando **Ollama** y validado rigurosamente mediante pruebas automatizadas con **pytest**.

Este repositorio ha sido diseñado con fines didácticos, conteniendo explicaciones detalladas y comentarios minuciosos en cada módulo para facilitar su comprensión paso a paso.

---

## 🎯 ¿Qué es el paradigma "Self-Refine"?

En los modelos de lenguaje tradicionales, el LLM recibe una instrucción y genera una respuesta directa de una sola pasada. Esto a menudo resulta en:
- **Alucinaciones**: Inventar datos que no estaban en el contexto.
- **Fallos lógicos**: Respuestas contradictorias o incoherentes.
- **Riesgos de seguridad**: Revelación involuntaria de instrucciones secretas del sistema o mención inapropiada de competidores.

El paradigma **Self-Refine** soluciona esto agregando un ciclo cerrado de retroalimentación interna:
1. **Generador (Generator)**: Formula un borrador inicial de la respuesta al cliente.
2. **Auto-Crítica (Self-Critic)**: Un segundo prompt en el cual el LLM actúa como un estricto auditor de control de calidad. Revisa si el borrador cumple con las reglas de seguridad y la información oficial de la base de conocimiento.
3. **Refinamiento (Refiner)**: Si el auditor detecta fallos, el LLM reescribe la respuesta tomando en cuenta la crítica, produciendo un borrador mejorado.
4. **Iteración**: Se repite el proceso hasta que la respuesta pase la auditoría limpia o se alcance el número máximo de intentos configurados (evitando bucles infinitos).

---

## ⚙️ Estructura del Proyecto

El repositorio está estructurado de la siguiente forma:

- **`config.py`**: Configuración centralizada. Define parámetros clave como la URL local de Ollama, el nombre del modelo (`gemma4:latest`) y temperaturas óptimas (temperatura alta para que el generador suene amigable y natural, y temperatura de `0.0` para que el evaluador sea sumamente determinista y estricto).
- **`faq_data.py`**: Base de conocimiento con las preguntas frecuentes de la tienda EcoShop (política de devolución, envíos, horarios, etc.) y la lista de reglas de seguridad/comportamiento.
- **`ollama_client.py`**: Cliente de comunicación HTTP que consume directamente el endpoint oficial de Ollama (`/api/chat`). No requiere bibliotecas complejas externas, permitiéndote ver cómo se estructuran las peticiones JSON crudas.
- **`chatbot.py`**: El cerebro del agente. Contiene el control del ciclo Self-Refine y el parser robusto que analiza el feedback del supervisor en formato estructurado (o JSON) e implementa fallbacks por si el modelo genera texto no estructurado.
- **`cli.py`**: Aplicación interactiva de consola para chatear con el bot. Por defecto muestra los logs de depuración del ciclo `[DEBUG]`, donde puedes ver qué borrador se hizo, qué críticas recibió y el resultado final.
- **`tests/conftest.py`**: Fixtures compartidas para `pytest` y validadores que detectan automáticamente si la instancia local de Ollama está encendida.
- **`tests/test_chatbot.py`**: Pruebas automáticas. Cubre tanto pruebas con **Mocks** (para comprobar que la máquina de estados y las iteraciones del ciclo Self-Refine funcionen al 100% sin depender de que Ollama esté activo) como pruebas de integración **en vivo** (evaluando FAQs, respuestas fuera de alcance e inyecciones de prompt).

---

## 🚀 Cómo Comenzar a Utilizarlo

### 1. Requisitos Previos

- Tener instalado **Python 3.8 o superior**.
- Tener instalado **Ollama**. Puedes descargarlo gratis desde [ollama.com](https://ollama.com).
- Haber descargado el modelo correspondiente (en este entorno se utiliza `gemma4:latest`):
  ```bash
  ollama pull gemma4:latest
  ```

### 2. Instalación de Dependencias

Instala las bibliotecas requeridas desde la raíz del proyecto:
```bash
pip install -r requirements.txt
```

### 3. Ejecución del Chatbot

Inicia el chat interactivo en tu terminal:
```bash
python cli.py
```
*Tip: Para chatear de forma normal ocultando el ciclo interno de depuración, puedes ejecutar:*
```bash
python cli.py --no-debug
```

### 4. Ejecución de Pruebas Automatizadas

Verifica que el chatbot cumpla con las directivas de seguridad y coherencia:
```bash
python -m pytest -v
```
> **Nota Didáctica**: Si Ollama no está activo al correr los tests, las pruebas de integración en vivo se omitirán automáticamente de forma segura (`skipped`), ejecutándose únicamente las pruebas unitarias basadas en Mocks, que comprueban la arquitectura lógica en milisegundos.

---

## 💡 Conceptos Educativos Clave que Aprenderás

1. **Ajuste de Temperaturas**: Comprenderás cómo diferentes tareas (redactar vs. auditar) requieren parámetros de creatividad opuestos para un desempeño ideal.
2. **Robustez ante el formato del LLM**: Verás cómo el parser maneja casos en los que el modelo no responde en un JSON perfecto, aplicando expresiones regulares como alternativa (fallback).
3. **Mocks de LLMs en Pruebas**: Aprenderás a simular llamadas a APIs generativas en tus entornos de pruebas para poder certificar la lógica de tus aplicaciones de forma instantánea y económica.
4. **Respuestas de Seguridad (Fallback Guardrails)**: Implementación de respuestas seguras por defecto cuando los agentes no consiguen auto-corregirse tras un número determinado de iteraciones.
