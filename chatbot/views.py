from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .services import procesar_mensaje


# =========================
# VISTA PRINCIPAL
# =========================

def chatbot_view(request):

    return render(
        request,
        'chatbot/chatbot.html'
    )


# =========================
# API DEL CHATBOT
# =========================

@csrf_exempt
def consultar_chatbot(request):

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            mensaje = data.get('mensaje', '')

            # =========================
            # VALIDAR USUARIO
            # =========================

            rol = "invitado"

            if request.user.is_authenticated:

                rol = "paciente"

            resultado = procesar_mensaje(
                mensaje=mensaje,
                rol=rol
            )

            return JsonResponse(resultado)

        except Exception as e:

            return JsonResponse({
                'respuesta': f'Error: {str(e)}',
                'intent': 'error',
                'opciones': []
            })

    return JsonResponse({
        'respuesta': 'Método no permitido',
        'intent': 'error',
        'opciones': []
    })