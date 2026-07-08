"""
Interfaz de Línea de Comandos (CLI) para interactuar con el Chatbot.

Este script permite al usuario conversar en tiempo real con el chatbot.
Por defecto ejecuta el bot con el modo de depuración (debug_mode=True) activo,
lo que permite ver paso a paso cómo funciona el paradigma de Self-Refine
(el borrador inicial, el veredicto del evaluador y el proceso de corrección).
"""

import sys
from chatbot import SelfRefineChatbot


def mostrar_bienvenida():
    print("=" * 70)
    print("  CHATBOT DE SERVICIO AL CLIENTE (ECOSHOP) CON EVALUACIÓN PROPIA (SELF-REFINE)  ")
    print("=" * 70)
    print("Este chatbot utiliza un ciclo de autocrítica para asegurar que sus")
    print("respuestas sean seguras, coherentes y libres de alucinaciones.")
    print("\nModo didáctico: Podrás ver los logs internos de cada etapa [DEBUG].")
    print("Para salir del chat, escribe 'salir', 'exit' o 'quit'.")
    print("=" * 70)


def iniciar_cli():
    # Inicializamos el chatbot en modo debug para poder visualizar el flujo didáctico
    debug = True
    if "--no-debug" in sys.argv:
        debug = False
        
    chatbot = SelfRefineChatbot(debug_mode=debug)
    mostrar_bienvenida()

    while True:
        try:
            # Captura la entrada del usuario
            usuario_input = input("\nCliente: ").strip()
            
            # Verificación de salida
            if usuario_input.lower() in ["salir", "exit", "quit"]:
                print("\n¡Gracias por usar EcoShop! Hasta luego.")
                break
                
            if not usuario_input:
                continue

            # Enviamos el mensaje al chatbot y obtenemos la respuesta final tras el ciclo Self-Refine
            respuesta_final = chatbot.enviar_mensaje(usuario_input)
            
            # Imprimimos la respuesta final visible para el cliente
            print(f"\n[RESPUESTA AL CLIENTE]:\n{respuesta_final}")
            print("-" * 70)

        except KeyboardInterrupt:
            print("\n\nSesión finalizada por el usuario.")
            break
        except Exception as e:
            print(f"\nOcurrió un error inesperado en la CLI: {e}")
            break


if __name__ == "__main__":
    iniciar_cli()
