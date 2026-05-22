from .nlp import predecir_intent, limpiar_texto_pro

OPCIONES_DEFAULT = ["Ver historial", "Cambiar contraseña", "Mis consultas", "Agregar contacto"]
INTENTS_PRIVADOS = ["ver_historial", "cambiar_password", "ver_consultas", "agregar_contacto"]

def procesar_mensaje(mensaje, rol="invitado", contexto=None):
    mensaje_limpio = limpiar_texto_pro(mensaje)
    
    # 1. FILTRO DE TEMAS FUERA DE ALCANCE (Evita respuestas como la de China o Clima)
    temas_no_salud = ["clima", "llover", "hora", "china", "chiste", "futbol", "tiempo", "noticias"]
    if any(palabra in mensaje_limpio for palabra in temas_no_salud):
        return {"intent": "desconocido", "opciones": OPCIONES_DEFAULT}

    # 2. ATAJOS RÁPIDOS
    afirmaciones = ["si", "sii", "claro", "por favor", "ok", "vale"]
    negaciones = ["no", "nada", "asi esta bien", "no gracias", "terminar"]

    if mensaje_limpio in afirmaciones:
        return {"intent": "confirmacion", "opciones": OPCIONES_DEFAULT}
    if mensaje_limpio in negaciones:
        return {"intent": "despedida", "opciones": []}

    if not mensaje.strip():
        return {"intent": "vacio", "opciones": []}

    # 3. PREDICCIÓN IA
    intent, confianza = predecir_intent(mensaje)

    # UMBRAL ESTRICTO: Si la IA duda (menos de 0.35), mejor decir que no sabe
    if confianza < 0.35:
        return {"intent": "desconocido", "opciones": OPCIONES_DEFAULT}

    # CONTEXTO
    preguntas_contexto = ["donde", "como", "despues", "luego", "que hago"]
    if (mensaje_limpio in preguntas_contexto or len(mensaje_limpio) < 4) and contexto:
        intent = contexto
        confianza = 1.0

    # SEGURIDAD POR ROL
    if intent in INTENTS_PRIVADOS and rol != "paciente":
        return {"intent": "restriccion", "opciones": ["Iniciar sesión", "Recuperar contraseña"]}

    return {
        "intent": intent,
        "opciones": OPCIONES_DEFAULT if intent in ["saludo", "confirmacion"] else []
    }