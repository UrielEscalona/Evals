import re
import json
import time
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.tools import get_tools_list, tracker

# Define LLM Pricing
TOKEN_COST_INPUT = 0.002 / 1000   # $2.00 per 1M input tokens
TOKEN_COST_OUTPUT = 0.006 / 1000  # $6.00 per 1M output tokens

class ReActAgent:
    def __init__(self, model_name="gemma4:latest", base_url="http://localhost:11434"):
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.0,  # Zero temperature for deterministic reasoning
            base_url=base_url
        )
        self.tools = {t.name: t for t in get_tools_list()}
        self.max_steps = 8

    def _get_tools_description(self):
        desc = ""
        for name, tool in self.tools.items():
            desc += f"- {name}: {tool.description}\n"
        return desc

    def _parse_action(self, text):
        """Parsea la acción y los argumentos del formato ReAct.
        Soporta tanto formato JSON como clave=valor.
        Ejemplos: 
          Action: buscar_producto({"query": "laptop"})
          Action: buscar_producto(query="laptop")
        """
        # Buscar "Action: nombre_herramienta(args)"
        match = re.search(r"Action:\s*(\w+)\((.*)\)", text, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            args_str = match.group(2).strip()
            
            # Intentar decodificar como JSON
            try:
                # Reemplazar comillas simples por dobles para JSON válido
                json_str = args_str.replace("'", '"')
                args = json.loads(json_str)
                return tool_name, args
            except json.JSONDecodeError:
                # Si falla, probar parsear formato clave=valor (ej: cp="12345", product_id=101)
                args = {}
                pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\d+))', args_str)
                for key, val_dq, val_sq, val_num in pairs:
                    if val_dq:
                        args[key] = val_dq
                    elif val_sq:
                        args[key] = val_sq
                    elif val_num:
                        args[key] = int(val_num)
                return tool_name, args
        return None, None

    def run(self, user_query: str, chat_history=None, fail_shipping=False):
        # Reset tool call tracker
        tracker.reset()
        tracker.fail_shipping_api = fail_shipping
        
        start_time = time.time()
        
        # Format tools description
        tools_desc = self._get_tools_description()
        
        system_prompt = f"""Eres el Agente Inteligente de E-commerce para nuestra tienda de laptops. Tu objetivo es resolver la consulta del usuario de forma eficiente y correcta.
Tienes acceso a las siguientes herramientas:
{tools_desc}

Para interactuar con las herramientas debes usar el formato ReAct (Reason -> Action -> Observation). En cada paso debes responder con:

Thought: [Razonamiento claro de tu siguiente paso. Qué información necesitas y qué herramienta usarás]
Action: [Nombre de la herramienta]([argumentos en formato JSON o clave=valor])

Ejemplos:
Thought: Necesito buscar laptops con 16GB de RAM.
Action: buscar_producto(query="laptop 16GB")

O:
Thought: Necesito verificar el stock de la laptop con ID 102.
Action: buscar_stock(product_id=102)

O:
Thought: Necesito consultar las políticas de envío.
Action: consultar_politicas(pregunta="envío exprés")

Recibirás la respuesta de la herramienta en el formato:
Observation: [Resultado de la herramienta]

IMPORTANTE:
- Realiza solo UNA acción por mensaje.
- NO inventes IDs de productos, precios ni cupones. Si necesitas datos, usa las herramientas correspondientes.
- La secuencia lógica para consultas complejas de compra es:
  1. buscar_producto (para ver qué laptops hay y obtener sus IDs).
  2. buscar_stock (de las laptops candidatas).
  3. calcular_envio (para validar el tiempo de envío si el usuario pide rapidez).
  4. calcular_descuento (si el usuario provee un cupón).
  5. responder con el producto correcto.
  
Cuando tengas toda la información necesaria y estés listo para dar la respuesta final al usuario, debes escribir:
Final Answer: [Tu respuesta final clara, detallada y en español]
"""

        # Build messages list
        messages = [SystemMessage(content=system_prompt)]
        
        # Add past chat history if any
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
                    
        # Define current turn content
        current_turn_prompt = f"Consulta del usuario: {user_query}\n\nComienza tu proceso de razonamiento."
        messages.append(HumanMessage(content=current_turn_prompt))
        
        steps = []
        total_input_tokens = 0
        total_output_tokens = 0
        
        final_answer = ""
        
        for step in range(self.max_steps):
            # Print current turn context to LLM
            try:
                response = self.llm.invoke(messages)
            except Exception as e:
                # Handle connection error to Ollama
                err_msg = f"No se pudo conectar con Ollama. ¿Está iniciado el servidor y cargado gemma4:latest? Detalles: {str(e)}"
                return {
                    "success": False,
                    "final_answer": err_msg,
                    "steps": steps,
                    "total_cost": 0.0,
                    "api_cost": 0.0,
                    "token_cost": 0.0,
                    "tokens": {"input": 0, "output": 0},
                    "latency": 0.0
                }

            # Extract token counts from response metadata (Ollama returns prompt_eval_count and eval_count)
            meta = response.response_metadata
            input_toks = meta.get("prompt_eval_count", 0)
            output_toks = meta.get("eval_count", 0)
            
            # If Ollama didn't return tokens in metadata, approximate by characters
            if input_toks == 0:
                # Simple approximation: 1 token ~ 4 characters
                total_chars_in = sum(len(m.content) for m in messages)
                input_toks = total_chars_in // 4
            if output_toks == 0:
                output_toks = len(response.content) // 4
                
            total_input_tokens += input_toks
            total_output_tokens += output_toks
            
            response_text = response.content.strip()
            
            # Append LLM's response to message history so it remembers its thoughts
            messages.append(AIMessage(content=response_text))
            
            # Extract Thought
            thought_match = re.search(r"Thought:\s*(.*?)(?:Action:|Final Answer:|$)", response_text, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else "Analizando los datos..."
            
            # Check for Action
            tool_name, tool_args = self._parse_action(response_text)
            
            # Check for Final Answer
            final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
            
            if tool_name and tool_name in self.tools:
                # Execute tool
                tool_obj = self.tools[tool_name]
                step_log = {
                    "step": step + 1,
                    "thought": thought,
                    "action": tool_name,
                    "arguments": tool_args,
                    "raw_response": response_text
                }
                
                try:
                    # Execute tool call
                    observation = tool_obj.invoke(tool_args)
                    step_log["observation"] = observation
                    step_log["status"] = "success"
                except Exception as e:
                    observation = f"Error al ejecutar la herramienta: {str(e)}"
                    step_log["observation"] = observation
                    step_log["status"] = "error"
                
                steps.append(step_log)
                
                # Append observation to message history for next turn
                obs_message = f"Observation: {observation}"
                messages.append(HumanMessage(content=obs_message))
                
            elif final_match:
                final_answer = final_match.group(1).strip()
                steps.append({
                    "step": step + 1,
                    "thought": thought,
                    "action": "Final Answer",
                    "arguments": {},
                    "observation": "",
                    "raw_response": response_text,
                    "status": "completed"
                })
                break
            else:
                # Fallback if the LLM output is unstructured or doesn't follow ReAct
                # We try to prompt it again to follow format, or treat the output as Final Answer
                if "Final Answer:" in response_text:
                    parts = response_text.split("Final Answer:")
                    final_answer = parts[-1].strip()
                    break
                else:
                    # Let's check if it did a final answer without the prefix
                    if step == self.max_steps - 1:
                        final_answer = response_text
                        break
                    else:
                        # Prompt the model to correct its formatting
                        err_msg = "Format Error: Debes usar 'Action: herramienta(args)' o 'Final Answer: respuesta'."
                        messages.append(HumanMessage(content=err_msg))
                        steps.append({
                            "step": step + 1,
                            "thought": "Error de formato en la respuesta. Pidiendo corrección.",
                            "action": "Format Correction Request",
                            "arguments": {},
                            "observation": err_msg,
                            "raw_response": response_text,
                            "status": "warning"
                        })
        
        if not final_answer:
            final_answer = "Lo siento, alcancé el número máximo de pasos de razonamiento sin llegar a una respuesta final."

        # Compute costs
        api_cost = tracker.get_total_cost()
        token_cost = (total_input_tokens * TOKEN_COST_INPUT) + (total_output_tokens * TOKEN_COST_OUTPUT)
        total_cost = api_cost + token_cost
        latency = time.time() - start_time
        
        return {
            "success": True,
            "final_answer": final_answer,
            "steps": steps,
            "total_cost": total_cost,
            "api_cost": api_cost,
            "token_cost": token_cost,
            "tokens": {
                "input": total_input_tokens,
                "output": total_output_tokens
            },
            "latency": latency,
            "tool_calls_logged": tracker.get_calls().copy()
        }
