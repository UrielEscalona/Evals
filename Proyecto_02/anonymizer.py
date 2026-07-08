import re
import logging

logger = logging.getLogger("PIIAnonymizer")

class PIIAnonymizer:
    """
    Clase educativa para la Detección y Anonimización en Tiempo Real de 
    Datos Personales y Datos Personales Sensibles (PII).
    
    Implementa el principio de "Privacy by Design" al asegurar que ninguna PII
    viaje al LLM externo. Trabaja localmente usando reglas heurísticas y expresiones
    regulares en español.
    """
    def __init__(self):
        self.mappings = {}  # Diccionario para almacenar {placeholder: original_value}
        self.counters = {
            "NOMBRE": 1,
            "CURP": 1,
            "RFC": 1,
            "TELEFONO": 1,
            "EMAIL": 1,
            "DIRECCION": 1
        }
        
        # Lista de nombres comunes en español para apoyar la detección de nombres
        self.COMMON_NAMES = {
            "juan", "maria", "maría", "carlos", "ana", "jose", "josé", "luis", "francisco", 
            "guadalupe", "alejandro", "rosa", "jorge", "roberto", "miguel", "javier", "pedro", 
            "sofia", "sofía", "fernando", "claudia", "daniel", "gabriel", "jesus", "jesús", 
            "manuel", "laura", "sergio", "david", "arturo", "sandra", "leticia", "adriana", 
            "enrique", "gabriela", "patricia", "ricardo", "eduardo", "martha", "hugo", "oscar",
            "óscar", "veronica", "verónica", "silvia", "elizabeth", "angel", "ángel", "victor",
            "víctor", "mario", "felipe", "antonio", "beatriz", "monica", "mónica", "ricardo",
            "carmen", "teresa", "alberto", "leticia", "adrian", "adrián", "alicia", "beatriz"
        }

    def clear(self):
        """Limpia los mapeos. Requerido para el Derecho de Cancelación (Derechos ARCO)."""
        self.mappings.clear()
        for key in self.counters:
            self.counters[key] = 1
        logger.info("[ARCO] Memoria del Anonimizador purgada (Derecho de Cancelación ejecutado).")

    def _get_placeholder(self, category: str, original_value: str) -> str:
        """
        Genera o recupera un marcador único (placeholder) para un valor detectado.
        Esto asegura la consistencia: si el mismo nombre aparece 3 veces, recibe el mismo placeholder.
        """
        # Limpiar espacios adicionales del valor original
        val = original_value.strip()
        
        # Si ya lo tenemos registrado, devolver el placeholder existente
        for ph, orig in self.mappings.items():
            if orig.lower() == val.lower():
                return ph
                
        # Si es nuevo, generar uno con el contador actual
        index = self.counters[category]
        placeholder = f"[{category}_{index}]"
        self.mappings[placeholder] = val
        self.counters[category] += 1
        return placeholder

    def anonymize(self, text: str) -> str:
        """
        Analiza el texto de entrada y reemplaza los datos personales por placeholders.
        Retorna el texto anonimizado.
        """
        if not text:
            return ""

        anonymized_text = text

        # 1. Anonimizar Correos Electrónicos (Email)
        # Expresión regular estándar para correos
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = re.findall(email_pattern, anonymized_text)
        for email in set(emails):
            placeholder = self._get_placeholder("EMAIL", email)
            anonymized_text = anonymized_text.replace(email, placeholder)

        # 2. Anonimizar CURP (Clave Única de Registro de Población - México)
        # Estructura: 4 letras, 6 números, H/M, 5 letras, 1 letra/número, 1 número
        curp_pattern = r'\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b'
        curps = re.findall(curp_pattern, anonymized_text, re.IGNORECASE)
        for curp in set(curps):
            placeholder = self._get_placeholder("CURP", curp.upper())
            # Reemplazo insensible a mayúsculas/minúsculas
            anonymized_text = re.sub(re.escape(curp), placeholder, anonymized_text, flags=re.IGNORECASE)

        # 3. Anonimizar RFC (Registro Federal de Contribuyentes - México)
        # Estructura: 3 o 4 letras/caracteres, 6 números, 3 caracteres de homoclave
        rfc_pattern = r'\b[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}\b'
        rfcs = re.findall(rfc_pattern, anonymized_text, re.IGNORECASE)
        for rfc in set(rfcs):
            placeholder = self._get_placeholder("RFC", rfc.upper())
            anonymized_text = re.sub(re.escape(rfc), placeholder, anonymized_text, flags=re.IGNORECASE)

        # 4. Anonimizar Teléfonos
        # Captura formatos estándar de 10 dígitos mexicanos, ladas con +52, paréntesis, espacios o guiones
        phone_pattern = r'\b(?:\+?52\s?)?(?:\d{10}|\d{3}[\s.-]\d{3}[\s.-]\d{4}|\(\d{3}\)[\s.-]\d{3}[\s.-]\d{4})\b'
        phones = re.findall(phone_pattern, anonymized_text)
        for phone in set(phones):
            # Filtrar números que parezcan años o números pequeños simples para evitar falsos positivos
            if len(re.sub(r'\D', '', phone)) >= 10:
                placeholder = self._get_placeholder("TELEFONO", phone)
                anonymized_text = anonymized_text.replace(phone, placeholder)

        # 5. Anonimizar Direcciones (Addresses)
        # Busca palabras clave de inicio de dirección mexicana (Calle, Avenida, C.P., Colonia, etc.) 
        # y captura hasta el fin de la frase o delimitador.
        address_keywords = [
            r'calle\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'avenida\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'av\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'calzada\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'bulevar\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'blvd\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'plaza\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'c\.p\.\s*\d{5}',
            r'código\s+postal\s*\d{5}',
            r'colonia\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'col\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9\s#.,-]+',
            r'ciudad\s+de\s+méxico',
            r'cdmx',
            r'monterrey',
            r'nuevo\s+león',
            r'n\.l\.'
        ]
        
        # Ejecutamos búsquedas de patrones de direcciones
        for kw in address_keywords:
            matches = re.findall(kw, anonymized_text, re.IGNORECASE)
            for match in set(matches):
                # Evitar anonimizar frases excesivamente cortas o comunes
                if len(match.strip()) > 3:
                    placeholder = self._get_placeholder("DIRECCION", match)
                    anonymized_text = anonymized_text.replace(match, placeholder)

        # 6. Detección y Anonimización de Nombres Propios (Names)
        # Usamos heurísticas de contexto en español:
        # A) Patrones de introducción: "Sr. [Nombre]", "C. [Nombre]", "ciudadano [Nombre]"
        intro_patterns = [
            r'(?:sr\.|sra\.|lic\.|dr\.|dra\.|don|doña|ing\.)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
            r'(?:ciudadano|representado por|titular|suscrito por)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})',
            r'el\s+c\.\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})'
        ]
        
        for pat in intro_patterns:
            matches = re.findall(pat, anonymized_text, re.IGNORECASE)
            for name in set(matches):
                placeholder = self._get_placeholder("NOMBRE", name)
                anonymized_text = anonymized_text.replace(name, placeholder)

        # B) Búsqueda basada en el diccionario de nombres comunes + apellidos capitalizados
        # Detectamos palabras que inicien en mayúscula que coincidan con nuestra lista de nombres comunes,
        # y capturamos también las siguientes palabras capitalizadas (que serían apellidos).
        words = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b', anonymized_text)
        for i, word in enumerate(words):
            if word.lower() in self.COMMON_NAMES:
                # Intentamos reconstruir el nombre completo (ej. María González Pérez)
                # Buscando las siguientes palabras en el texto original
                full_name_candidate = [word]
                
                # Buscamos en el texto original el fragmento que sigue a este nombre
                # Para fines de este parser, miramos si las siguientes palabras en el texto también están capitalizadas
                escaped_word = re.escape(word)
                pattern = escaped_word + r'([ \t]+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}'
                match = re.search(pattern, anonymized_text)
                if match:
                    full_name_candidate_str = match.group(0)
                    placeholder = self._get_placeholder("NOMBRE", full_name_candidate_str)
                    anonymized_text = anonymized_text.replace(full_name_candidate_str, placeholder)
                else:
                    # Anonimizar solo el nombre si no hay apellidos capitalizados contiguos
                    placeholder = self._get_placeholder("NOMBRE", word)
                    anonymized_text = anonymized_text.replace(word, placeholder)

        return anonymized_text

    def deanonymize(self, text: str) -> str:
        """
        Reemplaza los placeholders en el texto con sus valores originales guardados localmente.
        Reconstruye el reporte final para la lectura del usuario local.
        """
        if not text:
            return ""

        deanonymized_text = text
        # Ordenamos los placeholders por longitud descendente para evitar colisiones en los reemplazos
        # (ej. [NOMBRE_10] antes de [NOMBRE_1] si existieran)
        sorted_placeholders = sorted(self.mappings.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            original_value = self.mappings[placeholder]
            deanonymized_text = deanonymized_text.replace(placeholder, original_value)
            
        return deanonymized_text
