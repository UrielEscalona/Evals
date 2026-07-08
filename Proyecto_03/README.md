# DeepEval RAG Academy 🎓

Este repositorio contiene una **Guía e Instructivo Interactivo** desarrollado en Python y Streamlit para aprender y dominar **DeepEval**, el framework de evaluación para aplicaciones de Large Language Models (LLM), enfocado en sistemas RAG (Retrieval-Augmented Generation) empresariales.

La aplicación utiliza a **Gemini** como "LLM Judge" (evaluador inteligente) a través de la clave de API de Google AI Studio, permitiendo visualizar los veredictos y razonamientos de evaluación en tiempo real.

---

## 🚀 Características Clave

1. **📘 Fundamentos Educativos**: Explicación teórica de la tríada RAG y el funcionamiento del enfoque *LLM-as-a-Judge*.
2. **🧪 Simulador de Escenarios RAG**: Sandbox interactivo con casos preconfigurados que demuestran respuestas perfectas, alucinaciones de datos y respuestas desviadas/irrelevantes para observar cómo reacciona cada métrica de DeepEval.
3. **🔍 Evaluación de Métricas Core**:
   - **Fidelidad (Faithfulness)**: Comprobación de que la respuesta del LLM se base únicamente en el contexto recuperado (detector de alucinaciones).
   - **Relevancia de la Respuesta (Answer Relevancy)**: Validación de que la respuesta resuelva directamente la consulta inicial del usuario.
   - **Relevancia del Contexto (Contextual Relevancy)**: Medición de la calidad y la ausencia de ruido en los fragmentos de texto recuperados por el buscador.
4. **🧬 Sintetizador de Datos de Prueba (Synthesizer)**: Módulo interactivo que permite ingresar documentos corporativos y generar automáticamente casos de prueba sintéticos (`Goldens` con inputs, contextos y outputs esperados), exportables en formato CSV.
5. **💻 Cheat Sheet de Integración**: Guía de código Python lista para copiar y pegar en scripts de prueba locales o pipelines de integración continua (CI/CD) usando `pytest`.

---

## 📁 Estructura del Proyecto

* **[app.py](app.py)**: Archivo principal de la aplicación Streamlit con el tablero visual, explicaciones y la lógica de la interfaz de usuario.
* **[eval_utils.py](eval_utils.py)**: Adaptador de DeepEval que interactúa con la API de Gemini mediante `GeminiModel`. Encapsula la medición de métricas y la ejecución del generador sintético.
* **[rag_system.py](rag_system.py)**: Simula un sistema RAG corporativo con una base de conocimiento interna (empresa ficticia *ActumLogos*) y un motor de recuperación simple basado en coincidencia de términos.
* **[test_env.py](test_env.py)**: Script básico de consola para verificar rápidamente las credenciales de conexión con Gemini y la validez de DeepEval.
* **[requirements.txt](requirements.txt)**: Archivo con los paquetes y dependencias necesarias.
* **[.gitignore](.gitignore)**: Exclusiones de Git para evitar subir archivos de entorno locales (`.env`), cachés y archivos de compilación temporal.

---

## 🛠️ Instalación y Configuración

Sigue estos pasos para ejecutar el proyecto de forma local:

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd Proyecto_03
```

### 2. Configurar el Entorno de Anaconda
Si estás usando el ambiente de Conda preestablecido `evals_actumlogos`, actívalo:
```bash
conda activate evals_actumlogos
```
De lo contrario, puedes crear uno nuevo con Python 3.10 o superior:
```bash
conda create -n deepeval_env python=3.10
conda activate deepeval_env
```

### 3. Instalar las dependencias
Instala los paquetes necesarios definidos en `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno
Copia el archivo de plantilla `.env.example` y renómbralo a `.env`:
```bash
cp .env.example .env
```
Abre el archivo `.env` en tu editor de texto y coloca tu clave de API de **Google AI Studio** en el campo correspondiente:
```env
GEMINI_API_KEY="Tu_Clave_De_API_De_Google_AI_Studio_Aqui"
```

---

## 🚦 Verificación y Ejecución

### Paso A: Validar la conexión con Gemini
Antes de iniciar la web app, ejecuta el script de consola para confirmar que la API Key es válida y que DeepEval puede generar evaluaciones:
```bash
python test_env.py
```
Si todo es correcto, la consola mostrará la inicialización exitosa de `GeminiModel`, computará una prueba básica de relevancia y devolverá un puntaje `Score: 1.0` con la justificación del modelo.

### Paso B: Iniciar la interfaz interactiva Streamlit
Una vez verificado el entorno, corre el servidor de Streamlit:
```bash
streamlit run app.py
```

Abre tu navegador en la URL indicada por la consola (usualmente **[http://localhost:8501](http://localhost:8501)**) y comienza a aprender DeepEval.
