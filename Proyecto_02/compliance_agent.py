import logging
from anonymizer import PIIAnonymizer
from knowledge_base import EncryptedVectorStore
from gemini_client import GeminiClient
from logger_escalation import EscalationLogger

logger = logging.getLogger("ComplianceAgent")

class ComplianceAgent:
    """
    Agente de Cumplimiento Legal y de Privacidad (Compliance Agent).
    
    Implementa un flujo de Razonamiento CoT (Chain of Thought) estructurado en 4 pasos:
    1. Percepción: Identifica Datos Personales en el documento de entrada.
    2. Anonimización: Enmascara los datos mediante el PIIAnonymizer.
    3. RAG/Razonamiento: Recupera los artículos legales pertinentes de la BD vectorial cifrada.
    4. Respuesta: Invoca al LLM (gemini-3.1-flash-lite) con el contexto de las leyes y genera el reporte.
    
    Garantiza que la API comercial de Gemini NUNCA reciba datos sin anonimizar.
    """
    def __init__(self, api_client: GeminiClient, vector_store: EncryptedVectorStore):
        self.client = api_client
        self.db = vector_store
        self.anonymizer = PIIAnonymizer()
        self.escalator = EscalationLogger()
        
    def analyze_document(self, document_content: str, doc_name: str = "Documento") -> dict:
        """
        Ejecuta el análisis completo de cumplimiento sobre un documento.
        """
        cot_steps = []
        logger.info(f"=== Iniciando Análisis de Cumplimiento CoT para '{doc_name}' ===")
        
        # -------------------------------------------------------------
        # PASO 1: PERCEPCIÓN (Identificar PII localmente)
        # -------------------------------------------------------------
        step_1_msg = "Paso 1 (Percepción): Identificando Datos Personales Sensibles y de identificación en el documento."
        cot_steps.append(step_1_msg)
        print(f"\n[CoT] {step_1_msg}")
        
        # Escaneamos temporalmente para reportar qué se encontró (fines educativos)
        temp_anon = PIIAnonymizer()
        temp_anon.anonymize(document_content)
        detected_entities = list(temp_anon.mappings.values())
        print(f"  > PII Detectada localmente: {detected_entities}")

        # -------------------------------------------------------------
        # PASO 2: ANONIMIZACIÓN (Enmascarar)
        # -------------------------------------------------------------
        step_2_msg = "Paso 2 (Anonimización): Ejecutando la herramienta de enmascaramiento local (Privacy by Design)."
        cot_steps.append(step_2_msg)
        print(f"[CoT] {step_2_msg}")
        
        # Anonimizar el contenido real del documento
        anonymized_doc = self.anonymizer.anonymize(document_content)
        print("  > Documento enmascarado con éxito.")
        logger.debug(f"Documento Anonimizado:\n{anonymized_doc}")

        # -------------------------------------------------------------
        # PASO 3: RAG / RAZONAMIENTO (Consulta a la Base Vectorial Cifrada)
        # -------------------------------------------------------------
        step_3_msg = "Paso 3 (RAG/Razonamiento): Consultando la Base Vectorial Cifrada de Leyes (LFPDPPP y LGPDPPSO)."
        cot_steps.append(step_3_msg)
        print(f"[CoT] {step_3_msg}")
        
        # Cargamos los datos de las leyes si no están cargados
        self.db.load()
        
        # Generar un query de búsqueda. Usamos partes del documento anonimizado
        # o palabras clave que denotan riesgos en el documento.
        # Por seguridad y precisión, podemos extraer temas críticos del doc anonimizado.
        search_query = "datos personales sensibles consentimiento transferencia aviso de privacidad arco"
        if "biométrica" in anonymized_doc.lower() or "salud" in anonymized_doc.lower():
            search_query += " datos sensibles salud consentimiento expreso escrito"
        if "transferencia" in anonymized_doc.lower() or "transferir" in anonymized_doc.lower():
            search_query += " transferencia de datos terceros consentimiento"
            
        logger.info(f"[RAG] Realizando búsqueda vectorial para: '{search_query}'")
        
        # Generar embedding del query llamando a la API (el query está 100% libre de PII)
        query_embedding = self.client.get_embedding(search_query)
        
        # Buscar en la DB vectorial descifrada en memoria
        search_results = self.db.search(query_embedding, top_k=3)
        
        # Construir el contexto legal RAG para el LLM
        legal_context = ""
        print("  > Artículos recuperados del RAG para Grounding:")
        for idx, res in enumerate(search_results):
            source = res["source"]
            sim = res["similarity"]
            text = res["text"]
            legal_context += f"\n--- Fuente: {source} (Similitud: {sim:.4f}) ---\n{text}\n"
            
            # Imprimir el fragmento recuperado
            lines = text.split('\n')
            snippet = lines[0] if lines else ""
            print(f"    * [{source}] Similitud: {sim:.2f} | {snippet}...")
            
        logger.debug(f"Contexto Legal Recuperado:\n{legal_context}")

        # -------------------------------------------------------------
        # PASO 4: RESPUESTA (Generar el reporte de riesgos)
        # -------------------------------------------------------------
        step_4_msg = "Paso 4 (Respuesta): Generando el reporte de cumplimiento y riesgos legales basado en RAG."
        cot_steps.append(step_4_msg)
        print(f"[CoT] {step_4_msg}")
        
        # Instrucción del sistema para el Oficial de Cumplimiento IA
        system_instruction = (
            "Eres un Oficial de Cumplimiento de Datos Personales y Privacidad en México.\n"
            "Tu tarea es analizar el documento anonimizado provisto y evaluar sus riesgos legales en base "
            "EXCLUSIVAMENTE al contexto legal (LFPDPPP, LGPDPPSO y Marco General) que se te proporciona.\n"
            "Reglas estrictas:\n"
            "1. No inventes artículos ni leyes que no estén en el contexto legal proporcionado (Evita Alucinaciones).\n"
            "2. Identifica si el documento recaba datos sensibles y si cumple con los requisitos legales (ej. consentimiento escrito).\n"
            "3. Evalúa si el Aviso de Privacidad está presente o es requerido, y si las transferencias de datos son válidas.\n"
            "4. NUNCA inventes identidades de personas reales. Usa exclusivamente las etiquetas de anonimización provistas (ej. [NOMBRE_1], [DIRECCION_1]).\n"
            "5. Tu respuesta debe estructurarse en: I. Resumen del Documento, II. Análisis de Datos Personales Sensibles Detectados, III. Riesgos de Incumplimiento e Infracciones Específicas (citando artículos), y IV. Recomendaciones de Mitigación."
        )
        
        prompt = (
            f"CONTEXTO LEGAL (RAG):\n{legal_context}\n\n"
            f"DOCUMENTO ANONIMIZADO A ANALIZAR:\n{anonymized_doc}\n\n"
            f"Por favor, realiza el análisis de cumplimiento y riesgos:"
        )
        
        # Enviar prompt anonimizado al LLM (Temperatura baja 0.1 para respuestas deterministas)
        anonymized_response = self.client.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.1
        )
        
        # Monitorear si se requiere escalación humana basándose en el análisis
        self.escalator.check_for_escalation(document_content, anonymized_response)
        
        # Des-anonimizar la respuesta del LLM para el reporte local
        final_report = self.anonymizer.deanonymize(anonymized_response)
        
        logger.info("=== Análisis de Cumplimiento CoT Completado ===")
        
        return {
            "document_name": doc_name,
            "anonymized_document": anonymized_doc,
            "anonymized_report": anonymized_response,
            "final_report": final_report,
            "cot_steps": cot_steps,
            "recovered_laws": [res["source"] for res in search_results]
        }
