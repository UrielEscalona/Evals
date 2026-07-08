import streamlit as st
import pandas as pd
import os
import dotenv

# Intentar importar modulos locales
try:
    import rag_system
    import eval_utils
    LOCAL_IMPORTS = True
except ImportError:
    LOCAL_IMPORTS = False

# Cargar variables de entorno para depuración
dotenv.load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="DeepEval Academy - RAG & Sintetizador",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una estética Premium y Moderna
st.markdown("""
<style>
    /* Estilos globales y paleta de colores */
    .main {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    
    /* Tarjetas de Métricas */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 25px;
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        flex: 1;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    .metric-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    
    .metric-score {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #ffffff;
    }
    
    /* Insignias de Estado */
    .badge {
        padding: 6px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-fail {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Tarjetas de Base de Conocimiento */
    .kb-card {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #6366f1;
        border-radius: 4px 8px 8px 4px;
        padding: 16px;
        margin-bottom: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .kb-title {
        font-weight: 600;
        font-size: 1rem;
        color: #f1f5f9;
        margin-bottom: 4px;
    }
    
    .kb-category {
        font-size: 0.75rem;
        color: #818cf8;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .kb-content {
        font-size: 0.9rem;
        color: #cbd5e1;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Título de la Aplicación y Encabezado principal
st.title("🎓 DeepEval Academy")
st.subheader("Plataforma Interactiva para Evaluar RAG Empresarial y Sintetizar Datos con LLM Judges")
st.markdown("---")

# Verificar si los módulos locales están listos
if not LOCAL_IMPORTS:
    st.error("⚠️ Error: No se pudieron cargar los módulos `rag_system.py` o `eval_utils.py`. Asegúrate de que estén en el mismo directorio.")
    st.stop()

# Configuración del menú lateral (Sidebar)
with st.sidebar:
    st.header("⚙️ Configuración del Tutor")
    
    model_name = st.selectbox(
        "Modelo de LLM Judge:",
        ["gemini-3.1-flash-lite", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0,
        help="El modelo de Gemini que actuará como evaluador (LLM Judge)."
    )
    
    threshold = st.slider(
        "Umbral de Aprobación (Threshold):",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Puntaje mínimo requerido para que una métrica sea calificada como exitosa (Passed)."
    )
    
    st.markdown("---")
    st.header("🗂️ Base de Conocimiento")
    st.caption("Documentos internos de la empresa ficticia **ActumLogos** sobre los cuales opera nuestro RAG.")
    
    for doc in rag_system.KNOWLEDGE_BASE:
        st.markdown(f"""
        <div class="kb-card">
            <div class="kb-category">{doc['category']}</div>
            <div class="kb-title">{doc['title']}</div>
            <div class="kb-content">{doc['content']}</div>
        </div>
        """, unsafe_allow_html=True)

# Crear las pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "📘 Fundamentos de DeepEval",
    "🧪 Simulador y Evaluación RAG",
    "🧬 Generador de Datos Sintéticos",
    "💻 Cheat Sheet de Código"
])

# ==========================================
# PESTAÑA 1: FUNDAMENTOS
# ==========================================
with tab1:
    st.header("📘 Fundamentos de la Evaluación RAG")
    st.markdown("""
    En los sistemas **RAG (Retrieval-Augmented Generation)**, un LLM responde preguntas del usuario basándose en información recuperada de una base de conocimiento interna. 
    A diferencia del software tradicional, evaluar un RAG es sumamente difícil debido a la variabilidad de las respuestas de lenguaje natural. Aquí es donde entra **DeepEval**.
    
    ### La Tríada RAG y sus Métricas Clave
    Para evaluar un sistema RAG de forma holística, DeepEval propone evaluar tres relaciones fundamentales:
    """)
    
    # Diagrama Mermaid interactivo
    st.markdown("""
    ```mermaid
    graph TD
        Q[Pregunta / Input] -- 1. Relevancia del Contexto --> C[Contexto Recuperado / Retrieval Context]
        C -- 2. Fidelidad <br> (Evita Alucinaciones) --> A[Respuesta Generada / Actual Output]
        Q -- 3. Relevancia de la Respuesta --> A
        
        style Q fill:#1e293b,stroke:#64748b,stroke-width:2px,color:#fff
        style C fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
        style A fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff
    ```
    """)
    
    st.markdown("""
    1. **Fidelidad (Faithfulness)**: Evalúa si la respuesta generada (`Actual Output`) se basa **únicamente** en el contexto recuperado (`Retrieval Context`). Identifica si el modelo está alucinando o inventando datos no documentados.
    2. **Relevancia de la Respuesta (Answer Relevancy)**: Evalúa qué tan bien se alinea la respuesta con la consulta del usuario (`Input`). Ayuda a detectar si el modelo responde con rodeos, da respuestas vacías o evade el tema.
    3. **Relevancia del Contexto (Contextual Relevancy)**: Evalúa si el recuperador (Retriever) está trayendo información útil y relevante para la pregunta, filtrando ruido o información irrelevante.
    
    ### ¿Cómo funciona el LLM-as-a-Judge?
    DeepEval utiliza modelos avanzados (como **Gemini**) configurados con prompts específicos de evaluación para actuar como "jueces". 
    Por ejemplo, para evaluar la **Fidelidad**, el LLM Judge realiza los siguientes pasos de manera automatizada:
    1. **Extrae todos los enunciados / afirmaciones (Claims)** de la respuesta del usuario.
    2. **Verifica de forma lógica si cada una de estas afirmaciones** puede deducirse directamente del contexto recuperado.
    3. **Calcula el puntaje**: `Puntaje = (Afirmaciones respaldadas) / (Total de afirmaciones)`.
    4. **Genera una justificación textual** explicando por qué ciertos puntos fallaron la evaluación.
    """)

# ==========================================
# PESTAÑA 2: SIMULADOR Y EVALUACIÓN
# ==========================================
with tab2:
    st.header("🧪 Simulador de Escenarios RAG e Interfaz de Evaluación")
    st.markdown("""
    Prueba cómo funcionan los jueces de DeepEval. Puedes seleccionar un escenario educativo preconfigurado (para ver cómo reaccionan las métricas ante respuestas correctas o incorrectas) o realizar una prueba interactiva libre.
    """)
    
    # Inicializar estados de sesión si no existen
    if 'eval_query' not in st.session_state:
        st.session_state.eval_query = "¿Qué requisitos tiene la contraseña corporativa y cada cuánto se cambia?"
    if 'eval_contexts' not in st.session_state:
        st.session_state.eval_contexts = "En ActumLogos, todas las contraseñas corporativas deben tener un mínimo de 14 caracteres. Deben incluir al menos una letra mayúscula, una minúscula, un número y un carácter especial (ej. !, @, #). Las contraseñas deben ser actualizadas obligatoriamente cada 90 días."
    if 'eval_output' not in st.session_state:
        st.session_state.eval_output = "En ActumLogos, las contraseñas corporativas deben tener al menos 14 caracteres (incluyendo mayúsculas, minúsculas, números y caracteres especiales) y deben cambiarse obligatoriamente cada 90 días."
    if 'eval_results' not in st.session_state:
        st.session_state.eval_results = None
        
    # Selección de Escenario
    escenario = st.radio(
        "Selecciona un Escenario de Prueba:",
        [
            "Caso 1: RAG Perfecto (Alta Fidelidad, Alta Relevancia)",
            "Caso 2: Alucinación de Datos (Baja Fidelidad - Contradice o agrega datos falsos)",
            "Caso 3: Respuesta Desviada (Baja Relevancia de Respuesta - Divaga del tema)",
            "Caso 4: Consulta Libre / RAG Interactivo"
        ],
        index=0
    )
    
    # Configuración de variables según escenario elegido
    if escenario.startswith("Caso 1"):
        st.session_state.eval_query = "¿Qué requisitos tiene la contraseña corporativa y cada cuánto se cambia?"
        st.session_state.eval_contexts = "En ActumLogos, todas las contraseñas corporativas deben tener un mínimo de 14 caracteres. Deben incluir al menos una letra mayúscula, una minúscula, un número y un carácter especial (ej. !, @, #). Las contraseñas deben ser actualizadas obligatoriamente cada 90 días. Está estrictamente prohibido compartir contraseñas por canales de mensajería."
        st.session_state.eval_output = "En ActumLogos, las contraseñas corporativas deben tener al menos 14 caracteres (incluyendo mayúsculas, minúsculas, números y caracteres especiales) y deben cambiarse obligatoriamente cada 90 días. Además, está prohibido compartirlas por Slack o Teams."
        
    elif escenario.startswith("Caso 2"):
        st.session_state.eval_query = "¿Cómo accedo remotamente a la red corporativa y qué VPN uso?"
        st.session_state.eval_contexts = "Para acceder a los servidores internos y herramientas de desarrollo desde fuera de la oficina, los empleados deben utilizar la VPN corporativa 'FortiActum'. El acceso requiere autenticación de dos factores (2FA) configurada en la aplicación 'Google Authenticator'. Queda prohibido conectarse a la VPN desde redes Wi-Fi públicas abiertas sin activar el cifrado adicional."
        st.session_state.eval_output = "Para conectarte de manera remota a los servidores internos, debes descargar la VPN 'SuperConnect' e iniciar sesión con tu cuenta normal. No necesitas autenticación de dos factores (2FA), ya que la seguridad se gestiona a través de la IP pública de tu hogar de forma transparente."
        
    elif escenario.startswith("Caso 3"):
        st.session_state.eval_query = "¿Cuál es el límite de viáticos diarios para comidas en viajes de negocio?"
        st.session_state.eval_contexts = "Los gastos relacionados con viajes de negocios deben registrarse en la plataforma 'ActumExp' dentro de los 15 días posteriores al término del viaje. Los viáticos diarios para comidas están limitados a un máximo de $50 USD por día, y se requiere cargar facturas digitales válidas para cualquier gasto superior a $10 USD."
        st.session_state.eval_output = "Los modelos de lenguaje y la inteligencia artificial están redefiniendo el futuro del trabajo corporativo. Herramientas como ChatGPT y Gemini permiten a los empleados redactar correos, resumir reportes y programar más rápido, mejorando la productividad global en un 40%."

    # Interfaz para consulta libre
    if escenario.startswith("Caso 4"):
        st.markdown("#### 🛠️ Configura tu consulta RAG Interactiva")
        col_c1, col_c2 = st.columns([3, 2])
        
        with col_c1:
            custom_query = st.text_input("Ingresa tu pregunta empresarial:", value="¿Qué pasa si subo código a mi Github personal?")
        with col_c2:
            generation_type = st.selectbox(
                "Tipo de respuesta a generar con Gemini:",
                [
                    "Respuesta Perfecta (Basada 100% en políticas)",
                    "Respuesta Alucinada (Con datos inventados o erróneos)",
                    "Respuesta Irrelevante (Divagar sobre informática/IA)"
                ]
            )
            
        if st.button("🔍 Recuperar Contexto y Generar Respuesta RAG"):
            with st.spinner("Buscando en base de conocimientos y generando respuesta con Gemini..."):
                # Recuperar contexto
                retrieved_docs = rag_system.retrieve_context(custom_query, top_k=2)
                context_texts = [doc["content"] for doc in retrieved_docs]
                joined_context = "\n\n".join(context_texts)
                
                # Generar respuesta según la opción elegida
                if "Perfecta" in generation_type:
                    output_text = rag_system.generate_answer_perfect(custom_query, retrieved_docs)
                elif "Alucinada" in generation_type:
                    output_text = rag_system.generate_answer_hallucinated(custom_query, retrieved_docs)
                else:
                    output_text = rag_system.generate_answer_irrelevant(custom_query, retrieved_docs)
                
                # Guardar en variables
                st.session_state.eval_query = custom_query
                st.session_state.eval_contexts = joined_context
                st.session_state.eval_output = output_text
                st.success("¡Respuesta RAG Generada!")

    # Área de revisión de datos antes de evaluar
    st.markdown("### 📋 Datos a evaluar")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Pregunta del Usuario (Input):", value=st.session_state.eval_query, disabled=True)
        st.text_area("Contexto de Referencia Recuperado (Retrieval Context):", value=st.session_state.eval_contexts, height=180, disabled=True)
    with col2:
        st.text_area("Respuesta Generada por el RAG (Actual Output):", value=st.session_state.eval_output, height=252, disabled=True)

    # Botón para ejecutar la evaluación
    if st.button("🔍 Iniciar Evaluación con DeepEval (Gemini LLM Judge)", type="primary"):
        with st.spinner("Ejecutando métricas de DeepEval a través de Gemini (esto puede tomar unos segundos)..."):
            # Preparar contextos en formato lista
            ctx_list = [st.session_state.eval_contexts]
            
            results = eval_utils.evaluate_rag(
                query=st.session_state.eval_query,
                response=st.session_state.eval_output,
                contexts=ctx_list,
                threshold=threshold
            )
            st.session_state.eval_results = results

    # Mostrar Resultados de Evaluación
    if st.session_state.eval_results:
        results = st.session_state.eval_results
        
        if not results["success"]:
            st.error(f"Ocurrió un error al ejecutar la evaluación: {results['error']}")
        else:
            st.markdown("### 📊 Tablero de Resultados")
            metrics = results["metrics"]
            
            # Estructurar la visualización en 3 columnas
            col_f, col_ar, col_cr = st.columns(3)
            
            # 1. FIDELIDAD (Faithfulness)
            with col_f:
                f_data = metrics["faithfulness"]
                status_badge = '<span class="badge badge-success">Passed</span>' if f_data["success"] else '<span class="badge badge-fail">Failed</span>'
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span class="metric-title">🛡️ Fidelidad</span>
                        {status_badge}
                    </div>
                    <div class="metric-score">{f_data['score']:.2f}</div>
                    <p style="font-size:0.85rem; color:#94a3b8;">Umbral: {threshold}</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(f_data['score'])
                
            # 2. RELEVANCIA DE RESPUESTA (Answer Relevancy)
            with col_ar:
                ar_data = metrics["answer_relevancy"]
                status_badge = '<span class="badge badge-success">Passed</span>' if ar_data["success"] else '<span class="badge badge-fail">Failed</span>'
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span class="metric-title">💬 Relevancia Respuesta</span>
                        {status_badge}
                    </div>
                    <div class="metric-score">{ar_data['score']:.2f}</div>
                    <p style="font-size:0.85rem; color:#94a3b8;">Umbral: {threshold}</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(ar_data['score'])
                
            # 3. RELEVANCIA DE CONTEXTO (Contextual Relevancy)
            with col_cr:
                cr_data = metrics["context_relevancy"]
                status_badge = '<span class="badge badge-success">Passed</span>' if cr_data["success"] else '<span class="badge badge-fail">Failed</span>'
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <span class="metric-title">🔍 Relevancia Contexto</span>
                        {status_badge}
                    </div>
                    <div class="metric-score">{cr_data['score']:.2f}</div>
                    <p style="font-size:0.85rem; color:#94a3b8;">Umbral: {threshold}</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(cr_data['score'])
            
            st.markdown("---")
            st.markdown("### 🔬 Justificaciones del LLM Judge (Razonamientos)")
            
            with st.expander("Detalles de Fidelidad (Faithfulness)", expanded=True):
                st.markdown(f"**Puntaje:** `{metrics['faithfulness']['score']:.2f}`")
                st.markdown(f"**Análisis explicativo:**\n{metrics['faithfulness']['reason']}")
                
            with st.expander("Detalles de Relevancia de Respuesta (Answer Relevancy)", expanded=False):
                st.markdown(f"**Puntaje:** `{metrics['answer_relevancy']['score']:.2f}`")
                st.markdown(f"**Análisis explicativo:**\n{metrics['answer_relevancy']['reason']}")
                
            with st.expander("Detalles de Relevancia de Contexto (Contextual Relevancy)", expanded=False):
                st.markdown(f"**Puntaje:** `{metrics['context_relevancy']['score']:.2f}`")
                st.markdown(f"**Análisis explicativo:**\n{metrics['context_relevancy']['reason']}")

# ==========================================
# PESTAÑA 3: SINTETIZADOR
# ==========================================
with tab3:
    st.header("🧬 Generación Automática de Datos Sintéticos")
    st.markdown("""
    Para evaluar un RAG de forma robusta, necesitas decenas o cientos de casos de prueba (`Goldens`). 
    Crear esto manualmente consume mucho tiempo. El modulo **Synthesizer** de DeepEval analiza un corpus de documentos corporativos y, 
    usando técnicas de IA basadas en el contexto (evoluciones de complejidad de prompts), genera preguntas realistas y sus respuestas correctas esperadas.
    """)
    
    st.markdown("#### Paso 1: Selecciona los contextos fuente de la Base de Conocimiento")
    selected_contexts = []
    for doc in rag_system.KNOWLEDGE_BASE:
        # Checkbox por cada documento
        if st.checkbox(f"Documento: {doc['title']} ({doc['category']})", value=True, key=f"syn_check_{doc['id']}"):
            selected_contexts.append(doc["content"])
            
    st.markdown("#### Paso 2: Configuración del Sintetizador")
    goldens_per_context = st.slider(
        "Número de preguntas a generar por cada documento seleccionado:",
        min_value=1,
        max_value=2,
        value=1,
        help="Para evitar sobrecargar los límites de la API de Gemini, sugerimos mantenerlo en 1 por documento."
    )
    
    if st.button("✨ Generar Casos de Prueba (Goldens)", type="primary"):
        if not selected_contexts:
            st.warning("Selecciona al menos un documento para servir de base.")
        else:
            with st.spinner("DeepEval Synthesizer está analizando los documentos y generando preguntas/respuestas..."):
                # Ejecutar el sintetizador desde el utilitario
                syn_results = eval_utils.generate_synthetic_goldens(
                    contexts=selected_contexts,
                    max_goldens_per_context=goldens_per_context
                )
                
                if not syn_results["success"]:
                    st.error(f"Error al generar datos sintéticos: {syn_results['error']}")
                else:
                    goldens = syn_results["goldens"]
                    st.success(f"¡Casos generados con éxito! Total de Goldens: {len(goldens)}")
                    
                    # Convertir a DataFrame para visualización
                    df_goldens = pd.DataFrame(goldens)
                    
                    # Renombrar columnas para claridad
                    df_goldens.columns = ["Pregunta Sintética (Input)", "Respuesta Esperada (Expected Output)", "Contexto de Origen"]
                    
                    # Mostrar tabla
                    st.dataframe(df_goldens, use_container_width=True)
                    
                    # Botón para descargar como CSV
                    csv = df_goldens.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Dataset en CSV",
                        data=csv,
                        file_name="deepeval_dataset_sintetico.csv",
                        mime="text/csv"
                    )

# ==========================================
# PESTAÑA 4: CHEAT SHEET / CÓDIGO
# ==========================================
with tab4:
    st.header("💻 Código de Integración para tu IDE")
    st.markdown("""
    Una vez que comprendes las métricas a través de este tutor interactivo, el siguiente paso es implementarlo en tus flujos de CI/CD o scripts de prueba locales. 
    Aquí tienes los fragmentos de código listos para producción para integrar **DeepEval** con **Gemini**.
    """)
    
    st.subheader("1. Configuración de Variables de Entorno")
    st.markdown("Crea un archivo `.env` en la raíz de tu proyecto:")
    st.code("""
# Configuración del archivo .env
GEMINI_API_KEY="Tu_Google_API_Key_Aqui"
    """, language="properties")
    
    st.subheader("2. Script de Evaluación Local")
    st.markdown("Ejecuta la evaluación de una respuesta individual desde Python:")
    st.code("""
import os
from dotenv import load_dotenv
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

# Cargar API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 1. Configurar el modelo Gemini como evaluador
eval_model = GeminiModel(
    model="gemini-3.1-flash-lite",
    api_key=api_key
)

# 2. Definir el caso de prueba (triada de RAG)
test_case = LLMTestCase(
    input="¿Cómo accedo remotamente a la red corporativa?",
    actual_output="Debes conectarte usando la VPN corporativa FortiActum y autenticación de dos factores (2FA).",
    retrieval_context=["Para acceder desde fuera de la oficina, los empleados deben usar la VPN 'FortiActum' con 2FA."]
)

# 3. Inicializar las métricas con el modelo Gemini
faithfulness_metric = FaithfulnessMetric(threshold=0.5, model=eval_model)
relevancy_metric = AnswerRelevancyMetric(threshold=0.5, model=eval_model)

# 4. Medir
faithfulness_metric.measure(test_case)
print(f"Fidelidad: {faithfulness_metric.score}")
print(f"Justificación: {faithfulness_metric.reason}")

relevancy_metric.measure(test_case)
print(f"Relevancia: {relevancy_metric.score}")
print(f"Justificación: {relevancy_metric.reason}")
    """, language="python")
    
    st.subheader("3. Ejecución Masiva con PyTest (Pipeline CI/CD)")
    st.markdown("""
    DeepEval se integra perfectamente con `pytest` para poder automatizar las pruebas unitarias de tus LLMs. 
    Guarda el siguiente código en un archivo llamado `test_rag.py` y ejecútalo con el comando `deepeval test run test_rag.py`.
    """)
    st.code("""
# test_rag.py
import pytest
import os
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import GeminiModel

# El modelo Gemini lee la API key desde la variable de entorno GOOGLE_API_KEY o puedes pasarla
api_key = os.getenv("GEMINI_API_KEY")
gemini_judge = GeminiModel(model="gemini-3.1-flash-lite", api_key=api_key)

def test_politica_contrasenas():
    # 1. Definir caso de prueba
    test_case = LLMTestCase(
        input="¿Cada cuánto debo cambiar mi contraseña?",
        actual_output="Cada 90 días de forma obligatoria.",
        retrieval_context=["Las contraseñas de ActumLogos deben ser actualizadas obligatoriamente cada 90 días."]
    )
    
    # 2. Configurar la métrica
    metric = FaithfulnessMetric(threshold=0.6, model=gemini_judge)
    
    # 3. Ejecutar y asegurar que pase el umbral
    assert_test(test_case, [metric])
    """, language="python")
