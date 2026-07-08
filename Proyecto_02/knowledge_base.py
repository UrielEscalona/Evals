import os
import json
import logging
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import config

logger = logging.getLogger("KnowledgeBase")

class EncryptedVectorStore:
    """
    Base de datos vectorial ligera y CIFRADA para el almacenamiento seguro de la base de conocimiento (RAG).
    
    Implementa "Privacy by Design" a nivel de almacenamiento:
    - Las leyes y sus vectores asociados se guardan cifrados en disco usando AES-256-GCM.
    - Si un atacante accede al archivo 'vector_store.enc', no podrá leer los artículos ni los vectores.
    - Cuenta con capacidad de borrado de datos (Derecho de Cancelación ARCO) para purgar datos del usuario.
    """
    def __init__(self, db_path=None, encryption_key=None):
        self.db_path = db_path or config.KB_PATH
        self.encryption_key = encryption_key or config.ENCRYPTION_KEY
        
        # En memoria representamos la DB como una lista de diccionarios:
        # [{"text": "artículo...", "source": "LFPDPPP", "embedding": [...]}]
        self.entries = []

    def add_entry(self, text: str, source: str, embedding: list[float]):
        """Agrega un fragmento de ley y su vector de embedding a la base de datos en memoria."""
        self.entries.append({
            "text": text,
            "source": source,
            "embedding": embedding
        })

    def save(self):
        """
        Cifra la base de datos completa y la guarda en disco.
        Utiliza AES-GCM para garantizar Confidencialidad e Integridad (cifrado autenticado).
        """
        if not self.entries:
            logger.warning("[RAG DB] Intentando guardar una base de datos vacía.")
            
        try:
            # 1. Serializar los datos en formato JSON
            json_str = json.dumps(self.entries)
            data_bytes = json_str.encode('utf-8')
            
            # 2. Generar un Vector de Inicialización (IV) de 12 bytes aleatorio (estándar para GCM)
            # El IV NUNCA debe repetirse con la misma clave.
            iv = os.urandom(12)
            
            # 3. Inicializar el cifrador AES-GCM con la clave de 32 bytes (AES-256)
            aesgcm = AESGCM(self.encryption_key)
            
            # 4. Cifrar los datos. El método encrypt añade automáticamente el tag de autenticación.
            encrypted_data = aesgcm.encrypt(iv, data_bytes, None)
            
            # 5. Escribir a disco: Guardamos el IV concatenado con los datos cifrados
            # Estructura del archivo: [ 12 bytes IV ] + [ Datos Cifrados + Tag de Autenticación ]
            with open(self.db_path, "wb") as f:
                f.write(iv + encrypted_data)
                
            logger.info(f"[RAG DB] Base de datos cifrada y guardada en {self.db_path}. Registros: {len(self.entries)}")
        except Exception as e:
            logger.error(f"[RAG DB] Error al cifrar y guardar la base de datos: {e}")
            raise e

    def load(self):
        """
        Lee el archivo cifrado de disco, lo descifra usando la clave AES y carga los datos en memoria.
        Si el archivo no existe, inicializa una base de datos vacía.
        """
        if not os.path.exists(self.db_path):
            logger.info(f"[RAG DB] No se encontró base de datos en {self.db_path}. Iniciando vacía.")
            self.entries = []
            return

        try:
            # 1. Leer los bytes crudos del archivo
            with open(self.db_path, "rb") as f:
                file_content = f.read()
                
            if len(file_content) < 12:
                logger.error("[RAG DB] Archivo corrupto o demasiado pequeño.")
                self.entries = []
                return
                
            # 2. Extraer el IV (primeros 12 bytes) y los datos cifrados
            iv = file_content[:12]
            encrypted_data = file_content[12:]
            
            # 3. Inicializar el cifrador AES-GCM
            aesgcm = AESGCM(self.encryption_key)
            
            # 4. Descifrar los datos. Si los datos fueron alterados, se lanzará un error de autenticación.
            decrypted_bytes = aesgcm.decrypt(iv, encrypted_data, None)
            
            # 5. Deserializar el JSON resultante
            json_str = decrypted_bytes.decode('utf-8')
            self.entries = json.loads(json_str)
            logger.info(f"[RAG DB] Base de datos descifrada y cargada con éxito. Registros: {len(self.entries)}")
        except Exception as e:
            logger.error(f"[RAG DB] Error crítico al descifrar la base de datos (Clave incorrecta o datos corruptos): {e}")
            raise e

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[dict]:
        """
        Realiza una búsqueda de similitud de coseno entre el embedding de consulta y la base de datos.
        Utiliza numpy para acelerar los cálculos de álgebra lineal.
        """
        if not self.entries:
            logger.warning("[RAG DB] Intentando buscar en una base de datos vacía.")
            return []

        # Convertir el embedding de consulta en un vector numpy
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        
        if q_norm == 0:
            return []

        results = []
        for entry in self.entries:
            e_vec = np.array(entry["embedding"], dtype=np.float32)
            e_norm = np.linalg.norm(e_vec)
            
            if e_norm == 0:
                similarity = 0.0
            else:
                # Similitud de Coseno = (A . B) / (||A|| * ||B||)
                dot_product = np.dot(q_vec, e_vec)
                similarity = float(dot_product / (q_norm * e_norm))
                
            results.append({
                "text": entry["text"],
                "source": entry["source"],
                "similarity": similarity
            })

        # Ordenar los resultados por similitud en orden descendente
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def delete_user_data(self, user_name: str) -> int:
        """
        Implementa la depuración física de los datos de un usuario en la base vectorial (ARCO Cancelación).
        
        Elimina cualquier entrada cuya descripción o contenido contenga el nombre del usuario,
        evitando almacenar información que deba ser 'olvidada'.
        """
        initial_count = len(self.entries)
        
        # Filtrar las entradas en memoria: removemos las que mencionen al usuario
        # (Esto aplica si hemos guardado consultas previas del usuario en la base vectorial)
        self.entries = [
            entry for entry in self.entries 
            if user_name.lower() not in entry["text"].lower()
        ]
        
        removed = initial_count - len(self.entries)
        
        if removed > 0:
            # Guardamos la DB cifrada actualizada en disco
            self.save()
            logger.info(f"[ARCO] Se eliminaron {removed} registros conteniendo '{user_name}' de la base vectorial.")
        else:
            logger.debug(f"[ARCO] No se encontraron registros con '{user_name}' en la base vectorial.")
            
        return removed
