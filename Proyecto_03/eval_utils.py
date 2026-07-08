import os
import dotenv
from deepeval.models import GeminiModel
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.synthesizer import Synthesizer

# Cargar variables de entorno
dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

_model_instance = None

def get_gemini_model(model_name="gemini-3.1-flash-lite"):
    """Devuelve la instancia singleton del modelo Gemini para DeepEval."""
    global _model_instance
    if _model_instance is None:
        if not api_key:
            raise ValueError("No se encontró la API Key de Gemini en el archivo .env. Configura GEMINI_API_KEY.")
        # Usamos gemini-3.1-flash-lite por su rapidez y alta cuota en modo educativo
        _model_instance = GeminiModel(
            model=model_name,
            api_key=api_key
        )
    return _model_instance

def evaluate_rag(query: str, response: str, contexts: list, threshold: float = 0.5):
    """
    Evalúa una respuesta RAG en base a una consulta y su contexto de recuperación.
    Métricas utilizadas:
    - Faithfulness (Fidelidad / Si hay alucinaciones)
    - Answer Relevancy (Relevancia de la respuesta con la pregunta)
    - Contextual Relevancy (Relevancia del contexto recuperado con la pregunta)
    """
    try:
        model = get_gemini_model()
        test_case = LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=contexts
        )
        
        # Inicializar métricas
        faithfulness = FaithfulnessMetric(threshold=threshold, model=model)
        answer_relevancy = AnswerRelevancyMetric(threshold=threshold, model=model)
        context_relevancy = ContextualRelevancyMetric(threshold=threshold, model=model)
        
        # Ejecutar métricas
        faithfulness.measure(test_case)
        answer_relevancy.measure(test_case)
        context_relevancy.measure(test_case)
        
        return {
            "success": True,
            "metrics": {
                "faithfulness": {
                    "score": faithfulness.score,
                    "reason": faithfulness.reason,
                    "success": faithfulness.is_successful()
                },
                "answer_relevancy": {
                    "score": answer_relevancy.score,
                    "reason": answer_relevancy.reason,
                    "success": answer_relevancy.is_successful()
                },
                "context_relevancy": {
                    "score": context_relevancy.score,
                    "reason": context_relevancy.reason,
                    "success": context_relevancy.is_successful()
                }
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_synthetic_goldens(contexts: list, max_goldens_per_context: int = 1):
    """
    Genera casos de prueba de evaluación (Goldens) a partir de una lista de contextos
    de forma sintética, utilizando el módulo Synthesizer de DeepEval.
    """
    try:
        model = get_gemini_model()
        synthesizer = Synthesizer(model=model)
        
        # El Synthesizer en generate_goldens_from_contexts requiere una lista de listas de strings
        formatted_contexts = [[ctx] for ctx in contexts]
        
        goldens = synthesizer.generate_goldens_from_contexts(
            contexts=formatted_contexts,
            max_goldens_per_context=max_goldens_per_context
        )
        
        results = []
        for g in goldens:
            results.append({
                "input": g.input,
                "expected_output": g.expected_output,
                "context": g.context[0] if g.context else ""
            })
        return {
            "success": True,
            "goldens": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
