import json
import os
import re
import time
from src.agent import ReActAgent

EVAL_HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "eval_history.json")

# Define our test scenarios
SCENARIOS = [
    {
        "id": 1,
        "name": "Búsqueda y Compra Multi-hop",
        "prompt": "Quiero comprar la laptop de 16GB de RAM más barata con envío menor a dos días (mi CP es 01000).",
        "description": "Evalúa razonamiento multi-hop (buscar, filtrar por RAM, verificar stock de candidatos, cotizar envío, comparar precio y decidir).",
        "expected_product_id": 107,  # MSI Modern 15 ($700, 16GB, 1 day, stock 6)
        "fail_shipping": False,
        "evaluation_rules": {
            "required_tools": ["buscar_producto", "buscar_stock", "calcular_envio"],
            "forbidden_tools": ["consultar_politicas"],
            "must_contain": ["107", "MSI", "Modern 15", "700"]
        }
    },
    {
        "id": 2,
        "name": "Consulta de Políticas (RAG)",
        "prompt": "¿Cuáles son las políticas para reembolsos? Quiero saber qué pasa si me arrepiento de la compra.",
        "description": "Evalúa la correcta selección de la herramienta de políticas (RAG) en lugar de búsqueda de productos.",
        "expected_product_id": None,
        "fail_shipping": False,
        "evaluation_rules": {
            "required_tools": ["consultar_politicas"],
            "forbidden_tools": ["buscar_producto", "buscar_stock", "calcular_envio"],
            "must_contain": ["30", "devolución", "15"]
        }
    },
    {
        "id": 3,
        "name": "Cálculo de Cupón de Descuento",
        "prompt": "Quiero comprar la laptop Dell Inspiron 15 (ID 101). ¿Cuánto me costaría si aplico el cupón DESCUENTO10?",
        "description": "Evalúa el uso correcto del cupón de descuento y operaciones aritméticas del agente.",
        "expected_product_id": 101,
        "fail_shipping": False,
        "evaluation_rules": {
            "required_tools": ["calcular_descuento"],
            "forbidden_tools": ["consultar_politicas"],
            "must_contain": ["101", "Inspiron 15", "495"]
        }
    },
    {
        "id": 4,
        "name": "Resiliencia ante Fallo de API (Fallback)",
        "prompt": "Quiero la laptop Lenovo ThinkPad E14 (ID 102). Revisa si hay stock y cuánto cuesta el envío al CP 01000.",
        "description": "Simula un error 500 en la API de envíos y evalúa si el agente se recupera graciosamente explicando el fallo y dando el stock.",
        "expected_product_id": 102,
        "fail_shipping": True, # Force API failure
        "evaluation_rules": {
            "required_tools": ["buscar_stock", "calcular_envio"],
            "forbidden_tools": ["consultar_politicas"],
            "must_contain": ["Lenovo", "ThinkPad E14", "stock", "error", "envío"]
        }
    },
    {
        "id": 5,
        "name": "Manejo de Error de Lógica / Validación",
        "prompt": "¿Tienen stock de la laptop Apple?",
        "description": "El usuario pregunta por stock de una marca sin dar ID. El agente debe buscar el producto para obtener el ID 105 antes de llamar a buscar_stock.",
        "expected_product_id": 105,
        "fail_shipping": False,
        "evaluation_rules": {
            "required_tools": ["buscar_producto", "buscar_stock"],
            "forbidden_tools": ["consultar_politicas", "calcular_envio"],
            "must_contain": ["Apple", "MacBook Air", "15"]
        }
    }
]

def evaluate_scenario(agent, scenario):
    print(f"\n--- Evaluando Escenario {scenario['id']}: {scenario['name']} ---")
    print(f"Prompt: {scenario['prompt']}")
    
    result = agent.run(
        user_query=scenario["prompt"],
        fail_shipping=scenario["fail_shipping"]
    )
    
    if not result["success"]:
        print(f"Resultado: FALLO CRÍTICO ({result['final_answer']})")
        return {
            "scenario_id": scenario["id"],
            "name": scenario["name"],
            "success": False,
            "final_answer": result["final_answer"],
            "steps": [],
            "metrics": {
                "task_completed": False,
                "tools_correct": False,
                "tool_sequencing_ok": False,
                "cost_usd": 0.0,
                "latency_sec": 0.0,
                "steps_count": 0,
                "token_cost": 0.0,
                "api_cost": 0.0,
                "tokens_in": 0,
                "tokens_out": 0
            },
            "failures": ["Error al conectar con el LLM"]
        }

    # Evaluate criteria
    tool_calls = result["tool_calls_logged"]
    final_answer = result["final_answer"]
    
    # 1. Check required tools
    called_tools = [c["tool"] for c in tool_calls]
    failures = []
    
    for req in scenario["evaluation_rules"]["required_tools"]:
        if req not in called_tools:
            failures.append(f"Herramienta requerida faltante: '{req}'")
            
    # 2. Check forbidden tools
    for forb in scenario["evaluation_rules"]["forbidden_tools"]:
        if forb in called_tools:
            failures.append(f"Herramienta prohibida ejecutada: '{forb}'")
            
    # 3. Check tool sequencing
    tool_sequencing_ok = True
    if "buscar_producto" in called_tools and "buscar_stock" in called_tools:
        idx_search = called_tools.index("buscar_producto")
        idx_stock = called_tools.index("buscar_stock")
        if idx_stock < idx_search:
            tool_sequencing_ok = False
            failures.append("Secuencia incorrecta: Se llamó a 'buscar_stock' antes de 'buscar_producto'")
            
    if "buscar_producto" in called_tools and "calcular_envio" in called_tools:
        idx_search = called_tools.index("buscar_producto")
        idx_envio = called_tools.index("calcular_envio")
        if idx_envio < idx_search:
            tool_sequencing_ok = False
            failures.append("Secuencia incorrecta: Se llamó a 'calcular_envio' antes de 'buscar_producto'")

    # 4. Check Must Contain words in final answer
    answer_contains_ok = True
    for word in scenario["evaluation_rules"]["must_contain"]:
        if word.lower() not in final_answer.lower():
            answer_contains_ok = False
            failures.append(f"La respuesta final no menciona la palabra clave obligatoria: '{word}'")

    # 5. Check if shipping API failure was handled gracefully
    fallback_handled_ok = True
    if scenario["fail_shipping"]:
        # Verify if agent explained that shipping calculation is unavailable but still provided stock
        has_error_mention = any("error" in w or "envío" in w or "problema" in w for w in final_answer.lower().split())
        has_stock_mention = "5" in final_answer # ThinkPad E14 stock is 5
        if not (has_error_mention and has_stock_mention):
            fallback_handled_ok = False
            failures.append("No manejó adecuadamente el fallo de la API de envíos.")

    # Aggregate metrics
    task_completed = (len(failures) == 0)
    tools_correct = not any("Herramienta" in f for f in failures)
    
    print(f"Completitud de Tarea: {'PASA' if task_completed else 'FALLA'}")
    if failures:
        print("Detalles de fallos:")
        for f in failures:
            print(f"  - {f}")
    print(f"Costo: ${result['total_cost']:.5f} USD | Latencia: {result['latency']:.2f} s")
    
    return {
        "scenario_id": scenario["id"],
        "name": scenario["name"],
        "success": True,
        "final_answer": final_answer,
        "steps": result["steps"],
        "metrics": {
            "task_completed": task_completed,
            "tools_correct": tools_correct,
            "tool_sequencing_ok": tool_sequencing_ok,
            "cost_usd": result["total_cost"],
            "latency_sec": result["latency"],
            "steps_count": len(result["steps"]),
            "token_cost": result["token_cost"],
            "api_cost": result["api_cost"],
            "tokens_in": result["tokens"]["input"],
            "tokens_out": result["tokens"]["output"]
        },
        "failures": failures
    }

def run_full_evaluation():
    agent = ReActAgent()
    results = []
    
    print("Iniciando Suite de Evaluación Completa con gemma4:latest...")
    
    for scenario in SCENARIOS:
        res = evaluate_scenario(agent, scenario)
        results.append(res)
        time.sleep(1)  # Brief pause between scenarios
        
    # Summarize Run
    total_scenarios = len(SCENARIOS)
    successful_runs = sum(1 for r in results if r["success"])
    completed_tasks = sum(1 for r in results if r["metrics"]["task_completed"])
    correct_tools = sum(1 for r in results if r["metrics"]["tools_correct"])
    
    total_cost = sum(r["metrics"]["cost_usd"] for r in results)
    total_token_cost = sum(r["metrics"]["token_cost"] for r in results)
    total_api_cost = sum(r["metrics"]["api_cost"] for r in results)
    total_latency = sum(r["metrics"]["latency_sec"] for r in results)
    
    summary = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "totals": {
            "scenarios_count": total_scenarios,
            "successful_runs": successful_runs,
            "completed_tasks": completed_tasks,
            "correct_tools": correct_tools,
            "task_completion_rate": (completed_tasks / total_scenarios) * 100 if total_scenarios else 0.0,
            "tool_correctness_rate": (correct_tools / total_scenarios) * 100 if total_scenarios else 0.0,
            "total_cost_usd": total_cost,
            "total_token_cost_usd": total_token_cost,
            "total_api_cost_usd": total_api_cost,
            "average_latency_sec": total_latency / total_scenarios if total_scenarios else 0.0,
            "total_tokens_in": sum(r["metrics"]["tokens_in"] for r in results),
            "total_tokens_out": sum(r["metrics"]["tokens_out"] for r in results)
        },
        "scenarios": results
    }
    
    # Save to history
    history = []
    if os.path.exists(EVAL_HISTORY_PATH):
        try:
            with open(EVAL_HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except:
            history = []
            
    history.append(summary)
    
    # Keep only the last 20 evaluation runs to conserve space
    if len(history) > 20:
        history = history[-20:]
        
    os.makedirs(os.path.dirname(EVAL_HISTORY_PATH), exist_ok=True)
    with open(EVAL_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    print("\n================ EVALUATION SUMMARY ================")
    print(f"Completitud de Tareas (TCR): {summary['totals']['task_completion_rate']:.1f}% ({completed_tasks}/{total_scenarios})")
    print(f"Uso Correcto de Herramientas: {summary['totals']['tool_correctness_rate']:.1f}% ({correct_tools}/{total_scenarios})")
    print(f"Costo Total de la Corrida: ${total_cost:.5f} USD (Tokens: ${total_token_cost:.5f}, APIs: ${total_api_cost:.5f})")
    print(f"Latencia Promedio: {summary['totals']['average_latency_sec']:.2f} segundos")
    print("====================================================")
    
    return summary

if __name__ == "__main__":
    run_full_evaluation()
