import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products_db.json")
POLICIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "store_policies.txt")

def _load_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Base de datos de productos no encontrada en {DB_PATH}")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_all_products():
    """Retorna todos los productos de la base de datos."""
    return _load_db()

def find_product_by_id(product_id: int):
    """Busca un producto específico por ID."""
    db = _load_db()
    for product in db:
        if product["id"] == product_id:
            return product
    return None

def search_products_by_keyword(keyword: str):
    """Busca productos que contengan la palabra clave en su nombre, marca o descripción."""
    db = _load_db()
    results = []
    keyword_lower = keyword.lower()
    for p in db:
        if (keyword_lower in p["brand"].lower() or 
            keyword_lower in p["model"].lower() or 
            keyword_lower in p["description"].lower()):
            results.append(p)
    return results

def update_product_stock(product_id: int, new_stock: int):
    """Actualiza la cantidad de stock para un producto por ID."""
    db = _load_db()
    for product in db:
        if product["id"] == product_id:
            product["stock"] = new_stock
            _save_db(db)
            return True
    return False

def load_policies():
    """Lee el archivo de políticas de la tienda."""
    if not os.path.exists(POLICIES_PATH):
        return "Políticas no disponibles."
    with open(POLICIES_PATH, "r", encoding="utf-8") as f:
        return f.read()
