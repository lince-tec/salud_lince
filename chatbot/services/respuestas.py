import random

RESPUESTAS_DATA = {
    "saludo": [
        "¡Hola! ¿Cómo puedo ayudarte hoy?",
        "Hola, soy LincyBot. ¿En qué puedo apoyarte?",
        "¡Bienvenido a Salud Lince! ¿Qué necesitas consultar?",
        "Hola, estoy aquí para guiarte. ¿Qué tienes en mente?"
    ],
    "confirmacion": [
        "¡Entendido! Dime qué más necesitas.",
        "Perfecto, ¿en qué más puedo ayudarte?",
        "Muy bien. ¿Hay algo más en lo que pueda apoyarte?",
        "¡Claro! Continúa, te escucho."
    ],
    "despedida": [
        "Espero haberte ayudado. ¡Cuídate mucho!",
        "Gracias por usar Salud Lince. ¡Hasta pronto!",
        "Si necesitas algo más, aquí estaré. ¡Lindo día!"
    ],
    "desconocido": [
        "Lo siento, aún no sé cómo responder a eso. Solo manejo temas de Salud Lince (consultas, historiales o contraseñas).",
        "No tengo información sobre eso, pero puedo ayudarte con tus datos de salud. ¿Qué prefieres hacer?",
        "Aún no estoy entrenado para responder eso. ¿Te ayudo con algo de tu cuenta o tus consultas?"
    ],
    "recuperar_password": ["En el Login busca '¿Olvidaste tu contraseña?' e ingresa tu correo institucional."],
    "cambiar_password": ["Inicia sesión, ve a 'Mi Perfil' y en la derecha verás la opción de actualizar contraseña."],
    "ver_historial": ["Tu historial médico está en la pestaña 'Historial médico'."],
    "ver_consultas": ["Puedes ver tus consultas en el apartado 'Mis Consultas'."],
    "agregar_contacto": ["Añade contactos de emergencia en la sección 'Mi Perfil'."],
    "iniciar_sesion": ["Ingresa con tu matrícula/número de trabajador y tu contraseña (Si estan ingresando por primera vez, tu contraseña fue enviada a tu correo institucional)."],
    "salir": ["Haz clic en 'Salir' en la parte superior derecha."]
}

def obtener_respuesta_unica(intent, historial_reciente=None):
    opciones = RESPUESTAS_DATA.get(intent, ["Dime qué necesitas."])
    if not isinstance(opciones, list) or len(opciones) <= 1:
        return opciones[0] if isinstance(opciones, list) else opciones
    if not historial_reciente:
        return random.choice(opciones)
    disponibles = [opt for opt in opciones if opt not in historial_reciente]
    if not disponibles: disponibles = opciones
    return random.choice(disponibles)