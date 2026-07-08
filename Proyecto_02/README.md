# 🛡️ Agente de Cumplimiento Legal y de Privacidad (Compliance Agent)

Este repositorio contiene la implementación de un **Agente de Cumplimiento Legal y de Privacidad** desarrollado con fines **educativos**. Su principal objetivo es demostrar los principios de **Privacy by Design** (Privacidad desde el Diseño) y la implementación de un framework de **Evaluaciones (Evals)** robusto para auditorías de seguridad en agentes de Inteligencia Artificial.

El agente analiza documentos corporativos o legales (contratos, correos, avisos de privacidad) para identificar Datos Personales Sensibles y generar reportes de riesgos legales fundamentados en leyes mexicanas, garantizando que ningún dato confidencial sea transferido a APIs comerciales externas de LLMs.

---

## 🚀 Características Clave

1.  **Anonimización en Tiempo Real (Privacy by Design):**
    *   Una capa proxy local analiza el texto y enmascara automáticamente datos de identificación (PII) como nombres, CURP, RFC, teléfonos, correos y direcciones.
    *   El LLM comercial externo solo recibe placeholders (ej. `[NOMBRE_1]`), lo que elimina el riesgo de fuga de datos en tránsito o almacenamiento por terceros.
    *   Reconstruye de forma local y segura el reporte final (des-anonimización) para lectura del usuario final.
2.  **Base de Conocimiento RAG Cifrada (AES-256-GCM):**
    *   Almacena las leyes en una base de datos vectorial local protegida con cifrado simétrico autenticado AES-GCM.
    *   Descifra los artículos en la memoria RAM volátil solo durante la ejecución para realizar búsquedas de similitud con `numpy`.
    *   Contiene fragmentos clave de la **LFPDPPP** (Sector Privado) y la **LGPDPPSO** (Sector Público) de México.
3.  **Derechos ARCO (Derecho de Cancelación / "Al Olvido"):**
    *   Una función específica purga de inmediato los mapeos locales de sesión.
    *   Realiza un borrado físico y definitivo de los vectores de embeddings asociados al titular de la base de datos, evitando que permanezcan latentes en los índices de búsqueda.
4.  **Razonamiento CoT (Chain of Thought):**
    *   El agente desglosa de manera transparente sus pasos cognitivos: *Percepción* (detección de PII) ➔ *Anonimización* (enmascarado) ➔ *RAG/Razonamiento* (búsqueda cifrada de leyes) ➔ *Respuesta* (evaluación de riesgos).
5.  **Supervisión Humana (Human-in-the-Loop):**
    *   Un logger de escalación monitorea si el usuario presenta inconformidades (Derecho de Oposición) o si se evalúan datos biométricos de alto riesgo, redirigiendo el caso a un canal de revisión humana.
6.  **Suite de Evaluaciones Avanzadas (Evals):**
    *   **Red Teaming (Prompt Injection):** Pruebas adversariales que intentan manipular al LLM para revelar datos confidenciales.
    *   **Detección de Sesgos (Bias):** Garantiza que la evaluación legal sea idéntica e imparcial sin importar el nombre o perfil demográfico del titular.
    *   **Grounding RAG:** Verifica que el análisis de riesgos del agente esté 100% fundamentado en los artículos de ley recuperados.

---

## 📂 Estructura del Proyecto

```text
├── .env                       # Configuración local de API Key (ignorado en git)
├── .gitignore                 # Exclusión de archivos compilados, logs y secretos
├── config.py                  # Configuraciones generales, rutas y constantes del modelo
├── gemini_client.py           # Cliente para interactuar con la API REST de Gemini (requests)
├── anonymizer.py              # Detección local de PII, enmascaramiento y des-anonimización
├── knowledge_base.py          # Vector Store local cifrado con AES-GCM
├── populate_kb.py             # Script de inicialización, embedding y cifrado de leyes
├── compliance_agent.py        # Núcleo del Agente Compliance con razonamiento CoT
├── arco_tool.py               # Herramienta para Derechos ARCO (Derecho al Olvido)
├── logger_escalation.py       # Sistema de logs y alertas para escalación humana
├── run_agent.py               # Interfaz interactiva de consola (CLI)
├── app.py                     # Interfaz web interactiva moderna en Streamlit
├── eval_suite.py              # Framework de pruebas de Red Teaming, Sesgo y Grounding
├── data/                      # Almacenamiento local del proyecto
│   ├── raw_laws/              # Archivos de texto plano de leyes mexicanas (grounding)
│   └── test_documents/        # Archivos de prueba (contratos, correos, inyecciones)
├── tests/                     # Carpeta de pruebas unitarias
│   ├── test_anonymizer.py     # Pruebas para enmascaramiento de datos personales
│   └── test_kb.py             # Pruebas de cifrado y cálculo vectorial
└── README.md                  # Este archivo de documentación
```

---

## 🛠️ Instalación y Configuración

### 1. Requisitos del Sistema
Se requiere un entorno de Python (versión 3.10 o superior recomendada). Si utilizas Anaconda:
```bash
conda activate evals_actumlogos
```

### 2. Instalar Dependencias
Instala las librerías necesarias ejecutando:
```bash
pip install streamlit numpy cryptography requests python-dotenv pytest
```

### 3. Configurar API Key
Crea un archivo `.env` en la raíz del proyecto y agrega tu clave de acceso a la API de Google Gemini (AI Studio):
```text
GEMINI_API_KEY=tu_clave_de_api_de_gemini
```

---

## 💻 Instrucciones de Ejecución

### A. Ejecutar Interfaz Web Interactiva (Recomendado)
Para explorar de manera visual el flujo del agente, la comparativa de anonimización y las métricas de evals:
```bash
python -m streamlit run app.py
```
Abre en tu navegador la dirección indicada (usualmente `http://localhost:8501`).
> 💡 **Nota:** La primera vez que abras la aplicación, haz clic en **"Inicializar Base RAG Cifrada"** en el panel lateral izquierdo para indexar y encriptar las leyes.

### B. Ejecutar Consola Interactiva (CLI)
Si prefieres interactuar con el agente en terminal:
```bash
python run_agent.py
```

### C. Ejecutar Suite de Evaluaciones (Evals)
Para correr las pruebas de robustez contra inyecciones y sesgos:
```bash
python eval_suite.py
```

### D. Ejecutar Pruebas Unitarias
Para validar que todos los módulos locales funcionen correctamente:
```bash
python -m pytest tests/
```

---

## 🎓 Propósito Educativo

Este repositorio fue construido como material didáctico para ilustrar la implementación de **patrones de seguridad y auditoría en IA**. Muestra de forma práctica:
*   Cómo prevenir fugas de datos confidenciales sin sacrificar el uso de LLMs en la nube.
*   El diseño de métricas de calidad y robustez frente a ataques de inyección de prompts adversariales.
*   La forma de estructurar bases de conocimiento RAG cifradas respetando los derechos de privacidad de los usuarios.
