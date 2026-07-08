import logging
import os
from pathlib import Path

# Configurar logger de escalación humana
logger = logging.getLogger("HumanEscalation")

class EscalationLogger:
    """
    Logger educativo para el canal de escalación humana (Human-in-the-Loop).
    
    Tanto en la LFPDPPP como en regulaciones internacionales (ej. GDPR), se garantiza el derecho
    del titular a no ser objeto de decisiones enteramente automatizadas sin supervisión humana
    y a manifestar su Oposición al tratamiento.
    
    Este logger monitorea si hay solicitudes complejas o de Oposición y levanta alertas visuales.
    """
    def __init__(self, log_file="data/human_escalations.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log_escalation(self, reason: str, context_details: str):
        """
        Registra la escalación y activa el canal de alerta humana.
        """
        log_entry = (
            f"\n=======================================================\n"
            f"[ALERTA DE ESCALACIÓN HUMANA REQUERIDA]\n"
            f"Motivo: {reason}\n"
            f"Detalles: {context_details}\n"
            f"Acción: El agente IA ha transferido el control a un oficial de privacidad humano.\n"
            f"=======================================================\n"
        )
        
        logger.warning(log_entry)
        
        # Guardar en archivo para persistencia y auditoría
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        return log_entry

    def check_for_escalation(self, user_input: str, doc_analysis_result: str = "") -> bool:
        """
        Analiza las entradas del usuario y las respuestas de análisis del agente
        para identificar si se requiere escalación humana.
        """
        # 1. Detectar Oposición Explícita del usuario (Derecho de Oposición ARCO)
        opposition_keywords = [
            "me opongo", "no autorizo", "no quiero que traten", "revoco", 
            "no doy consentimiento", "deniego mi consentimiento", "demanda", "legal",
            "queja", "inconformidad", "oposición", "oponerse", "cancelación"
        ]
        
        for kw in opposition_keywords:
            if kw in user_input.lower():
                self.log_escalation(
                    "Oposición del Usuario / Ejercicio de Derecho ARCO de Oposición",
                    f"El usuario ingresó: '{user_input}'"
                )
                return True

        # 2. Detectar Decisión Automatizada Compleja o de Alto Riesgo en el análisis
        # (ej. si el contrato contiene multas leoninas, cláusulas de exclusión severas, o consentimiento de datos biométricos)
        automated_decision_keywords = [
            "biométricos", "genéticos", "alto riesgo", "cláusula leonina", 
            "sanción severa", "multa excesiva", "conflicto legal grave", "salud mental",
            "orientación sexual", "preferencia sexual", "creencia religiosa"
        ]
        
        for kw in automated_decision_keywords:
            if kw in doc_analysis_result.lower() or kw in user_input.lower():
                self.log_escalation(
                    "Decisión Automatizada Compleja / Tratamiento de Datos Sensibles de Alto Riesgo",
                    f"Se detectó el término crítico: '{kw}' en el flujo de análisis."
                )
                return True
                
        return False
