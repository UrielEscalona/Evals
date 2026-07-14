import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import time

from src.agent import ReActAgent
from src.database import get_all_products, update_product_stock, load_policies
from src.tools import tracker
from src.evaluator import run_full_evaluation, SCENARIOS

# Page Configuration
st.set_page_config(
    page_title="Agent E-commerce Evaluator 🚀",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Dark glassmorphic styling */
    .stApp {
        background-color: #0f111a;
        color: #e2e8f0;
    }
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa 0%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #6366f1;
    }
    .step-card {
        background-color: #1e1b4b;
        border-left: 4px solid #818cf8;
        padding: 1rem;
        border-radius: 4px 8px 8px 4px;
        margin-bottom: 1rem;
    }
    .observation-card {
        background-color: #020617;
        border-left: 4px solid #10b981;
        padding: 0.8rem;
        border-radius: 4px;
        font-family: monospace;
        margin-top: 0.5rem;
    }
    .cost-badge {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .error-badge {
        background: linear-gradient(90deg, #ef4444 0%, #b91c1c 100%);
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Title section
st.markdown('<h1 class="main-header">Plataforma de Evals para Agentes de IA 🛍️</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Evaluación de Planificación, Selección de Herramientas y Recuperación de Fallas con gemma4:latest</p>', unsafe_allow_html=True)

# Session State Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_cost" not in st.session_state:
    st.session_state.session_cost = 0.0
if "session_tokens" not in st.session_state:
    st.session_state.session_tokens = {"in": 0, "out": 0}
if "fail_shipping_api" not in st.session_state:
    st.session_state.fail_shipping_api = False

# Sidebar Config
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/ai.png", width=100)
    st.markdown("### Configuración del Entorno")
    
    # Model Selector (Instruction indicates gemma4 is pre-loaded)
    model_name = st.text_input("Modelo Ollama", value="gemma4:latest", disabled=True)
    
    # LLM Host Endpoint
    base_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
    
    st.markdown("---")
    st.markdown("### Interruptores de Fallo (Robusto)")
    
    # Checkbox to force shipping API failures
    fail_shipping_api = st.checkbox(
        "Simular Caída de API de Envíos (Error 500)",
        value=st.session_state.fail_shipping_api,
        help="Fuerza un fallo en calcular_envio() para verificar si el agente se recupera."
    )
    st.session_state.fail_shipping_api = fail_shipping_api
    
    st.markdown("---")
    st.markdown("### Métricas de Sesión de Chat")
    st.metric("Costo Acumulado", f"${st.session_state.session_cost:.4f} USD", help="Dinero ficticio gastado en esta pestaña de chat por tokens + APIs.")
    st.metric("Tokens Consumidos", f"{st.session_state.session_tokens['in'] + st.session_state.session_tokens['out']:,}", help="Suma de tokens de Entrada y Salida.")
    
    if st.button("Limpiar Chat"):
        st.session_state.chat_history = []
        st.session_state.session_cost = 0.0
        st.session_state.session_tokens = {"in": 0, "out": 0}
        st.rerun()

# Tabs
tab_chat, tab_evals, tab_db = st.tabs(["💬 Chat con el Agente", "📊 Dashboard de Evals", "🗄️ Base de Datos & Políticas"])

# ================= TAB 1: CHAT WITH THE AGENT =================
with tab_chat:
    st.markdown("### Interactúa con el Agente de Gestión de Pedidos")
    st.write("Pregúntale por laptops, disponibilidad de stock, cotizaciones de envío o políticas de reembolso.")
    
    # User Predefined Examples
    st.markdown("**Sugerencias de Consulta:**")
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    with col_ex1:
        if st.button("Comprar la laptop de 16GB más barata"):
            st.session_state.pending_query = "Quiero comprar la laptop de 16GB de RAM más barata que tenga envío menor a dos días al CP 01000."
    with col_ex2:
        if st.button("Aplicar descuento en la Dell ID 101"):
            st.session_state.pending_query = "Quiero comprar la Dell ID 101 aplicando el cupón DESCUENTO10. ¿Cuál es el precio final?"
    with col_ex3:
        if st.button("Preguntar sobre políticas de garantía"):
            st.session_state.pending_query = "¿Cuál es la garantía de una laptop reacondicionada según las políticas?"
            
    # Check if example was clicked
    query = st.chat_input("Escribe tu mensaje para el agente...")
    if "pending_query" in st.session_state:
        query = st.session_state.pop("pending_query")

    # Render past chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            # Show steps expander if assistant message has steps
            if msg["role"] == "assistant" and "steps" in msg and msg["steps"]:
                with st.expander("🛠️ Ver Pensamiento Interno y Costo de APIs"):
                    for step in msg["steps"]:
                        st.markdown(f"**Paso {step['step']}:**")
                        st.markdown(f"<div class='step-card'><b>Pensamiento:</b> {step['thought']}<br>"
                                    f"<b>Acción:</b> <code style='color:#f472b6'>{step['action']}({step['arguments']})</code></div>", unsafe_allow_html=True)
                        if step["observation"]:
                            st.markdown(f"<div class='observation-card'><b>Observación:</b> {step['observation']}</div>", unsafe_allow_html=True)
                    st.markdown(f"**Métricas de esta respuesta:** "
                                f"<span class='cost-badge'>Costo de APIs: ${msg['api_cost']:.4f} USD</span> "
                                f"<span class='cost-badge'>Costo de Tokens: ${msg['token_cost']:.4f} USD</span>", unsafe_allow_html=True)

    # Process new user input
    if query:
        # Display user message
        with st.chat_message("user"):
            st.write(query)
        st.session_state.chat_history.append({"role": "user", "content": query})
        
        # Display assistant thinking status
        with st.chat_message("assistant"):
            status_placeholder = st.empty()
            status_placeholder.markdown("*El agente está planificando y ejecutando herramientas...* ⌛")
            
            # Execute Agent
            agent = ReActAgent(model_name="gemma4:latest", base_url=base_url)
            
            # Run
            result = agent.run(
                user_query=query,
                chat_history=st.session_state.chat_history[:-1],  # Exclude current query as it is sent separately
                fail_shipping=st.session_state.fail_shipping_api
            )
            
            if result["success"]:
                # Clear loader and write final response
                status_placeholder.empty()
                st.write(result["final_answer"])
                
                # Append assistant message with steps
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["final_answer"],
                    "steps": result["steps"],
                    "api_cost": result["api_cost"],
                    "token_cost": result["token_cost"]
                })
                
                # Update session cost & tokens
                st.session_state.session_cost += result["total_cost"]
                st.session_state.session_tokens["in"] += result["tokens"]["input"]
                st.session_state.session_tokens["out"] += result["tokens"]["output"]
                
                # Show steps expander
                if result["steps"]:
                    with st.expander("🛠️ Ver Pensamiento Interno y Costo de APIs"):
                        for step in result["steps"]:
                            st.markdown(f"**Paso {step['step']}:**")
                            st.markdown(f"<div class='step-card'><b>Pensamiento:</b> {step['thought']}<br>"
                                        f"<b>Acción:</b> <code style='color:#f472b6'>{step['action']}({step['arguments']})</code></div>", unsafe_allow_html=True)
                            if step["observation"]:
                                st.markdown(f"<div class='observation-card'><b>Observación:</b> {step['observation']}</div>", unsafe_allow_html=True)
                        st.markdown(f"**Métricas de esta respuesta:** "
                                    f"<span class='cost-badge'>Costo de APIs: ${result['api_cost']:.4f} USD</span> "
                                    f"<span class='cost-badge'>Costo de Tokens: ${result['token_cost']:.4f} USD</span>", unsafe_allow_html=True)
                
                # Rerun to update sidebar metrics
                st.rerun()
            else:
                status_placeholder.markdown(f"❌ Error en la ejecución: {result['final_answer']}")

# ================= TAB 2: EVALS DASHBOARD =================
with tab_evals:
    st.markdown("### Suite de Evaluaciones de Agentes (Evals)")
    st.write("Las evals corren de forma determinista y evalúan de manera automatizada la completitud de tareas, la correcta selección de herramientas y los costos financieros por errores.")
    
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_btn = st.button("⚡ Ejecutar Suite Completa", use_container_width=True)
    with col_info:
        st.write("Nota: La suite ejecuta 5 escenarios de prueba con diferentes complejidades usando tu instancia local de Ollama.")
        
    EVAL_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "eval_history.json")
    
    if run_btn:
        with st.spinner("Ejecutando evaluaciones... Esto tomará entre 30 y 60 segundos debido a la velocidad de inferencia de Ollama..."):
            summary = run_full_evaluation()
            st.success("¡Evaluación completada con éxito!")
            
    # Load and display history
    if os.path.exists(EVAL_HISTORY_FILE):
        with open(EVAL_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
            
        if history:
            latest_run = history[-1]
            totals = latest_run["totals"]
            scenarios = latest_run["scenarios"]
            
            st.markdown("---")
            st.markdown("#### Resultados del Último Test de Evals")
            st.caption(f"Ejecutado el: {latest_run['date']}")
            
            # KPI Cards
            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            with col_kpi1:
                st.markdown(f"<div class='metric-card'><h5 style='color:#94a3b8;margin:0;'>Completitud de Tarea</h5><h2 style='color:#10b981;margin:5px 0;'>{totals['task_completion_rate']:.1f}%</h2><p style='color:#64748b;margin:0;'>{totals['completed_tasks']}/{totals['scenarios_count']} Pasados</p></div>", unsafe_allow_html=True)
            with col_kpi2:
                st.markdown(f"<div class='metric-card'><h5 style='color:#94a3b8;margin:0;'>Llamadas de Tools</h5><h2 style='color:#818cf8;margin:5px 0;'>{totals['tool_correctness_rate']:.1f}%</h2><p style='color:#64748b;margin:0;'>Selección correcta</p></div>", unsafe_allow_html=True)
            with col_kpi3:
                st.markdown(f"<div class='metric-card'><h5 style='color:#94a3b8;margin:0;'>Costo de Ejecución</h5><h2 style='color:#f472b6;margin:5px 0;'>${totals['total_cost_usd']:.4f} USD</h2><p style='color:#64748b;margin:0;'>Tokens + APIs</p></div>", unsafe_allow_html=True)
            with col_kpi4:
                st.markdown(f"<div class='metric-card'><h5 style='color:#94a3b8;margin:0;'>Latencia Promedio</h5><h2 style='color:#f59e0b;margin:5px 0;'>{totals['average_latency_sec']:.2f} s</h2><p style='color:#64748b;margin:0;'>Por escenario</p></div>", unsafe_allow_html=True)
                
            # Visual Graphs
            st.markdown("#### Análisis Gráfico de Rendimiento Financiero y Precisión")
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                # Cost Breakdown Pie Chart
                cost_data = pd.DataFrame({
                    "Concepto": ["Costo de Tokens de LLM", "Cobro de Consultas APIs (Tools)"],
                    "Costo (USD)": [totals["total_token_cost_usd"], totals["total_api_cost_usd"]]
                })
                fig_pie = px.pie(cost_data, values="Costo (USD)", names="Concepto", 
                                 title="Distribución de Costo Financiero de la Corrida",
                                 color_discrete_sequence=["#f472b6", "#818cf8"])
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_graph2:
                # Scenarios Cost & Performance Bar Chart
                scen_names = [s["name"] for s in scenarios]
                scen_costs = [s["metrics"]["cost_usd"] for s in scenarios]
                scen_success = ["Pasado" if s["metrics"]["task_completed"] else "Fallado" for s in scenarios]
                
                df_scenarios = pd.DataFrame({
                    "Escenario": scen_names,
                    "Costo (USD)": scen_costs,
                    "Resultado": scen_success
                })
                
                fig_bar = px.bar(df_scenarios, x="Escenario", y="Costo (USD)", color="Resultado",
                                 title="Costo Financiero vs. Estado por Escenario",
                                 color_discrete_map={"Pasado": "#10b981", "Fallado": "#ef4444"})
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig_bar, use_container_width=True)
                
            # Detailed breakdown per scenario
            st.markdown("#### Detalle Técnico por Escenario")
            for idx, scen in enumerate(scenarios):
                with st.expander(f"Escenario {scen['scenario_id']}: {scen['name']} - {'✅ PASADO' if scen['metrics']['task_completed'] else '❌ FALLADO'}"):
                    st.write(f"**Objetivo:** {SCENARIOS[idx]['description']}")
                    st.write(f"**Consulta del usuario:** *\"{SCENARIOS[idx]['prompt']}\"*")
                    st.markdown(f"**Respuesta del Agente:**\n{scen['final_answer']}")
                    
                    st.markdown("**Métricas Financieras y de Inferencia:**")
                    col_met1, col_met2, col_met3 = st.columns(3)
                    col_met1.write(f"**Pasos Ejecutados:** {scen['metrics']['steps_count']}")
                    col_met2.write(f"**Tokens Totales:** {scen['metrics']['tokens_in'] + scen['metrics']['tokens_out']} ({scen['metrics']['tokens_in']} In, {scen['metrics']['tokens_out']} Out)")
                    col_met3.write(f"**Costo del Escenario:** ${scen['metrics']['cost_usd']:.5f} USD")
                    
                    # Tool sequence visualization
                    if scen["steps"]:
                        st.markdown("**Secuencia de Herramientas Llamadas:**")
                        tools_seq = " ➡️ ".join([f"`{step['action']}`" for step in scen["steps"]])
                        st.markdown(tools_seq)
                        
                    if scen["failures"]:
                        st.markdown("**Fallos Detectados:**")
                        for fail in scen["failures"]:
                            st.markdown(f"<span class='error-badge'>✗ {fail}</span>", unsafe_allow_html=True)
                            
            # Historical Trends Chart
            st.markdown("#### Histórico de Evaluaciones (Evolución en el Tiempo)")
            dates = [run["date"] for run in history]
            tcrs = [run["totals"]["task_completion_rate"] for run in history]
            costs = [run["totals"]["total_cost_usd"] for run in history]
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=dates, y=tcrs, name="Completitud de Tarea (%)", yaxis="y1", line=dict(color="#10b981", width=2)))
            fig_trend.add_trace(go.Scatter(x=dates, y=costs, name="Costo Total (USD)", yaxis="y2", line=dict(color="#f472b6", width=2)))
            
            fig_trend.update_layout(
                title="Tasa de Éxito vs Costo Total en las últimas corridas",
                yaxis=dict(title=dict(text="Completitud de Tarea (%)", font=dict(color="#10b981")), tickfont=dict(color="#10b981")),
                yaxis2=dict(title=dict(text="Costo (USD)", font=dict(color="#f472b6")), tickfont=dict(color="#f472b6"), overlaying="y", side="right"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Aún no hay registros de evaluaciones en el historial. Haz clic en 'Ejecutar Suite Completa' para iniciar.")
    else:
        st.info("Haz clic en el botón de arriba para correr la suite de evals por primera vez.")

# ================= TAB 3: DATABASE EXPLORER =================
with tab_db:
    st.markdown("### Explorador de Base de Datos y Políticas de Tienda")
    st.write("Aquí puedes monitorear y alterar el estado del inventario para hacer pruebas de comportamiento 'en vivo' con el agente en la pestaña de chat.")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### Modificar Inventario (Laptops)")
        products = get_all_products()
        df_prod = pd.DataFrame(products)
        
        # Display editable table
        st.dataframe(df_prod[["id", "brand", "model", "price", "ram_gb", "stock", "shipping_days"]], use_container_width=True, hide_index=True)
        
        # Simple edit widget
        st.markdown("##### Cambiar Stock de Producto")
        col_sel_id, col_sel_stock, col_sel_btn = st.columns([2, 2, 1])
        with col_sel_id:
            selected_id = st.selectbox("ID de Laptop", options=df_prod["id"].tolist())
        with col_sel_stock:
            selected_stock = st.number_input("Nuevo Stock", min_value=0, max_value=100, value=int(df_prod[df_prod["id"] == selected_id]["stock"].values[0]))
        with col_sel_btn:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Guardar"):
                if update_product_stock(selected_id, selected_stock):
                    st.success(f"Stock del ID {selected_id} actualizado a {selected_stock} unidades.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("No se pudo actualizar el stock.")
                    
    with col_right:
        st.markdown("#### Base de Conocimientos (Políticas para RAG)")
        policies_text = load_policies()
        st.text_area("Políticas Cargadas", value=policies_text, height=450, disabled=True)
