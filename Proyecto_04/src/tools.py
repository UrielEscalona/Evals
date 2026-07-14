import time
import re
from langchain_core.tools import tool
from src.database import search_products_by_keyword, find_product_by_id, load_policies

# Singleton tracker for logging tool executions during a run
class ToolExecutionTracker:
    def __init__(self):
        self.history = []
        self.fail_shipping_api = False  # Switch to simulate API failures for evals

    def reset(self):
        self.history = []

    def log_call(self, tool_name, args, cost, success=True, error_msg=None):
        self.history.append({
            "tool": tool_name,
            "args": args,
            "cost": cost,
            "success": success,
            "error": error_msg,
            "timestamp": time.time()
        })

    def get_total_cost(self):
        return sum(x["cost"] for x in self.history)

    def get_calls(self):
        return self.history

tracker = ToolExecutionTracker()

# API Cost structure (Fictional API call cost in USD)
COSTS = {
    "buscar_producto": 0.002,
    "buscar_stock": 0.001,
    "calcular_envio": 0.005,
    "calcular_descuento": 0.002,
    "consultar_politicas": 0.003
}

@tool
def buscar_producto(query: str) -> str:
    """Busca laptops en la tienda que coincidan con la marca, modelo o descripción de búsqueda.
    Retorna una lista de productos en formato JSON con su id, marca, modelo, precio, ram_gb, stock y shipping_days.
    """
    cost = COSTS["buscar_producto"]
    try:
        results = search_products_by_keyword(query)
        tracker.log_call("buscar_producto", {"query": query}, cost, success=True)
        if not results:
            return f"No se encontraron productos que coincidan con la búsqueda '{query}'."
        return str(results)
    except Exception as e:
        tracker.log_call("buscar_producto", {"query": query}, cost, success=False, error_msg=str(e))
        return f"Error al buscar productos: {str(e)}"

@tool
def buscar_stock(product_id: int) -> str:
    """Consulta la disponibilidad de stock de un producto específico utilizando su ID numérico.
    Retorna el estado de disponibilidad y la cantidad exacta de unidades en inventario.
    """
    cost = COSTS["buscar_stock"]
    try:
        # Convert product_id to int in case it comes as a string or float from LLM
        pid = int(product_id)
        product = find_product_by_id(pid)
        if not product:
            msg = f"Producto con ID {pid} no existe."
            tracker.log_call("buscar_stock", {"product_id": pid}, cost, success=False, error_msg=msg)
            return msg
        
        stock = product["stock"]
        tracker.log_call("buscar_stock", {"product_id": pid}, cost, success=True)
        return f"El producto {product['brand']} {product['model']} (ID: {pid}) tiene {stock} unidades disponibles en stock."
    except Exception as e:
        tracker.log_call("buscar_stock", {"product_id": product_id}, cost, success=False, error_msg=str(e))
        return f"Error al buscar stock para el producto ID {product_id}: {str(e)}"

@tool
def calcular_envio(product_id: int, cp: str) -> str:
    """Calcula el tiempo de envío en días hábiles y el costo del servicio de entrega express para un producto (por ID) y un código postal (cp) dados.
    Retorna el costo de envío y el número de días estimado para la entrega.
    """
    cost = COSTS["calcular_envio"]
    pid = int(product_id)
    
    # Check if we should simulate an API failure
    if tracker.fail_shipping_api:
        err_msg = "500 Internal Server Error: Shipping provider API is offline."
        tracker.log_call("calcular_envio", {"product_id": pid, "cp": cp}, cost, success=False, error_msg=err_msg)
        return f"ERROR: No se pudo conectar con el proveedor de envíos. Detalles: {err_msg}"
        
    try:
        product = find_product_by_id(pid)
        if not product:
            msg = f"Producto con ID {pid} no existe."
            tracker.log_call("calcular_envio", {"product_id": pid, "cp": cp}, cost, success=False, error_msg=msg)
            return msg
            
        shipping_days = product["shipping_days"]
        # Dummy cost calculation based on shipping days and postal code format
        shipping_cost = 25.0  # express shipping
        if len(cp) != 5 or not cp.isdigit():
            msg = "Código Postal inválido. Debe tener exactamente 5 dígitos."
            tracker.log_call("calcular_envio", {"product_id": pid, "cp": cp}, cost, success=False, error_msg=msg)
            return msg
            
        tracker.log_call("calcular_envio", {"product_id": pid, "cp": cp}, cost, success=True)
        return f"Envío Express para ID {pid} al Código Postal {cp}: Costo: ${shipping_cost} USD, Tiempo estimado: {shipping_days} días hábiles."
    except Exception as e:
        tracker.log_call("calcular_envio", {"product_id": product_id, "cp": cp}, cost, success=False, error_msg=str(e))
        return f"Error al calcular el envío para el producto ID {product_id}: {str(e)}"

@tool
def calcular_descuento(product_id: int, coupon_code: str) -> str:
    """Aplica un cupón de descuento a un producto (por ID) y calcula el precio final con el descuento aplicado.
    Retorna el precio original, el descuento aplicado y el precio final de compra.
    """
    cost = COSTS["calcular_descuento"]
    try:
        pid = int(product_id)
        product = find_product_by_id(pid)
        if not product:
            msg = f"Producto con ID {pid} no existe."
            tracker.log_call("calcular_descuento", {"product_id": pid, "coupon_code": coupon_code}, cost, success=False, error_msg=msg)
            return msg
            
        original_price = product["price"]
        coupon_clean = coupon_code.strip().upper()
        
        discount_percent = 0
        discount_amount = 0.0
        
        if coupon_clean == "DESCUENTO10":
            discount_percent = 10
            discount_amount = original_price * 0.10
        elif coupon_clean == "BIENVENIDA" and original_price > 500:
            discount_amount = 50.0
        elif coupon_clean == "ENVIOFREE":
            # Shipping discount is handled in shipping cost, not product price
            tracker.log_call("calcular_descuento", {"product_id": pid, "coupon_code": coupon_code}, cost, success=True)
            return f"Cupón ENVIOFREE aplicado. El precio del producto {product['brand']} {product['model']} sigue siendo ${original_price} USD, pero el costo de envío exprés será gratuito ($0 USD)."
        else:
            msg = f"El cupón '{coupon_code}' es inválido o no es aplicable a este producto."
            tracker.log_call("calcular_descuento", {"product_id": pid, "coupon_code": coupon_code}, cost, success=False, error_msg=msg)
            return msg
            
        final_price = original_price - discount_amount
        tracker.log_call("calcular_descuento", {"product_id": pid, "coupon_code": coupon_code}, cost, success=True)
        return (f"Cupón {coupon_clean} aplicado con éxito.\n"
                f"Precio original: ${original_price} USD\n"
                f"Descuento aplicado: -${discount_amount} USD ({discount_percent}%)\n"
                f"Precio final: ${final_price} USD")
    except Exception as e:
        tracker.log_call("calcular_descuento", {"product_id": product_id, "coupon_code": coupon_code}, cost, success=False, error_msg=str(e))
        return f"Error al aplicar descuento para el producto ID {product_id}: {str(e)}"

@tool
def consultar_politicas(pregunta: str) -> str:
    """Consulta la base de conocimientos de políticas de la tienda (devoluciones, garantías, envíos, cupones).
    Retorna los fragmentos de texto de las políticas que son relevantes para responder la pregunta del usuario.
    """
    cost = COSTS["consultar_politicas"]
    try:
        policies = load_policies()
        
        # Simple keyword-based extraction of relevant policy paragraphs (acting as keyword RAG)
        keywords = re.findall(r'\b\w+\b', pregunta.lower())
        relevant_paragraphs = []
        
        # Split policies by section or paragraph
        paragraphs = policies.split("\n\n")
        
        for paragraph in paragraphs:
            score = 0
            for keyword in keywords:
                if len(keyword) > 3 and keyword in paragraph.lower():
                    score += 1
            if score > 0:
                relevant_paragraphs.append((score, paragraph))
                
        # Sort by relevance score
        relevant_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        tracker.log_call("consultar_politicas", {"pregunta": pregunta}, cost, success=True)
        
        if not relevant_paragraphs:
            # Fallback: return general refund/shipping section
            return "No se encontraron secciones específicas para tu pregunta. Aquí están las políticas generales:\n" + paragraphs[0]
            
        # Join top 3 most relevant paragraphs
        top_matches = [p[1] for p in relevant_paragraphs[:3]]
        return "\n\n---\n\n".join(top_matches)
    except Exception as e:
        tracker.log_call("consultar_politicas", {"pregunta": pregunta}, cost, success=False, error_msg=str(e))
        return f"Error al buscar políticas: {str(e)}"

# Export list of tools for LangChain agent
def get_tools_list():
    return [buscar_producto, buscar_stock, calcular_envio, calcular_descuento, consultar_politicas]
