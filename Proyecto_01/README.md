# Agente de Clasificación Multimodal con LLM Local y Evals

Este proyecto implementa un agente inteligente en Python para la clasificación de datos no estructurados (comentarios, logs de error) y el análisis visual de documentos (facturas, tickets de compra y logotipos) utilizando un modelo de lenguaje multimodal local a través de la API de **Ollama**.

Está optimizado para ejecutarse localmente, garantizando total privacidad y seguridad de los datos.

---

## 🚀 Características Clave

- **Análisis de Texto y Visión Multimodal**: Clasificación de textos y análisis de imágenes usando el modelo **Qwen3-VL-4B** (o equivalentes multimodales como `qwen2.5-vl:3b` o `qwen-vl`).
- **Parser Robustecido (`_parse_robust`)**: Mapeo inteligente y tolerancia ante variaciones en las llaves del JSON devuelto por el LLM (por ejemplo, diferencias de mayúsculas/minúsculas o acentos) y traducción de confianzas cualitativas (como "high", "alta", "medium") a valores decimales numéricos precisos.
- **Generador de Datos Sintéticos**: Script programático (`generate_mock_data.py`) que dibuja de forma interactiva imágenes de prueba realistas (una factura corporativa formal, un ticket de supermercado y un logo geométrico minimalista) mediante **Pillow**.
- **Suite de Pruebas con Pytest**: Cobertura de pruebas unitarias (con mocks de `requests.post`) y de integración real que validan el comportamiento ante fallos de conexión, respuestas incorrectas del modelo y análisis multimodal real.
- **Logs Detallados**: Sistema de registro unificado en consola y archivo local `agent.log` que monitoriza solicitudes, latencia de la API local y errores del sistema.
- **Compatibilidad Multiplataforma**: Diseñado con salidas estándar de consola en ASCII para evitar fallos de codificación en terminales Windows (CMD/PowerShell).

---

## 📂 Estructura del Proyecto

```text
Proyecto_01/
│
├── .env.example               # Plantilla de configuración de variables de entorno
├── .gitignore                 # Configuración de exclusiones para Git
├── requirements.txt           # Dependencias del proyecto
├── logger_config.py           # Configuración del logging centralizado
├── agent.py                   # Lógica principal del Agente Clasificador
├── generate_mock_data.py      # Generador de imágenes mock y dataset de pruebas
├── main.py                    # Script demostrativo interactivo en consola
├── prueba_imagen.py           # Ejemplo práctico para clasificar imágenes personalizadas
│
└── tests/                     # Suite de pruebas automatizadas
    ├── conftest.py            # Configuración y fixtures globales de pytest
    └── test_agent.py          # Pruebas unitarias e integración con Ollama
```

---

## 🛠️ Requisitos Previos

1. **Python 3.10+** (Se recomienda usar un gestor de entornos como **Conda**).
2. **Ollama** instalado y ejecutándose localmente.
3. Descargar el modelo multimodal en Ollama:
   ```bash
   ollama pull qwen3-vl:4b
   ```

---

## 🔧 Instalación y Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/nombre-del-repositorio.git
   cd nombre-del-repositorio
   ```

2. **Crear y activar el entorno virtual (Conda)**:
   ```bash
   conda create -n evals_actumlogos python=3.10 -y
   conda activate evals_actumlogos
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variables de Entorno**:
   Copia el archivo `.env.example` y renombralo a `.env`:
   ```bash
   copy .env.example .env   # En Windows
   cp .env.example .env     # En Linux/macOS
   ```
   Ajusta las variables de entorno en el archivo `.env` según sea necesario (por defecto apunta a `http://localhost:11434/api/chat` y al modelo `qwen3-vl:4b`).

---

## 💻 Uso del Proyecto

### 1. Ejecutar la Demostración Completa
Este script genera automáticamente las imágenes mock necesarias si no existen y realiza la clasificación en tiempo real:
```bash
python main.py
```
*Nota: Si Ollama no está activo o no tienes el modelo instalado, el script entrará automáticamente en modo **Dry-run simulado (MOCK)** para que puedas ver el comportamiento.*

### 2. Probar con una Imagen Propia
Puedes clasificar y describir cualquier imagen local usando el script de ejemplo `prueba_imagen.py`. Coloca tu archivo en el directorio correspondiente y ejecuta:
```bash
python prueba_imagen.py
```

### 3. Ejecutar Pruebas Automatizadas
Para correr la suite de pruebas locales e integración:
```bash
pytest -v
```

---

## 🧪 Pruebas y Validación (Evals)

El proyecto utiliza `pytest` para certificar la confiabilidad y calidad del código. Las pruebas evalúan:
- Clasificación de texto simulada (con mocks de red).
- Clasificación de imagen simulada (con mocks de codificación base64).
- Manejo robusto de errores HTTP (códigos 500, etc.).
- Comportamiento seguro ante la caída de conexión de la API local.
- Pruebas reales de visión e integración en tiempo real contra Ollama (saltadas automáticamente si Ollama no está activo en la máquina de pruebas).
