import os
import json
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name="arial.ttf", size=16):
    """
    Carga una fuente TrueType estándar de Windows si está disponible,
    de lo contrario retorna la fuente por defecto de Pillow.
    """
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        # Fallback a la fuente por defecto en caso de no encontrarse
        return ImageFont.load_default()

def create_factura_image(path):
    """Genera una imagen que representa una Factura comercial."""
    # Lienzo de factura (tipo carta: 600 x 800)
    img = Image.new("RGB", (600, 800), "white")
    draw = ImageDraw.Draw(img)
    
    # Fuentes de diferentes tamaños
    font_title = get_font("arial.ttf", 32)
    font_bold = get_font("arial.ttf", 20)
    font_normal = get_font("arial.ttf", 16)
    
    # 1. Encabezado corporativo (Banner azul premium)
    draw.rectangle([(0, 0), (600, 100)], fill="#1a365d")
    draw.text((30, 30), "FACTURA COMERCIAL", fill="white", font=font_title)
    
    # 2. Información de la empresa y factura
    draw.text((30, 130), "Emisor: Soluciones Actum S.A.", fill="#333333", font=font_bold)
    draw.text((30, 160), "RFC: ACT990101XYZ", fill="#666666", font=font_normal)
    draw.text((30, 180), "Dirección: Av. de la Tecnología 404, CDMX", fill="#666666", font=font_normal)
    
    draw.text((400, 130), "FACTURA # F-99321", fill="#1a365d", font=font_bold)
    draw.text((400, 160), "Fecha: 2026-05-19", fill="#666666", font=font_normal)
    draw.text((400, 180), "Vence: 2026-06-19", fill="#666666", font=font_normal)
    
    # 3. Información del Cliente
    draw.rectangle([(30, 220), (570, 290)], outline="#cccccc", width=1)
    draw.text((45, 230), "CLIENTE / FACTURADO A:", fill="#1a365d", font=font_bold)
    draw.text((45, 260), "Nombre: Industrias del Norte S.A. de C.V.", fill="#333333", font=font_normal)
    
    # 4. Tabla de Artículos
    # Encabezados de tabla
    draw.rectangle([(30, 320), (570, 355)], fill="#f0f4f8")
    draw.text((45, 330), "Descripción del Concepto", fill="#1a365d", font=font_bold)
    draw.text((380, 330), "Cant.", fill="#1a365d", font=font_bold)
    draw.text((480, 330), "Total (USD)", fill="#1a365d", font=font_bold)
    
    # Líneas de artículos
    items = [
        ("Licencias de Software de IA (Suscripción anual)", "1", "1,200.00"),
        ("Servicios de Consultoría de Integración LLM", "5", "500.00"),
        ("Configuración y Despliegue de Servidor Ollama", "1", "350.00")
    ]
    
    y = 370
    for desc, cant, tot in items:
        draw.text((45, y), desc, fill="#333333", font=font_normal)
        draw.text((395, y), cant, fill="#333333", font=font_normal)
        draw.text((485, y), f"${tot}", fill="#333333", font=font_normal)
        draw.line([(30, y + 25), (570, y + 25)], fill="#eeeeee", width=1)
        y += 35
        
    # 5. Totales
    draw.text((350, y + 20), "Subtotal:", fill="#666666", font=font_normal)
    draw.text((480, y + 20), "$2,050.00", fill="#333333", font=font_normal)
    
    draw.text((350, y + 45), "I.V.A (16%):", fill="#666666", font=font_normal)
    draw.text((480, y + 45), "$328.00", fill="#333333", font=font_normal)
    
    draw.rectangle([(340, y + 75), (570, y + 115)], fill="#1a365d")
    draw.text((350, y + 85), "TOTAL NETO:", fill="white", font=font_bold)
    draw.text((475, y + 85), "$2,378.00 USD", fill="white", font=font_bold)
    
    # Nota de pie de página
    draw.text((30, 740), "¡Gracias por su preferencia comercial!", fill="#999999", font=font_normal)
    
    # Guardar imagen
    img.save(path)
    print(f"Imagen de FACTURA creada en: {path}")

def create_ticket_image(path):
    """Genera una imagen que representa un Ticket de supermercado/tienda."""
    # Lienzo de ticket (angosto y largo: 350 x 700)
    img = Image.new("RGB", (350, 700), "#fdfdfd")
    draw = ImageDraw.Draw(img)
    
    font_bold = get_font("arial.ttf", 18)
    font_normal = get_font("arial.ttf", 14)
    font_small = get_font("arial.ttf", 12)
    
    # Header del ticket
    draw.text((60, 20), "=== SUPERMERCADO ACTUM ===", fill="black", font=font_bold)
    draw.text((70, 45), "Av. Principal 123 - Sucursal Centro", fill="black", font=font_small)
    draw.text((105, 60), "Teléfono: 555-0192-384", fill="black", font=font_small)
    
    # Separador dashed
    draw.text((20, 85), "--------------------------------------------------------", fill="gray", font=font_small)
    
    # Info de caja
    draw.text((25, 105), "Fecha: 2026-05-19 18:43", fill="black", font=font_small)
    draw.text((25, 120), "Caja: 04   Cajero: Carlos M.", fill="black", font=font_small)
    draw.text((25, 135), "Ticket #: 0092348", fill="black", font=font_small)
    
    # Separador
    draw.text((20, 155), "--------------------------------------------------------", fill="gray", font=font_small)
    
    # Artículos listados
    items = [
        ("1  CAFE SOLUBLE 200G", "4.50"),
        ("2  PAN DE CAJA INTEGRAL", "3.20"),
        ("1  LECHE ENTERA 1L", "1.80"),
        ("3  REFRESCO LATA 355ML", "3.60"),
        ("1  MANZANAS BOLSA 1KG", "2.90"),
        ("1  PASTAS DENTALES PACK", "5.10")
    ]
    
    y = 180
    for name, price in items:
        draw.text((25, y), name, fill="black", font=font_normal)
        draw.text((280, y), f"${price}", fill="black", font=font_normal)
        y += 25
        
    # Separador
    draw.text((20, y), "--------------------------------------------------------", fill="gray", font=font_small)
    y += 20
    
    # Totales
    draw.text((150, y), "SUBTOTAL:", fill="black", font=font_normal)
    draw.text((280, y), "$21.10", fill="black", font=font_normal)
    y += 20
    
    draw.text((150, y), "I.V.A. (16%):", fill="black", font=font_normal)
    draw.text((280, y), "$3.38", fill="black", font=font_normal)
    y += 25
    
    # Total destacado
    draw.rectangle([(20, y), (330, y + 40)], outline="black", width=1)
    draw.text((30, y + 10), "TOTAL COMPRA:", fill="black", font=font_bold)
    draw.text((245, y + 10), "$24.48", fill="black", font=font_bold)
    y += 55
    
    # Pago
    draw.text((25, y), "Efectivo Recibido:", fill="black", font=font_small)
    draw.text((280, y), "$50.00", fill="black", font=font_small)
    y += 18
    
    draw.text((25, y), "Cambio Entregado:", fill="black", font=font_small)
    draw.text((280, y), "$25.52", fill="black", font=font_small)
    y += 35
    
    # Código de barras simulado (líneas verticales gruesas/delgadas)
    barcode_x = 40
    barcode_y = y
    for w in [4, 2, 8, 2, 4, 6, 2, 8, 4, 2, 4, 6, 2, 8, 2, 4, 6, 4, 2, 8, 4, 2, 8]:
        draw.rectangle([(barcode_x, barcode_y), (barcode_x + w - 1, barcode_y + 40)], fill="black")
        barcode_x += w + 2
        
    draw.text((110, barcode_y + 45), "*0092348*", fill="black", font=font_small)
    
    draw.text((50, barcode_y + 70), "¡GRACIAS POR COMPRAR CON NOSOTROS!", fill="black", font=font_small)
    
    # Guardar
    img.save(path)
    print(f"Imagen de TICKET creada en: {path}")

def create_logo_image(path):
    """Genera una imagen que representa un Logo moderno y minimalista."""
    # Lienzo de logo cuadrado premium (500 x 500)
    # Fondo con gradiente simulado de azul marino a morado oscuro
    img = Image.new("RGB", (500, 500), "#0f172a") # Slate muy oscuro
    draw = ImageDraw.Draw(img)
    
    font_logo = get_font("arial.ttf", 40)
    font_sub = get_font("arial.ttf", 16)
    
    # 1. Dibujar un polígono premium geométrico brillante (el logo en sí)
    # Círculo externo difuminado de fondo
    draw.ellipse([(150, 100), (350, 300)], outline="#38bdf8", width=3)
    
    # Triángulos entrelazados con gradiente
    draw.polygon([(250, 130), (170, 270), (330, 270)], outline="#fbbf24", fill="#1e293b") # Triángulo dorado
    draw.polygon([(250, 280), (170, 160), (330, 160)], outline="#38bdf8", fill=None) # Triángulo azul invertido
    
    # Punto brillante en el centro
    draw.ellipse([(242, 205), (258, 221)], fill="#fbbf24")
    
    # 2. Tipografía del Logo
    # Texto principal
    draw.text((115, 340), "ACTUM LOGOS", fill="#ffffff", font=font_logo)
    
    # Eslogan inferior
    draw.text((150, 400), "TECHNOLOGY & ARTIFICIAL INTELLIGENCE", fill="#64748b", font=font_sub)
    
    # Línea de detalle
    draw.line([(100, 430), (400, 430)], fill="#fbbf24", width=2)
    
    # Guardar
    img.save(path)
    print(f"Imagen de LOGO creada en: {path}")

def main():
    # Crear carpetas de datos
    os.makedirs("data/images", exist_ok=True)
    
    # Crear imágenes mock
    create_factura_image("data/images/factura.png")
    create_ticket_image("data/images/ticket.png")
    create_logo_image("data/images/logo.png")
    
    # Crear dataset.json
    dataset = {
        "text_tests": [
            {
                "input": "El servicio al cliente fue terrible, tardaron 3 horas en responder y el agente no resolvió mi problema.",
                "expected_category": "Queja"
            },
            {
                "input": "Error: Connection timeout at database pool connection. Failure code 504. Host: db-instance-01.internal",
                "expected_category": "Error de Base de Datos"
            },
            {
                "input": "Me encanta el nuevo diseño de la plataforma. La velocidad de búsqueda es excelente y la UX es increíble. ¡Buen trabajo!",
                "expected_category": "Felicitación"
            },
            {
                "input": "El sistema está arrojando una alerta crítica: Memory leak detected in worker thread #4. Usage reached 98.4%.",
                "expected_category": "Alerta de Infraestructura"
            }
        ],
        "image_tests": [
            {
                "path": "data/images/factura.png",
                "expected_category": "Factura",
                "description_keywords": ["factura", "emisor", "soluciones", "comercial", "total", "neto"]
            },
            {
                "path": "data/images/ticket.png",
                "expected_category": "Ticket",
                "description_keywords": ["ticket", "supermercado", "caja", "cajero", "compra", "total"]
            },
            {
                "path": "data/images/logo.png",
                "expected_category": "Logo",
                "description_keywords": ["logo", "actum", "logos", "polígono", "triángulo", "tecnología"]
            }
        ]
    }
    
    with open("data/dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print("Archivo 'data/dataset.json' creado exitosamente.")

if __name__ == "__main__":
    main()
