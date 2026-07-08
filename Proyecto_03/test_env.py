import os
import dotenv
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# Cargar variables de entorno desde .env
dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("=== DEEPEVAL & GEMINI VERIFICATION ===")
print(f"GEMINI_API_KEY encontrada: {api_key is not None}")
if api_key:
    # Mostrar los primeros y últimos caracteres por seguridad
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")

print("\n1. Inicializando GeminiModel...")
try:
    # Usamos gemini-3.1-flash-lite como indico el usuario
    gemini_model = GeminiModel(
        model="gemini-3.1-flash-lite",
        api_key=api_key
    )
    print("[OK] GeminiModel inicializado con exito!")

    print("\n2. Creando caso de prueba de evaluación (LLMTestCase)...")
    test_case = LLMTestCase(
        input="Cual es la capital de Francia?",
        actual_output="La capital de Francia es Paris.",
        retrieval_context=["Paris es la capital y la ciudad mas poblada de Francia."]
    )
    print("[OK] Caso de prueba creado.")

    print("\n3. Ejecutando métrica de Relevancia de Respuesta (AnswerRelevancyMetric)...")
    metric = AnswerRelevancyMetric(threshold=0.5, model=gemini_model)
    metric.measure(test_case)
    
    print("\n=== RESULTADOS DE EVALUACIÓN ===")
    print(f"Puntaje (Score): {metric.score} (Pasa: {metric.is_successful()})")
    print(f"Razon (Reason): {metric.reason}")
    print("=================================")
    print("[OK] Verificacion completada con exito!")

except Exception as e:
    print("\n[ERROR] Ocurrio un error durante la verificacion:")
    import traceback
    traceback.print_exc()
