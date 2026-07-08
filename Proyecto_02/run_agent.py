import os
import sys
import logging
from dotenv import load_dotenv

# Configurar logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ComplianceCLI")

# Desactivar logs detallados en consola para hacer la interfaz CLI más limpia
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from config import RAW_LAWS_DIR, TEST_DOCS_DIR, KB_PATH, GEMINI_API_KEY
from gemini_client import GeminiClient
from knowledge_base import EncryptedVectorStore
from compliance_agent import ComplianceAgent
from arco_tool import ARCOTool
from eval_suite import ComplianceEvalSuite

def print_banner():
    print("""
========================================================================
   AGENTE DE CUMPLIMIENTO LEGAL Y DE PRIVACIDAD (COMPLIANCE AGENT)
                  - PROYECTO EDUCATIVO DE PRIVACIDAD -
========================================================================
Este agente demuestra los conceptos de:
1. Privacy by Design: Anonimización local de PII en tiempo real.
2. RAG Cifrado: Almacenamiento seguro de leyes en base vectorial AES-256.
3. Razonamiento CoT (Chain of Thought): Desglose del análisis de riesgos.
4. Derechos ARCO: Ejercicio del Derecho de Cancelación ("Derecho al Olvido").
5. Supervisión Humana: Detección y canal de escalación humana.
========================================================================
""")

def select_document() -> str:
    """Permite al usuario seleccionar un documento de prueba o escribir uno."""
    docs = [f for f in os.listdir(TEST_DOCS_DIR) if f.endswith('.txt')]
    
    print("\nDocumentos de prueba disponibles:")
    for idx, doc in enumerate(docs):
        print(f" [{idx + 1}] {doc}")
    print(f" [{len(docs) + 1}] Ingresar texto manual...")
    print(" [0] Cancelar")
    
    try:
        opt = int(input("\nSelecciona una opción: "))
        if opt == 0:
            return None
        elif opt == len(docs) + 1:
            print("\nEscribe o pega el texto del documento (presiona Enter y luego Ctrl+Z en Windows para finalizar en una nueva línea, o escribe 'FIN' en una línea vacía):")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "FIN":
                        break
                    lines.append(line)
                except EOFError:
                    break
            return "\n".join(lines)
        elif 1 <= opt <= len(docs):
            filepath = TEST_DOCS_DIR / docs[opt - 1]
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
    except ValueError:
        print("[!] Opción inválida.")
    return None

def check_env():
    """Verifica si la API Key de Gemini está configurada."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("\n" + "!"*80)
        print("¡ATENCIÓN! GEMINI_API_KEY no configurada en el archivo .env.")
        print("El análisis RAG y las llamadas al LLM no funcionarán hasta que agregues una clave válida.")
        print("!"*80 + "\n")
        return False
    return True

def run_menu():
    client = GeminiClient()
    db = EncryptedVectorStore()
    agent = ComplianceAgent(client, db)
    arco_tool = ARCOTool(agent.anonymizer, db)

    # Verificar si la base vectorial existe
    if not os.path.exists(KB_PATH):
        print("[RAG] Base vectorial no encontrada. Se recomienda inicializarla (Opción 1).")

    while True:
        print("\n--- MENÚ PRINCIPAL ---")
        print(" [1] Inicializar / Poblar Base de Conocimiento RAG (Leyes Cifradas)")
        print(" [2] Analizar Documento (Flujo CoT con Anonimización)")
        print(" [3] Ejercer Derecho ARCO (Derecho de Cancelación)")
        print(" [4] Ejecutar Suite de Evaluaciones (Red Teaming, Grounding, Sesgo)")
        print(" [0] Salir")
        
        try:
            choice = input("\nSeleccione una opción: ").strip()
            if choice == "0":
                print("\nGracias por usar el Agente de Cumplimiento Educativo. ¡Hasta luego!")
                break
                
            elif choice == "1":
                if not check_env():
                    continue
                print("\nEjecutando populate_kb.py...")
                import populate_kb
                try:
                    populate_kb.main()
                except SystemExit:
                    pass
                    
            elif choice == "2":
                if not check_env():
                    continue
                # Verificar si la DB ya fue poblada
                if not os.path.exists(KB_PATH):
                    print("\n[!] Primero debes inicializar la base de datos (Opción 1).")
                    continue
                    
                doc_content = select_document()
                if not doc_content:
                    continue
                    
                print("\n--- INICIANDO PROCESAMIENTO ---")
                analysis = agent.analyze_document(doc_content, "Documento de Usuario")
                
                # Visualización educativa paso a paso
                print("\n=======================================================")
                print("1. PROMPT ENVIADO AL LLM COMERCIAL (ANONIMIZADO)")
                print("=======================================================")
                print("Este es el texto exacto que salió de la máquina del usuario:")
                print("-------------------------------------------------------")
                print(analysis["anonymized_document"][:800] + "\n...")
                print("-------------------------------------------------------")
                print("  * OBSERVACIÓN: ¡Ningún dato personal real fue expuesto!")

                print("\n=======================================================")
                print("2. REPORTE BRUTO DEVUELTO POR EL LLM (ANONIMIZADO)")
                print("=======================================================")
                print(analysis["anonymized_report"][:800] + "\n...")
                print("-------------------------------------------------------")

                print("\n=======================================================")
                print("3. REPORTE FINAL DES-ANONIMIZADO LOCALMENTE")
                print("=======================================================")
                print("Los placeholders han sido reemplazados con los datos originales:")
                print("-------------------------------------------------------")
                print(analysis["final_report"])
                print("-------------------------------------------------------")
                
                # Revisar log de escalación humana
                if os.path.exists("data/human_escalations.log"):
                    print("\n[Audit] Revisa 'data/human_escalations.log' para auditorías de supervisión humana.")
                    
            elif choice == "3":
                user_to_delete = input("\nIngrese el nombre completo del titular a olvidar (ej. Juan Pérez García): ").strip()
                if not user_to_delete:
                    print("[!] Nombre no válido.")
                    continue
                    
                result = arco_tool.execute_cancellation(user_to_delete)
                print("\n=======================================================")
                print("RESULTADO DE EJERCICIO DE DERECHO ARCO (CANCELACIÓN)")
                print("=======================================================")
                print(f" Titular: {result['titular']}")
                print(f" Mapeos en proxy eliminados: {result['mapeos_removidos']}")
                print(f" Registros en BD vectorial eliminados: {result['vectores_removidos_db']}")
                print(f" Mensaje: {result['mensaje']}")
                print("=======================================================")
                
            elif choice == "4":
                suite = ComplianceEvalSuite()
                suite.run_red_teaming_test()
                suite.run_grounding_test()
                suite.run_bias_test()
                
            else:
                print("[!] Opción no válida.")
        except Exception as e:
            print(f"\n[!] Ocurrió un error: {e}")
            logger.exception(e)

if __name__ == "__main__":
    print_banner()
    run_menu()
