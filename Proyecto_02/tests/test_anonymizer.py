import pytest
from anonymizer import PIIAnonymizer

def test_anonymize_email():
    anonymizer = PIIAnonymizer()
    text = "Mi correo es juan.perez@example.com y el de Maria es maria.gomez@mail.co"
    anon_text = anonymizer.anonymize(text)
    
    assert "[EMAIL_1]" in anon_text
    assert "[EMAIL_2]" in anon_text
    assert "juan.perez@example.com" not in anon_text
    assert "maria.gomez@mail.co" not in anon_text
    
    # Probar des-anonimización
    deanonymized = anonymizer.deanonymize(anon_text)
    assert deanonymized == text

def test_anonymize_curp_rfc():
    anonymizer = PIIAnonymizer()
    text = "Mi CURP es PEGJ850615HMNDRR09 y mi RFC es PEGJ8506159A3."
    anon_text = anonymizer.anonymize(text)
    
    assert "[CURP_1]" in anon_text
    assert "[RFC_1]" in anon_text
    assert "PEGJ850615HMNDRR09" not in anon_text
    assert "PEGJ8506159A3" not in anon_text
    
    # Probar des-anonimización
    deanonymized = anonymizer.deanonymize(anon_text)
    assert "PEGJ850615HMNDRR09" in deanonymized
    assert "PEGJ8506159A3" in deanonymized

def test_anonymize_phone():
    anonymizer = PIIAnonymizer()
    text = "Llámame al 8112345678 o al +52 5554321098."
    anon_text = anonymizer.anonymize(text)
    
    assert "[TELEFONO_1]" in anon_text
    assert "[TELEFONO_2]" in anon_text
    assert "8112345678" not in anon_text
    
    deanonymized = anonymizer.deanonymize(anon_text)
    assert "8112345678" in deanonymized
    assert "5554321098" in deanonymized

def test_anonymize_names():
    anonymizer = PIIAnonymizer()
    text = "Este contrato es firmado por el Lic. Juan Pérez García y la Sra. María González."
    anon_text = anonymizer.anonymize(text)
    
    assert "[NOMBRE_1]" in anon_text
    assert "[NOMBRE_2]" in anon_text
    assert "Juan Pérez García" not in anon_text
    assert "María González" not in anon_text
    
    deanonymized = anonymizer.deanonymize(anon_text)
    assert "Juan Pérez García" in deanonymized
    assert "María González" in deanonymized

def test_anonymize_address():
    anonymizer = PIIAnonymizer()
    text = "Vivo en calle Roble 45, Colonia Del Valle, Monterrey y mi código postal es 64000."
    anon_text = anonymizer.anonymize(text)
    
    assert "[DIRECCION_1]" in anon_text
    assert "calle Roble 45" not in anon_text
    
    deanonymized = anonymizer.deanonymize(anon_text)
    assert "calle Roble 45" in deanonymized

def test_clear_mappings():
    anonymizer = PIIAnonymizer()
    text = "Mi correo es juan@mail.com"
    anon = anonymizer.anonymize(text)
    assert "[EMAIL_1]" in anon
    
    anonymizer.clear()
    assert len(anonymizer.mappings) == 0
    assert anonymizer.counters["EMAIL"] == 1
    
    # Des-anonimizar tras limpiar mapeos debe retornar el texto con placeholders intactos
    deanonymized = anonymizer.deanonymize(anon)
    assert deanonymized == anon
