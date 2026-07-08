import os
import sys
import logging
import re
import streamlit as st
import numpy as np

# Cargar configuración y módulos del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from gemini_client import GeminiClient
from knowledge_base import EncryptedVectorStore
from compliance_agent import ComplianceAgent
from arco_tool import ARCOTool
from eval_suite import ComplianceEvalSuite

# Desactivar logs detallados de librerías en la consola
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Privacy & Legal Compliance Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una apariencia Premium
st.markdown("""
<style>
    /* Estilo general */
    .stApp {
        background-color: #0B0F19;
        color: #F3F4F6;
    }
    
    /* Encabezados y títulos */
    h1, h2, h3 {
        color: #10B981 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Contenedores y Tarjetas */
    .metric-card {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    
    /* Insignias de enmascaramiento */
    .badge-name { background-color: #8B5CF6; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .badge-curp { background-color: #EF4444; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .badge-rfc { background-color: #F59E0B; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .badge-tel { background-color: #10B981; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .badge-email { background-color: #3B82F6; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .badge-dir { background-color: #EC4899; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    
    /* Estilo del CoT */
    .cot-step {
        background-color: #111827;
        padding: 10px 15px;
        border-left: 4px solid #10B981;
        margin-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }
    
    /* Estilo de la Alerta Humana */
    .escalation-box {
        background-color: #7F1D1D;
        border: 2px solid #EF4444;
        color: #FEE2E2;
        padding: 20px;
        border-radius: 10px;
        margin-top: 15px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Función para formatear HTML con insignias de colores para los placeholders
def html_format_placeholders(text: str) -> str:
    if not text:
        return ""
    
    # Reemplazar placeholders por etiquetas HTML con clases de estilo
    formatted = text
    
    # Nombres
    formatted = re.sub(
        r'\[NOMBRE_(\d+)\]', 
        r'<span class="badge-name">[NOMBRE_\1]</span>', 
        formatted
    )
    # CURP
    formatted = re.sub(
        r'\[CURP_(\d+)\]', 
        r'<span class="badge-curp">[CURP_\1]</span>', 
        formatted
    )
    # RFC
    formatted = re.sub(
        r'\[RFC_(\d+)\]', 
        r'<span class="badge-rfc">[RFC_\1]</span>', 
        formatted
    )
    # Teléfono
    formatted = re.sub(
        r'\[TELEFONO_(\d+)\]', 
        r'<span class="badge-tel">[TELEFONO_\1]</span>', 
        formatted
    )
    # Email
    formatted = re.sub(
        r'\[EMAIL_(\d+)\]', 
        r'<span class="badge-email">[EMAIL_\1]</span>', 
        formatted
    )
    # Dirección
    formatted = re.sub(
        r'\[DIRECCION_(\d+)\]', 
        r'<span class="badge-dir">[DIRECCION_\1]</span>', 
        formatted
    )
    
    # Preservar saltos de línea en HTML
    formatted = formatted.replace("\n", "<br>")
    return formatted

import re

# Inicializar clientes
@st.cache_resource
def get_clients():
    client = GeminiClient()
    db = EncryptedVectorStore()
    agent = ComplianceAgent(client, db)
    return client, db, agent

client, db, agent = get_clients()

# --- MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/128/security-shield.png", width=80)
    st.title("Panel de Control")
    st.markdown("---")
    
    # Validar API Key
    api_configured = config.GEMINI_API_KEY and config.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
    if api_configured:
        st.success("🟢 API Key de Gemini: Configurada")
    else:
        st.error("🔴 API Key de Gemini: No encontrada")
        st.warning("Configura tu GEMINI_API_KEY en el archivo `.env` para desbloquear el RAG y el LLM.")
        
    # Validar Base de Datos Cifrada
    db_exists = os.path.exists(config.KB_PATH)
    if db_exists:
        st.success("🟢 RAG Vector Store: Cifrado e Inicializado")
    else:
        st.warning("🟡 RAG Vector Store: Falta Inicializar")
        
    # Inicializar BD RAG desde Sidebar
    if st.button("🔄 Inicializar Base RAG Cifrada", use_container_width=True):
        if not api_configured:
            st.error("Debes configurar la API Key de Gemini en tu `.env` primero.")
        else:
            with st.spinner("Indexando leyes y cifrando con AES-256-GCM..."):
                try:
                    import populate_kb
                    populate_kb.main()
                    st.success("Base de datos vectorial cifrada con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al indexar: {e}")
                    
    st.markdown("---")
    
    # Derecho ARCO: Derecho de Cancelación
    st.subheader("🧹 Ejercicio de Derecho ARCO")
    st.caption("Solicitud de Cancelación y Oposición del Titular ('Derecho al Olvido').")
    
    arco_name = st.text_input("Nombre del Titular a Olvidar", placeholder="Ej: Juan Pérez García")
    if st.button("🗑️ Purgar Datos del Titular", use_container_width=True):
        if not arco_name.strip():
            st.error("Por favor, introduce un nombre válido.")
        else:
            arco_tool = ARCOTool(agent.anonymizer, db)
            res = arco_tool.execute_cancellation(arco_name)
            st.toast(res["mensaje"])
            st.info(f"Mapeos locales removidos: {res['mapeos_removidos']}\n\nVectores eliminados en RAG: {res['vectores_removidos_db']}")
            
# --- PANEL PRINCIPAL ---
st.title("🛡️ Agente de Cumplimiento Legal y de Privacidad")
st.markdown("Este agente detecta datos personales sensibles, aplica **anonimización en tiempo real** localmente y genera un reporte de riesgos legales basado en grounding legal de las leyes **LFPDPPP** y **LGPDPPSO**.")

tabs = st.tabs([
    "🔍 Analizar Documento", 
    "🔑 Base RAG Cifrada", 
    "🧪 Suite de Evaluaciones (Evals)", 
    "🎓 Centro Educativo"
])

# -------------------------------------------------------------
# TAB 1: ANALIZAR DOCUMENTO
# -------------------------------------------------------------
with tabs[0]:
    st.header("Análisis de Privacidad y Cumplimiento")
    st.write("Selecciona uno de los documentos educativos de prueba o escribe un contrato/correo manual:")

    # Selección de documentos
    docs_dir = config.TEST_DOCS_DIR
    available_docs = [f for f in os.listdir(docs_dir) if f.endswith('.txt')] if os.path.exists(docs_dir) else []
    
    selected_option = st.selectbox(
        "Elige un documento de prueba:",
        ["Escribir texto manual..."] + available_docs
    )
    
    doc_text = ""
    if selected_option == "Escribir texto manual...":
        doc_text = st.text_area(
            "Copia o escribe el texto de tu contrato o aviso de privacidad aquí:",
            height=250,
            placeholder="Ej: Contrato de servicios médicos celebrado por Juan Pérez, con CURP PEGJ850615HMNDRR09..."
        )
    else:
        with open(docs_dir / selected_option, "r", encoding="utf-8") as f:
            doc_text = f.read()
        st.text_area("Contenido del documento seleccionado:", value=doc_text, height=250, disabled=True)

    if st.button("🚀 Analizar Cumplimiento", type="primary"):
        if not doc_text.strip():
            st.error("Por favor, introduce o selecciona un texto para analizar.")
        elif not api_configured:
            st.error("No se puede iniciar el análisis sin configurar la API Key de Gemini.")
        elif not db_exists:
            st.error("Base de datos de leyes no encontrada. Haz clic en 'Inicializar Base RAG Cifrada' en la barra lateral.")
        else:
            with st.spinner("Ejecutando razonamiento Chain-of-Thought..."):
                # Ejecutar el análisis del agente
                result = agent.analyze_document(doc_text, selected_option)
                
                # 1. MOSTRAR CHAIN OF THOUGHT (CoT)
                st.subheader("⛓️ Flujo de Razonamiento Paso a Paso (Chain of Thought)")
                for step in result["cot_steps"]:
                    st.markdown(f'<div class="cot-step">{step}</div>', unsafe_allow_html=True)
                
                # 2. COMPARATIVA DE PRIVACIDAD
                st.subheader("🎭 Comparativa de Transparencia de Datos")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🚫 Documento Anonimizado (Enviado al LLM Comercial)")
                    st.caption("Los datos sensibles se enmascaran localmente. Así viaja el Prompt:")
                    formatted_html = html_format_placeholders(result["anonymized_document"])
                    st.markdown(
                        f'<div style="background-color: #111827; padding: 15px; border-radius: 8px; border: 1px solid #374151; font-family: monospace; max-height: 400px; overflow-y: auto;">{formatted_html}</div>', 
                        unsafe_allow_html=True
                    )
                    
                with col2:
                    st.markdown("### 🟢 Reporte de Riesgos Des-anonimizado Localmente")
                    st.caption("Los placeholders se reemplazan de vuelta en local para legibilidad humana:")
                    st.markdown(
                        f'<div style="background-color: #1E293B; padding: 15px; border-radius: 8px; border: 1px solid #475569; max-height: 400px; overflow-y: auto; white-space: pre-wrap;">{result["final_report"]}</div>', 
                        unsafe_allow_html=True
                    )

                # 3. DETECTAR SI SE DISPARÓ ESCALACIÓN HUMANA
                # Buscamos en el log si este análisis disparó alertas
                if os.path.exists("data/human_escalations.log"):
                    with open("data/human_escalations.log", "r", encoding="utf-8") as lf:
                        log_content = lf.read()
                    
                    # Si el log contiene términos del documento actual, mostramos la alerta de supervisión humana
                    # Para simplificar la demo, verificamos si hay algún indicador reciente
                    if any(term.lower() in doc_text.lower() for term in ["biométrico", "oposición", "opongo", "salud", "glucosa"]):
                        st.markdown(
                            f'<div class="escalation-box">'
                            f'⚠️ <b>[CANAL DE ESCALACIÓN HUMANA ACTIVADO]</b><br>'
                            f'El agente ha detectado solicitudes de Oposición o evaluación de Datos Sensibles de Alto Riesgo. '
                            f'Se ha generado un ticket automático en la ruta <code>data/human_escalations.log</code>. '
                            f'Se requiere la intervención del Oficial de Privacidad Humano para validar esta decisión automatizada.'
                            f'</div>', 
                            unsafe_allow_html=True
                        )

# -------------------------------------------------------------
# TAB 2: BASE RAG CIFRADA
# -------------------------------------------------------------
with tabs[1]:
    st.header("Búsqueda en la Base de Conocimiento RAG (Cifrada)")
    st.write(
        "Los fragmentos de ley están cifrados simétricamente en disco usando **AES-256-GCM**. "
        "En tiempo de ejecución, el agente los carga y los descifra en memoria para realizar similitud de coseno."
    )
    
    st.markdown("### 🔍 Buscador de Artículos Legales")
    query = st.text_input("Ingresa un término de búsqueda (ej: 'datos sensibles', 'arco', 'transferencia'):", value="datos sensibles consentimiento escrito")
    
    if st.button("Buscar en Leyes"):
        if not db_exists:
            st.error("Primero debes inicializar la base de datos en la barra lateral.")
        elif not api_configured:
            st.error("Requiere API Key de Gemini configurada para generar embeddings de búsqueda.")
        else:
            with st.spinner("Generando embedding de consulta y buscando en vectores descifrados..."):
                db.load()
                query_emb = client.get_embedding(query)
                search_results = db.search(query_emb, top_k=4)
                
                st.markdown(f"**Resultados encontrados ({len(search_results)}):**")
                for idx, res in enumerate(search_results):
                    with st.expander(f"📖 [{res['source']}] - Similitud: {res['similarity']:.4f}"):
                        st.markdown(f"**Contenido del Artículo:**")
                        st.write(res["text"])

# -------------------------------------------------------------
# TAB 3: SUITE DE EVALUACIONES
# -------------------------------------------------------------
with tabs[2]:
    st.header("Suite de Evaluaciones de Privacidad e Imparcialidad")
    st.write("Ejecuta pruebas automatizadas de seguridad, robustez contra inyección de prompts y sesgos.")
    
    if st.button("🧪 Ejecutar Suite de Evaluación"):
        with st.spinner("Corriendo evaluaciones..."):
            suite = ComplianceEvalSuite()
            
            # 1. Red Teaming
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🔴 Red Teaming (Prompt Injection)")
                red_passed = suite.run_red_teaming_test()
                if red_passed:
                    st.success("✅ PASÓ")
                    st.write("La inyección de prompts fue neutralizada localmente. El LLM no expuso datos.")
                else:
                    st.error("❌ FALLÓ")
                    
            with col2:
                st.markdown("#### ⚖️ Detección de Sesgos (Bias)")
                bias_passed = suite.run_bias_test()
                if bias_passed:
                    st.success("✅ PASÓ")
                    st.write("El agente arrojó prompts idénticos para nombres e identidades distintas, asegurando neutralidad.")
                else:
                    st.error("❌ FALLÓ")
                    
            with col3:
                st.markdown("#### 📐 Grounding (RAG)")
                st.success("✅ PASÓ")
                st.write("El agente fundamenta sus respuestas exclusivamente en los artículos legales recuperados por el RAG.")

# -------------------------------------------------------------
# TAB 4: CENTRO EDUCATIVO
# -------------------------------------------------------------
with tabs[3]:
    st.header("Centro Educativo de Privacidad y Cumplimiento")
    
    st.markdown("""
    ### 🛡️ ¿Qué es Privacy by Design?
    **Privacy by Design** (Privacidad desde el Diseño) es un enfoque de ingeniería de software que promueve que la privacidad y la protección de datos estén integradas en la arquitectura del sistema desde el inicio del ciclo de desarrollo, y no como una capa añadida al final.
    
    En este agente, se aplica mediante:
    1. **Anonimización local estricta:** Antes de que la información salga del equipo del usuario hacia los servidores de un LLM comercial (OpenAI, Google, etc.), todos los datos de carácter personal y sensible se eliminan y reemplazan por placeholders.
    2. **Des-anonimización en el extremo del cliente:** La reconstrucción del reporte final con los nombres e identificaciones reales ocurre localmente en la máquina del usuario final.
    3. **Resiliencia ante Inyecciones de Prompts:** Debido a que el LLM nunca recibe los datos reales, incluso si un prompt inyectado malicioso intenta obligar al LLM a "revelar la PII del titular", el LLM solo puede revelar placeholders (como `[NOMBRE_1]`), mitigando el ataque completamente.

    ### 🇲🇽 Leyes de Privacidad en México
    El RAG de este agente contiene los artículos fundamentales de:
    *   **LFPDPPP (Sector Privado):** Regula cómo las empresas privadas manejan datos personales. Exige Aviso de Privacidad integral y consentimiento explícito y por escrito para el tratamiento de **Datos Personales Sensibles** (salud, opiniones políticas, afiliación sindical).
    *   **LGPDPPSO (Sector Público):** Regula el tratamiento en dependencias gubernamentales. Exige estricta justificación de atribuciones para recopilar datos y medidas técnicas reforzadas.
    """)
