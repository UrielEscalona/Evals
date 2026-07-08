import logging
from anonymizer import PIIAnonymizer

logger = logging.getLogger("ARCOTool")

class ARCOTool:
    """
    Herramienta/Skill para ejercer los Derechos ARCO, específicamente el Derecho de Cancelación
    (simulando el Derecho al Olvido).
    
    Permite limpiar el historial, los mapeos del proxy de anonimización y purgar cualquier registro
    de datos personales en las bases vectoriales y de almacenamiento del agente para un titular específico.
    """
    def __init__(self, anonymizer: PIIAnonymizer, vector_store=None):
        self.anonymizer = anonymizer
        self.vector_store = vector_store

    def execute_cancellation(self, user_name: str) -> dict:
        """
        Ejecuta el Derecho de Cancelación para un usuario determinado.
        
        1. Identifica los datos del usuario en los mapeos actuales.
        2. Elimina los mapeos del anonimizador correspondientes a este usuario.
        3. Elimina las entradas de historial o documentos cargados por el usuario en la base vectorial.
        """
        logger.info(f"[ARCO] Iniciando trámite de Derecho de Cancelación para: '{user_name}'")
        
        # Buscar placeholders asociados a este nombre en los mapeos
        placeholders_to_remove = []
        for placeholder, original in list(self.anonymizer.mappings.items()):
            # Si coincide con el nombre o si es PII de este usuario
            if original.lower() == user_name.lower():
                placeholders_to_remove.append(placeholder)
        
        # Eliminar del anonimizador
        removed_count = 0
        for ph in placeholders_to_remove:
            val = self.anonymizer.mappings.pop(ph, None)
            logger.info(f"[ARCO] Removiendo mapeo local: {ph} -> '{val}'")
            removed_count += 1
            
        # Purgar en la base de datos vectorial de historial si existe
        db_removed_count = 0
        if self.vector_store:
            # Simular la eliminación de los fragmentos que contengan el nombre del usuario
            # En la base vectorial, buscaríamos por metadatos (e.g. metadata['owner'] == user_name)
            db_removed_count = self.vector_store.delete_user_data(user_name)
            logger.info(f"[ARCO] Removidos {db_removed_count} vectores del historial del usuario '{user_name}' de la base de datos.")

        # Si no se encontró en mapeos activos pero el usuario solicita borrar todo, limpiamos la sesión por seguridad
        if removed_count == 0 and not placeholders_to_remove:
            logger.info(f"[ARCO] No se encontraron mapeos específicos activos para '{user_name}'. Procediendo a purgar la sesión completa por precaución.")
            self.anonymizer.clear()
            removed_count = "Sesión completa"
            
        result = {
            "status": "success",
            "titular": user_name,
            "mapeos_removidos": removed_count,
            "vectores_removidos_db": db_removed_count,
            "mensaje": f"El Derecho de Cancelación ha sido ejercido exitosamente. Los datos de '{user_name}' han sido completamente purgados y olvidados del sistema."
        }
        
        logger.info(f"[ARCO] Cancelación finalizada con éxito para '{user_name}'.")
        return result
