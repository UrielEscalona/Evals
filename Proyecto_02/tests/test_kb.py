import os
import pytest
import numpy as np
from knowledge_base import EncryptedVectorStore

@pytest.fixture
def temp_db(tmp_path):
    # Generar ruta temporal para la DB
    db_file = tmp_path / "test_store.enc"
    # Clave de 32 bytes para pruebas
    test_key = b"12345678901234567890123456789012"
    
    store = EncryptedVectorStore(db_path=str(db_file), encryption_key=test_key)
    return store

def test_add_and_search(temp_db):
    # Agregar entradas ficticias con vectores conocidos
    # Vector de consulta: [1.0, 0.0]
    # Entrada 1: [1.0, 0.0] -> Similitud 1.0
    # Entrada 2: [0.0, 1.0] -> Similitud 0.0
    # Entrada 3: [-1.0, 0.0] -> Similitud -1.0
    
    temp_db.add_entry("Texto idéntico", "DocA", [1.0, 0.0])
    temp_db.add_entry("Texto ortogonal", "DocB", [0.0, 1.0])
    temp_db.add_entry("Texto opuesto", "DocC", [-1.0, 0.0])
    
    # Búsqueda
    results = temp_db.search([1.0, 0.0], top_k=3)
    
    assert len(results) == 3
    assert results[0]["text"] == "Texto idéntico"
    assert pytest.approx(results[0]["similarity"], 0.0001) == 1.0
    
    assert results[1]["text"] == "Texto ortogonal"
    assert pytest.approx(results[1]["similarity"], 0.0001) == 0.0
    
    assert results[2]["text"] == "Texto opuesto"
    assert pytest.approx(results[2]["similarity"], 0.0001) == -1.0

def test_save_and_load_encrypted(temp_db):
    # Agregar entradas
    temp_db.add_entry("Artículo 9 - Datos Sensibles", "LFPDPPP", [0.1, 0.2, 0.3])
    temp_db.add_entry("Artículo 16 - Principios", "LGPDPPSO", [0.4, 0.5, 0.6])
    
    # Guardar cifrado
    temp_db.save()
    
    # Verificar que el archivo existe
    assert os.path.exists(temp_db.db_path)
    
    # Intentar leer el archivo cifrado de forma binaria. No debe contener texto plano legible.
    with open(temp_db.db_path, "rb") as f:
        content = f.read()
    assert b"Datos Sensibles" not in content
    
    # Crear nueva instancia apuntando al mismo archivo con la misma clave y cargar
    new_store = EncryptedVectorStore(db_path=temp_db.db_path, encryption_key=temp_db.encryption_key)
    new_store.load()
    
    assert len(new_store.entries) == 2
    assert new_store.entries[0]["text"] == "Artículo 9 - Datos Sensibles"
    assert new_store.entries[0]["embedding"] == [0.1, 0.2, 0.3]

def test_load_with_wrong_key(temp_db):
    temp_db.add_entry("Datos Confidenciales", "Doc", [0.1])
    temp_db.save()
    
    # Cargar con clave incorrecta
    wrong_key = b"wrongkeywrongkeywrongkeywrongkey"
    bad_store = EncryptedVectorStore(db_path=temp_db.db_path, encryption_key=wrong_key)
    
    with pytest.raises(Exception):
        bad_store.load()

def test_delete_user_data_arco(temp_db):
    temp_db.add_entry("Expediente de Juan Pérez de glucosa", "Salud", [0.1])
    temp_db.add_entry("Artículo general sobre LFPDPPP", "Ley", [0.2])
    temp_db.save()
    
    assert len(temp_db.entries) == 2
    
    # Eliminar datos de Juan Pérez
    removed = temp_db.delete_user_data("Juan Pérez")
    assert removed == 1
    assert len(temp_db.entries) == 1
    assert temp_db.entries[0]["text"] == "Artículo general sobre LFPDPPP"
