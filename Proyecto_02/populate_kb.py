import os
import sys
import logging
from gemini_client import GeminiClient
from knowledge_base import EncryptedVectorStore
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PopulateKB")

def split_laws_into_chunks(filepath: str) -> list[str]:
    """
    Función educativa de procesamiento de texto.
    Divide el archivo de leyes en bloques lógicos basándose en 'ARTÍCULO' o secciones.
    Esto permite que el RAG recupere el artículo completo con sus definiciones.
    """
    logger.info(f"Leyendo y dividiendo archivo: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Error: El archivo {filepath} no existe.")
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Dividir el documento por "ARTÍCULO" para aislar cada precepto legal
    # Usamos expresión regular para detectar saltos de línea seguidos de "ARTÍCULO"
    raw_chunks = re.split(r'\n(?=ARTÍCULO|\[MARCO|\[LEY)', content)
    
    chunks = []
    for chunk in raw_chunks:
        chunk_cleaned = chunk.strip()
        if chunk_cleaned:
            chunks.append(chunk_cleaned)
            
    logger.info(f"Se generaron {len(chunks)} fragmentos legales a partir de {os.path.basename(filepath)}")
    return chunks

import re

def main():
    logger.info("=== Iniciando indexación de Base de Conocimiento RAG (Fines Educativos) ===")
    
    # 1. Validar que la API Key esté configurada
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.error(
            "ERROR: GEMINI_API_KEY no configurada. "
            "Para generar embeddings, configura tu API Key en el archivo .env."
        )
        print("\n[!] Por favor, configura tu GEMINI_API_KEY en el archivo .env antes de ejecutar este script.")
        sys.exit(1)

    # 2. Inicializar el cliente API de Gemini y la Base de Datos Vectorial Cifrada
    client = GeminiClient()
    db = EncryptedVectorStore()
    
    # 3. Definir archivos a indexar
    laws_to_index = [
        {"file": config.RAW_LAWS_DIR / "LFPDPPP.txt", "source": "LFPDPPP (Sector Privado)"},
        {"file": config.RAW_LAWS_DIR / "LGPDPPSO.txt", "source": "LGPDPPSO (Sector Público)"},
        {"file": config.RAW_LAWS_DIR / "Marco_Legal_General.txt", "source": "Marco Legal General (INAI/Constitución)"}
    ]

    total_chunks = 0
    # 4. Procesar cada archivo
    for law in laws_to_index:
        filepath = law["file"]
        source = law["source"]
        
        chunks = split_laws_into_chunks(str(filepath))
        for i, chunk in enumerate(chunks):
            print(f"-> Indexando fragmento {i+1}/{len(chunks)} de: {source}...", end="", flush=True)
            try:
                # Generar embedding del fragmento llamando a la API
                embedding = client.get_embedding(chunk)
                
                # Guardar en memoria de la DB
                db.add_entry(chunk, source, embedding)
                total_chunks += 1
                print(" OK")
            except Exception as e:
                print(" ERROR")
                logger.error(f"Error al indexar fragmento {i+1}: {e}")
                sys.exit(1)

    # 5. Cifrar y guardar la DB en disco
    print("\nCifrando base de datos y escribiendo archivo seguro...")
    db.save()
    print("=== ¡Indexación completada con éxito! ===")
    print(f"Archivo vectorial cifrado guardado en: {db.db_path}")
    print(f"Total de fragmentos legales indexados y protegidos con AES-256: {total_chunks}")

if __name__ == "__main__":
    main()
