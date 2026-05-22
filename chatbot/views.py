import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.chatbot_engine import procesar_mensaje
from .services.respuestas import obtener_respuesta_unica

@csrf_exempt
def consultar_chatbot(request):
    if request.method != "POST":
        return JsonResponse({"error": "No permitido"}, status=405)

    try:
        data = json.loads(request.body)
        mensaje = data.get("mensaje", "")
        rol = data.get("rol", "invitado")

        ultimo_intent = request.session.get("ultimo_intent")
        historial = request.session.get("historial_respuestas", [])

        resultado = procesar_mensaje(mensaje, rol=rol, contexto=ultimo_intent)
        intent_actual = resultado["intent"]

        # MANEJO DE RESPUESTAS ESPECIALES
        if intent_actual == "restriccion":
            respuesta_final = "Lo siento, esta información es solo para pacientes. ¡Por favor, inicia sesión!"
        elif intent_actual == "vacio":
            respuesta_final = "Dime algo, estoy aquí para ayudarte con Salud Lince."
        else:
            # Aquí entra la respuesta única (incluyendo 'desconocido')
            respuesta_final = obtener_respuesta_unica(intent_actual, historial)
        
        resultado["respuesta"] = respuesta_final

        # ACTUALIZAR SESIÓN
        request.session["ultimo_intent"] = intent_actual
        historial.append(respuesta_final)
        request.session["historial_respuestas"] = historial[-5:]

        return JsonResponse(resultado)

    except Exception as e:
        return JsonResponse({"respuesta": f"Error: {str(e)}", "intent": "error"}, status=500)